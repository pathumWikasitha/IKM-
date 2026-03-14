"""Tests for Pydantic request/response models."""

import pytest
from pydantic import ValidationError

from app.models import QuestionRequest, QAResponse


class TestQuestionRequest:
    """Tests for the QuestionRequest model."""

    def test_valid_question(self):
        req = QuestionRequest(question="What is RAG?")
        assert req.question == "What is RAG?"
        assert req.enable_planning is True  # default

    def test_with_planning_disabled(self):
        req = QuestionRequest(question="Test", enable_planning=False)
        assert req.enable_planning is False

    def test_missing_question_raises(self):
        with pytest.raises(ValidationError):
            QuestionRequest()

    def test_empty_string_passes_pydantic(self):
        """Pydantic allows empty strings — the endpoint does extra validation."""
        req = QuestionRequest(question="")
        assert req.question == ""


class TestQAResponse:
    """Tests for the QAResponse model."""

    def test_valid_response(self):
        resp = QAResponse(answer="42", context="some context")
        assert resp.answer == "42"
        assert resp.plan is None
        assert resp.context == "some context"

    def test_with_plan(self):
        resp = QAResponse(answer="yes", plan="step 1", context="ctx")
        assert resp.plan == "step 1"

    def test_missing_answer_raises(self):
        with pytest.raises(ValidationError):
            QAResponse(context="ctx")

    def test_missing_context_raises(self):
        with pytest.raises(ValidationError):
            QAResponse(answer="yes")
