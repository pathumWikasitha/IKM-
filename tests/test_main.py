"""Tests for FastAPI endpoints."""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app, raise_server_exceptions=False)


class TestQAEndpoint:
    """Tests for the /qa endpoint."""

    def test_empty_question_returns_400(self):
        response = client.post("/qa", json={"question": "   "})
        assert response.status_code == 400
        assert "non-empty" in response.json()["detail"]

    @patch("app.main.answer_question")
    def test_valid_question_returns_200(self, mock_answer):
        mock_answer.return_value = {
            "answer": "Test answer",
            "plan": "Test plan",
            "context": "Test context",
        }
        response = client.post("/qa", json={"question": "What is RAG?"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Test answer"
        assert data["plan"] == "Test plan"
        assert data["context"] == "Test context"

    @patch("app.main.answer_question")
    def test_planning_disabled(self, mock_answer):
        mock_answer.return_value = {
            "answer": "Answer",
            "context": "Context",
        }
        response = client.post(
            "/qa", json={"question": "Test", "enable_planning": False}
        )
        assert response.status_code == 200
        mock_answer.assert_called_once_with("Test", False)

    def test_missing_question_returns_422(self):
        response = client.post("/qa", json={})
        assert response.status_code == 422


class TestIndexPDFEndpoint:
    """Tests for the /index-pdf endpoint."""

    def test_non_pdf_returns_400(self):
        response = client.post(
            "/index-pdf",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_hidden_filename_returns_400(self):
        response = client.post(
            "/index-pdf",
            files={"file": (".hidden.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 400
        assert "Invalid filename" in response.json()["detail"]

    @patch("app.main.index_pdf_file")
    def test_path_traversal_sanitized(self, mock_index):
        """A filename with path traversal should be sanitized to just the basename."""
        mock_index.return_value = 5
        response = client.post(
            "/index-pdf",
            files={"file": ("../../etc/passwd.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        # The filename in the response should be sanitized
        assert data["filename"] == "passwd.pdf"

    @patch("app.main.index_pdf_file")
    def test_valid_pdf_upload(self, mock_index):
        mock_index.return_value = 10
        response = client.post(
            "/index-pdf",
            files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["chunks_indexed"] == 10
        assert data["message"] == "PDF indexed successfully."


class TestRootEndpoint:
    """Tests for the root redirect."""

    def test_root_redirects_to_static(self):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307)
        assert "/static/index.html" in response.headers.get("location", "")
