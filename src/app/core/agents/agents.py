"""Agent implementations for the multi-agent RAG flow.

This module defines three LangChain agents (Retrieval, Summarization,
Verification) and thin node functions that LangGraph uses to invoke them.
"""

from typing import List

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage

from ..llm.factory import create_chat_model
from .prompts import (
    RETRIEVAL_SYSTEM_PROMPT,
    SUMMARIZATION_SYSTEM_PROMPT,
    VERIFICATION_SYSTEM_PROMPT,
    PLANNING_SYSTEM_PROMPT,
)
from .state import QAState
from .tools import retrieval_tool


def _extract_last_ai_content(messages: List[object]) -> str:
    """Extract the content of the last AIMessage in a messages list."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            return str(msg.content)
    return ""

def create_agent(model, tools, system_prompt: str = ""):
    """Create a LangGraph React agent. 
    
    Note: system_prompt is ignored here as this version of create_react_agent 
    does not support state_modifier. System prompts should be passed in the 
    messages list during invocation.
    """
    return create_react_agent(model, tools)


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
        print("DEBUG: Invoking planning_agent")
        result = planning_agent.invoke(
            {"messages": [
                SystemMessage(content=PLANNING_SYSTEM_PROMPT),
                HumanMessage(content=question)
            ]}
        )
        print("DEBUG: planning_agent returned")
    except Exception as e:
        print(f"DEBUG: planning_agent failed: {e}")
        raise e

    messages = result.get("messages", [])
    response_text = _extract_last_ai_content(messages)

    # Simple parsing logic
    plan = response_text
    sub_questions = []
    
    if "Sub-questions:" in response_text:
        parts = response_text.split("Sub-questions:")
        plan = parts[0].replace("Plan:", "").strip()
        sub_qs_block = parts[1].strip()
        for line in sub_qs_block.split("\n"):
            line = line.strip()
            if line.startswith("- "):
                sub_questions.append(line[2:])
    
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
                SystemMessage(content=RETRIEVAL_SYSTEM_PROMPT),
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
            SystemMessage(content=SUMMARIZATION_SYSTEM_PROMPT),
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
            SystemMessage(content=VERIFICATION_SYSTEM_PROMPT),
            HumanMessage(content=user_content)
        ]}
    )
    messages = result.get("messages", [])
    answer = _extract_last_ai_content(messages)

    return {
        "answer": answer,
    }
