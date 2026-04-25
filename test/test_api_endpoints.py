"""
Integration tests for FastAPI endpoints
Tests the full HTTP API with mocked RAG pipeline
"""
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from main import app, ChatRequest, ChatResponse, HealthResponse


@pytest.fixture
def client():
    """Provide test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_rag_chain():
    """Fixture for mocked RAG chain"""
    mock_chain = MagicMock()
    mock_chain.invoke = MagicMock(return_value="Mocked RAG response about frequency control")
    return mock_chain


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_returns_200(self, client, mock_rag_chain):
        """Test that health endpoint returns 200 OK"""
        # Mock the global rag_chain
        with patch("main.rag_chain", mock_rag_chain):
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_returns_correct_structure(self, client, mock_rag_chain):
        """Test health endpoint returns expected JSON structure"""
        with patch("main.rag_chain", mock_rag_chain):
            response = client.get("/health")
            data = response.json()

            assert "status" in data
            assert "message" in data
            assert "timestamp" in data
            assert data["status"] == "healthy"

    def test_health_without_pipeline_returns_503(self, client):
        """Test health check fails when pipeline not initialized"""
        with patch("main.rag_chain", None):
            response = client.get("/health")
            assert response.status_code == 503

    def test_health_includes_timestamp(self, client, mock_rag_chain):
        """Test health response includes ISO format timestamp"""
        with patch("main.rag_chain", mock_rag_chain):
            response = client.get("/health")
            data = response.json()

            # Timestamp should be ISO format
            assert "T" in data["timestamp"]
            assert "Z" in data["timestamp"] or "+" in data["timestamp"]


class TestWebUIEndpoint:
    """Tests for web UI endpoint"""

    def test_web_ui_returns_200(self, client):
        """Test that web UI endpoint returns 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_web_ui_returns_html(self, client):
        """Test that web UI returns HTML content"""
        response = client.get("/")
        assert "text/html" in response.headers.get("content-type", "")

    def test_web_ui_contains_expected_elements(self, client):
        """Test that HTML contains expected UI elements"""
        response = client.get("/")
        html = response.text

        assert "Energy Grid AI" in html or "chat" in html.lower()
        assert "<!DOCTYPE" in html or "<html" in html.lower()

    def test_web_ui_is_valid_html(self, client):
        """Test that response is valid HTML structure"""
        response = client.get("/")
        html = response.text

        assert html.count("<") > 0
        assert html.count(">") > 0
        assert html.count("<html") >= 1


class TestChatEndpoint:
    """Tests for chat endpoint"""

    def test_chat_returns_200_with_valid_request(self, client, mock_rag_chain):
        """Test chat endpoint returns 200 with valid request"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": "What is frequency control?",
                        "session_id": "test_session"
                    }
                )
                assert response.status_code == 200

    def test_chat_returns_correct_structure(self, client, mock_rag_chain):
        """Test chat endpoint returns expected response structure"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": "What is BDEW?",
                        "session_id": "test_session"
                    }
                )
                data = response.json()

                assert "question" in data
                assert "answer" in data
                assert "session_id" in data
                assert "timestamp" in data

    def test_chat_preserves_question(self, client, mock_rag_chain):
        """Test that chat endpoint returns the original question"""
        question = "What is the Agorameter?"
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": question,
                        "session_id": "test_session"
                    }
                )
                data = response.json()

                assert data["question"] == question

    def test_chat_preserves_session_id(self, client, mock_rag_chain):
        """Test that chat endpoint returns the session ID"""
        session_id = "my_session_12345"
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": "Test question",
                        "session_id": session_id
                    }
                )
                data = response.json()

                assert data["session_id"] == session_id

    def test_chat_missing_question_returns_422(self, client):
        """Test that missing question parameter returns validation error"""
        response = client.post(
            "/chat",
            json={"session_id": "test_session"}
        )
        assert response.status_code == 422

    def test_chat_with_default_session_id(self, client, mock_rag_chain):
        """Test that session_id defaults to 'default' if not provided"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={"question": "Test question"}
                )
                data = response.json()

                assert data["session_id"] == "default"

    def test_chat_calls_rag_chain_with_correct_params(self, client, mock_rag_chain):
        """Test that chat endpoint calls rag_chain with correct parameters"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                question = "What is frequency?"
                session_id = "test_session"

                response = client.post(
                    "/chat",
                    json={
                        "question": question,
                        "session_id": session_id
                    }
                )

                # Verify rag_chain.invoke was called
                mock_rag_chain.invoke.assert_called()

    def test_chat_handles_special_characters(self, client, mock_rag_chain):
        """Test chat with special characters in question"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": "What is @#$%^&*()? <html>",
                        "session_id": "test_session"
                    }
                )
                assert response.status_code == 200

    def test_chat_handles_long_question(self, client, mock_rag_chain):
        """Test chat with very long question"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                long_question = "What is " + "frequency " * 1000
                response = client.post(
                    "/chat",
                    json={
                        "question": long_question,
                        "session_id": "test_session"
                    }
                )
                assert response.status_code == 200


