"""Tests for POET FastAPI routes"""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from opendxa.dana.poet.routes import router

# Create a minimal FastAPI app and include the router
app = FastAPI()
app.include_router(router)

# Create test client using the app
client = TestClient(app, raise_server_exceptions=False)


def test_poet_service_info():
    """Test the service info endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "POET"
    assert data["status"] == "active"
    assert "endpoints" in data


def test_transpile_function_basic():
    """Test basic function transpilation"""
    request_data = {
        "function_code": """
@poet(domain="ml_monitoring")
def predict_temperature(data: dict) -> float:
    return data["temperature"]
""",
        "language": "python",
        "config": {"domain": "ml_monitoring", "optimize_for": None, "retries": 3, "timeout": 30, "enable_monitoring": True},
    }

    response = client.post("/transpile", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "poet_implementation" in data
    assert "metadata" in data
    assert data["metadata"]["domain"] == "ml_monitoring"


def test_transpile_function_invalid_code():
    """Test transpilation with invalid function code"""
    request_data = {
        "function_code": "invalid python code",
        "language": "python",
        "config": {"domain": "ml_monitoring", "optimize_for": None, "retries": 3, "timeout": 30, "enable_monitoring": True},
    }

    response = client.post("/transpile", json=request_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Invalid Python code" in data["detail"]


def test_transpile_function_missing_decorator():
    """Test transpilation with missing @poet decorator"""
    request_data = {
        "function_code": """
def predict_temperature(data: dict) -> float:
    return data["temperature"]
""",
        "language": "python",
        "config": {"domain": "ml_monitoring", "optimize_for": None, "retries": 3, "timeout": 30, "enable_monitoring": True},
    }

    response = client.post("/transpile", json=request_data)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Missing @poet decorator" in data["detail"]


def test_transpile_function_with_context():
    """Test transpilation with additional context"""
    request_data = {
        "function_code": """
@poet(domain="ml_monitoring")
def predict_temperature(data: dict) -> float:
    return data["temperature"]
""",
        "language": "python",
        "context": {"model_type": "regression", "input_features": ["temperature", "humidity"]},
        "config": {"domain": "ml_monitoring", "optimize_for": None, "retries": 3, "timeout": 30, "enable_monitoring": True},
    }

    response = client.post("/transpile", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "poet_implementation" in data
    assert "metadata" in data
    assert data["metadata"]["context"] == request_data["context"]


def test_transpile_function_with_optimization():
    """Test transpilation with optimization target"""
    request_data = {
        "function_code": """
@poet(domain="ml_monitoring")
def predict_temperature(data: dict) -> float:
    return data["temperature"]
""",
        "language": "python",
        "config": {"domain": "ml_monitoring", "optimize_for": "accuracy", "retries": 3, "timeout": 30, "enable_monitoring": True},
    }

    response = client.post("/transpile", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "poet_implementation" in data
    assert "metadata" in data
    assert data["metadata"]["optimize_for"] == "accuracy"
    assert "train_code" in data["poet_implementation"]


def test_submit_feedback():
    """Test feedback submission endpoint"""
    feedback_request = {
        "execution_id": "test-execution-123",
        "function_name": "test_function",
        "feedback_payload": "The result was excellent!",
    }
    response = client.post("/feedback", json=feedback_request)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Feedback processed successfully"}


def test_submit_feedback_invalid_request():
    """Test feedback submission with invalid request"""
    invalid_request = {"execution_id": "test-execution-123"}
    response = client.post("/feedback", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_submit_feedback_with_structured_data():
    """Test feedback submission with structured data"""
    feedback_request = {
        "execution_id": "test-execution-456",
        "function_name": "test_function",
        "feedback_payload": {"rating": 5, "comment": "Excellent performance", "suggestions": ["Consider caching results"]},
    }
    response = client.post("/feedback", json=feedback_request)
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Feedback processed successfully"}


def test_get_function_status(monkeypatch):
    """Test getting function status for an existing function"""

    # Patch storage and feedback system to return test data
    class DummyStorage:
        def list_function_versions(self, function_name):
            return ["v1", "v2"]

        def load_metadata(self, function_name, version):
            return {"function_name": function_name, "version": version, "enhanced": True}

    class DummyFeedback:
        def get_feedback_summary(self, function_name):
            return {"total_feedback": 2, "sentiment_distribution": {"positive": 1, "negative": 1}}

    monkeypatch.setattr("opendxa.dana.poet.routes.get_default_storage", lambda: DummyStorage())
    monkeypatch.setattr("opendxa.dana.poet.routes.get_default_feedback_system", lambda: DummyFeedback())

    response = client.get("/functions/test_function")
    assert response.status_code == 200
    data = response.json()
    assert data["function_name"] == "test_function"
    assert data["latest_version"] == "v2"
    assert data["metadata"]["version"] == "v2"
    assert data["metadata"]["enhanced"] is True
    assert data["feedback_summary"]["total_feedback"] == 2


def test_get_function_status_not_found(monkeypatch):
    """Test getting function status for a non-existent function"""

    class DummyStorage:
        def list_function_versions(self, function_name):
            return []

    monkeypatch.setattr("opendxa.dana.poet.routes.get_default_storage", lambda: DummyStorage())
    response = client.get("/functions/does_not_exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
