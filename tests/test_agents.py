"""Tests for the planning node logic and PlanningOutput model."""

import pytest
from pydantic import ValidationError

from app.core.agents.agents import PlanningOutput, planning_node


class TestPlanningOutput:
    """Tests for the PlanningOutput Pydantic model."""

    def test_valid_output(self):
        output = PlanningOutput(plan="Search for X", sub_questions=["Q1", "Q2"])
        assert output.plan == "Search for X"
        assert output.sub_questions == ["Q1", "Q2"]

    def test_empty_sub_questions(self):
        output = PlanningOutput(plan="Simple", sub_questions=[])
        assert output.sub_questions == []

    def test_missing_plan_raises(self):
        with pytest.raises(ValidationError):
            PlanningOutput(sub_questions=["Q1"])

    def test_missing_sub_questions_raises(self):
        with pytest.raises(ValidationError):
            PlanningOutput(plan="Some plan")


class TestPlanningNode:
    """Tests for planning_node logic (bypass path only — no LLM calls)."""

    def test_bypass_when_planning_disabled(self):
        """When enable_planning is False, should return original question as-is."""
        state = {
            "question": "What is RAG?",
            "enable_planning": False,
            "context": None,
            "plan": None,
            "sub_questions": None,
            "draft_answer": None,
            "answer": None,
        }
        result = planning_node(state)
        assert result["plan"] == ""
        assert result["sub_questions"] == ["What is RAG?"]

    def test_bypass_preserves_question(self):
        """The original question should be the only sub-question when bypassed."""
        state = {
            "question": "Complex multi-part question here",
            "enable_planning": False,
            "context": None,
            "plan": None,
            "sub_questions": None,
            "draft_answer": None,
            "answer": None,
        }
        result = planning_node(state)
        assert len(result["sub_questions"]) == 1
        assert result["sub_questions"][0] == "Complex multi-part question here"