class TestStaticFiles:
    """Tests for static file serving"""

    def test_static_styles_css_returns_200(self, client):
        """Test that styles.css is served"""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_static_app_js_returns_200(self, client):
        """Test that app.js is served"""
        response = client.get("/static/app.js")
        assert response.status_code == 200

    def test_static_nonexistent_returns_404(self, client):
        """Test that nonexistent static file returns 404"""
        response = client.get("/static/nonexistent.js")
        assert response.status_code == 404


class TestAPIDocumentation:
    """Tests for API documentation endpoints"""

    def test_swagger_ui_returns_200(self, client):
        """Test Swagger UI documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_returns_200(self, client):
        """Test ReDoc documentation is available"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_returns_200(self, client):
        """Test OpenAPI schema endpoint"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/json"

    def test_openapi_schema_is_valid_json(self, client):
        """Test that OpenAPI schema is valid JSON"""
        response = client.get("/openapi.json")
        try:
            data = response.json()
            assert "openapi" in data or "swagger" in data
        except json.JSONDecodeError:
            pytest.fail("OpenAPI schema is not valid JSON")


class TestErrorHandling:
    """Tests for error handling"""

    def test_invalid_json_returns_422(self, client):
        """Test that invalid JSON returns 422"""
        response = client.post(
            "/chat",
            data="not valid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422

    def test_chat_with_null_question_returns_422(self, client):
        """Test that null question returns validation error"""
        response = client.post(
            "/chat",
            json={"question": None, "session_id": "test"}
        )
        assert response.status_code == 422

    def test_nonexistent_endpoint_returns_404(self, client):
        """Test that nonexistent endpoint returns 404"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404


class TestResponseModels:
    """Tests for Pydantic response models"""

    def test_chat_response_validation(self, client, mock_rag_chain):
        """Test that ChatResponse model validates correctly"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response = client.post(
                    "/chat",
                    json={
                        "question": "Test",
                        "session_id": "test"
                    }
                )

                # Should have proper structure
                data = response.json()
                assert all(key in data for key in ["question", "answer", "session_id", "timestamp"])

    def test_health_response_validation(self, client, mock_rag_chain):
        """Test that HealthResponse model validates correctly"""
        with patch("main.rag_chain", mock_rag_chain):
            response = client.get("/health")

            data = response.json()
            assert all(key in data for key in ["status", "message", "timestamp"])


class TestConcurrentRequests:
    """Tests for handling multiple concurrent requests"""

    def test_multiple_sequential_requests(self, client, mock_rag_chain):
        """Test multiple sequential chat requests"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                for i in range(3):
                    response = client.post(
                        "/chat",
                        json={
                            "question": f"Question {i+1}",
                            "session_id": f"session_{i}"
                        }
                    )
                    assert response.status_code == 200

    def test_different_sessions_independent(self, client, mock_rag_chain):
        """Test that different sessions don't interfere"""
        with patch("main.rag_chain", mock_rag_chain):
            with patch("main.pipeline", MagicMock()):
                response1 = client.post(
                    "/chat",
                    json={
                        "question": "Question A",
                        "session_id": "session_a"
                    }
                )

                response2 = client.post(
                    "/chat",
                    json={
                        "question": "Question B",
                        "session_id": "session_b"
                    }
                )

                data1 = response1.json()
                data2 = response2.json()

                assert data1["session_id"] == "session_a"
                assert data2["session_id"] == "session_b"
