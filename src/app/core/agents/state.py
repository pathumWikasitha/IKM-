"""LangGraph state schema for the multi-agent QA flow."""

from typing import TypedDict, Optional, List


class QAState(TypedDict):
    """State schema for the linear multi-agent QA flow.

    The state flows through three agents:
    1. Retrieval Agent: populates `context` from `question`
    2. Summarization Agent: generates `draft_answer` from `question` + `context`
    3. Verification Agent: produces final `answer` from `question` + `context` + `draft_answer`
    """

    question: str
    enable_planning: bool
    context: Optional[str]
    plan: Optional[str]
    sub_questions: Optional[List[str]]
    draft_answer: Optional[str]
    answer: Optional[str]
