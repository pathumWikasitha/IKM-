"""Agent implementations for the multi-agent RAG flow.

This module defines three LangChain agents (Retrieval, Summarization,
Verification) and thin node functions that LangGraph uses to invoke them.
"""

import json
from typing import List

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from core.llm.factory import create_chat_model
from core.agents.prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    PLANNING_SYSTEM_PROMPT,
)
from core.agents.state import QAState
from core.agents.tools import retrieval_tool


def _extract_last_ai_content(messages: List[object]) -> str:
    """Extract the content of the last AIMessage in a messages list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""

def create_agent(model, tools, system_prompt: str = ""):
    """Create a LangGraph React agent."""
    return create_react_agent(model, tools, prompt=system_prompt)


# Define agents at module level for reuse
retrieval_agent = create_agent(
    model=create_chat_model(),
    tools=[retrieval_tool],
    system_prompt=RETRIEVAL_SYSTEM_PROMPT,
)

summarization_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=SUMMARIZATION_SYSTEM_PROMPT,
)

verification_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=VERIFICATION_SYSTEM_PROMPT,
)


planning_agent = create_agent(
    model=create_chat_model(),
    tools=[],
    system_prompt=PLANNING_SYSTEM_PROMPT,
)


def planning_node(state: QAState) -> QAState:
    """Planning Agent node: decomposes complex questions."""
    print("DEBUG: Entering planning_node")
    question = state["question"]
    
    try:
        if not state.get("enable_planning", True):
            print("DEBUG: Bypassing planning_agent due to toggle")
            return {
                "plan": "",
                "sub_questions": [question],
            }

        print("DEBUG: Invoking planning_agent")
        result = planning_agent.invoke(
            {"messages": [
                HumanMessage(content=question)
            ]}
        )
        print("DEBUG: planning_agent returned")
    except Exception as e:
        print(f"DEBUG: planning_agent failed: {e}")
        raise e

    messages = result.get("messages", [])
    response_text = _extract_last_ai_content(messages)

    plan = ""
    sub_questions = []

    if messages:
        last_message = messages[-1]
        if isinstance(last_message, AIMessage):
            # Check for tool_calls representing the Pydantic structured output
            if getattr(last_message, "tool_calls", None):
                for tc in last_message.tool_calls:
                    if tc["name"] == "PlanningOutput":
                        plan = tc["args"].get("plan", "")
                        sub_questions = tc["args"].get("sub_questions", [])
                        break
            # Fallback if raw content is a dict
            elif isinstance(last_message.content, dict):
                plan = last_message.content.get("plan", "")
                sub_questions = last_message.content.get("sub_questions", [])
            elif hasattr(last_message, "parsed"): 
                plan = getattr(last_message.parsed, "plan", "")
                sub_questions = getattr(last_message.parsed, "sub_questions", [])

    # If the response_format wasn't natively extracted and passed as a string/markdown block containing JSON
    if not plan and not sub_questions and response_text:
        try:
            # Try to parse the response text as JSON (sometimes LLMs wrap it in markdown code blocks)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            parsed_json = json.loads(cleaned_text.strip())
            plan = parsed_json.get("plan", "")
            sub_questions = parsed_json.get("sub_questions", [])
        except json.JSONDecodeError:
            # Fallback for completely unstructured unexpected response
            plan = response_text
            sub_questions = []
    
    # If no sub-questions found, stick to original question
    if not sub_questions:
        sub_questions = [question]

    print(f"DEBUG: Planning done. Sub-questions: {len(sub_questions)}")
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
    """Summarization Agent node: generates draft answer from context.

    This node:
    - Sends question + context to the Summarization Agent.
    - Agent responds with a draft answer grounded only in the context.
    - Stores the draft answer in `state["draft_answer"]`.
    """
    question = state["question"]
    context = state.get("context")

    user_content = f"Question: {question}\n\nContext:\n{context}"

    result = summarization_agent.invoke(
        {"messages": [
            HumanMessage(content=user_content)
        ]}
    )
    messages = result.get("messages", [])
    draft_answer = _extract_last_ai_content(messages)

    return {
        "draft_answer": draft_answer,
    }


def verification_node(state: QAState) -> QAState:
    """Verification Agent node: verifies and corrects the draft answer.

    This node:
    - Sends question + context + draft_answer to the Verification Agent.
    - Agent checks for hallucinations and unsupported claims.
    - Stores the final verified answer in `state["answer"]`.
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

    result = verification_agent.invoke(
        {"messages": [
            HumanMessage(content=user_content)
        ]}
    )
    messages = result.get("messages", [])
    answer = _extract_last_ai_content(messages)

    return {
        "answer": answer,
    }
