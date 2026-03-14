"""Agent implementations for the multi-agent RAG flow.

This module defines the Retrieval agent (which uses tools) and direct LLM
invocations for Planning, Summarization, and Verification nodes.
"""

import logging
from typing import List

from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from app.core.llm.factory import create_chat_model
from app.core.agents.prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    PLANNING_SYSTEM_PROMPT,
)
from app.core.agents.state import QAState
from app.core.agents.tools import retrieval_tool

logger = logging.getLogger(__name__)


class PlanningOutput(BaseModel):
    """Structured output schema for the Planning Agent."""
    plan: str = Field(description="A brief description of the search plan.")
    sub_questions: List[str] = Field(description="List of sub-questions to search for.")


def _extract_last_ai_content(messages: List[object]) -> str:
    """Extract the content of the last AIMessage in a messages list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""


# --- Agents & LLMs at module level for reuse ---

# Retrieval agent needs tools, so it stays as a full agent
retrieval_agent = create_agent(
    model=create_chat_model(),
    tools=[retrieval_tool],
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
)

# Summarization & verification have no tools — use direct LLM invocation
summarization_llm = create_chat_model()
verification_llm = create_chat_model()

# Planning uses structured output to guarantee Pydantic schema
planning_llm = create_chat_model().with_structured_output(PlanningOutput)


def planning_node(state: QAState) -> QAState:
    """Planning Agent node: decomposes complex questions."""
    logger.info("Entering planning_node")
    question = state["question"]

    if not state.get("enable_planning", True):
        logger.info("Bypassing planning due to toggle")
        return {
            "plan": "",
            "sub_questions": [question],
        }

    logger.info("Invoking planning_llm (structured output)")
    result: PlanningOutput = planning_llm.invoke([
        SystemMessage(content=PLANNING_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ])

    plan = result.plan
    sub_questions = result.sub_questions

    # If no sub-questions found, stick to original question
    if not sub_questions:
        sub_questions = [question]

    logger.info("Planning done. Sub-questions: %d", len(sub_questions))
    return {
        "plan": plan,
        "sub_questions": sub_questions,
    }


def retrieval_node(state: QAState) -> QAState:
    """Retrieval Agent node: gathers context from vector store.

    This node:
    - Iterates through `sub_questions` (or uses the main question).
    - Calls the Retrieval Agent for each query.
    - Consolidates all retrieved chunks into `state["context"]`.
    """
    queries = state.get("sub_questions") or [state["question"]]
    all_context_parts = []

    for query in queries:
        result = retrieval_agent.invoke(
            {"messages": [
                HumanMessage(content=query)
            ]}
        )
        messages = result.get("messages", [])

        # Extract context from this specific call
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage):
                all_context_parts.append(str(msg.content))
                break

    # Deduplicate or just join. Simple join for now.
    consolidated_context = "\n\n".join(all_context_parts)

    return {
        "context": consolidated_context,
    }


def summarization_node(state: QAState) -> QAState:
    """Summarization node: generates draft answer from context.

    Invokes the LLM directly (no tools needed) with a system prompt
    and the question + context as user input.
    """
    question = state["question"]
    context = state.get("context")

    user_content = f"Question: {question}\n\nContext:\n{context}"

    response = summarization_llm.invoke([
        SystemMessage(content=SUMMARIZATION_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
    draft_answer = response.content

    return {
        "draft_answer": draft_answer,
    }


def verification_node(state: QAState) -> QAState:
    """Verification node: verifies and corrects the draft answer.

    Invokes the LLM directly (no tools needed) with a system prompt
    and the question + context + draft answer as user input.
    """
    question = state["question"]
    context = state.get("context", "")
    draft_answer = state.get("draft_answer", "")

    user_content = f"""Question: {question}

Context:
{context}

Draft Answer:
{draft_answer}

Please verify and correct the draft answer, removing any unsupported claims."""

    response = verification_llm.invoke([
        SystemMessage(content=VERIFICATION_SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ])
    answer = response.content

    return {
        "answer": answer,
    }
