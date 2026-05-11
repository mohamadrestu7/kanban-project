import pytest
from fastapi.testclient import TestClient
import importlib
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

app = importlib.import_module("main").app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Test FastAPI endpoints."""

    def test_api_test_endpoint(self, client):
        """Test /api/test endpoint returns correct JSON."""
        response = client.get("/api/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "message" in data
        assert "version" in data

    def test_root_endpoint_returns_html(self, client):
        """Test / endpoint returns HTML content."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Project Management MVP" in response.text

    def test_api_test_response_structure(self, client):
        """Test /api/test response has correct structure."""
        response = client.get("/api/test")
        data = response.json()
        assert isinstance(data, dict)
        assert set(data.keys()) >= {"status", "message", "version"}

    def test_root_contains_status_information(self, client):
        """Test / endpoint contains expected status sections."""
        response = client.get("/")
        assert "API Server Active" in response.text
        assert "Port:" in response.text
        assert "Framework:" in response.text

    def test_root_contains_next_steps(self, client):
        """Test / endpoint contains next steps section."""
        response = client.get("/")
        assert "Next Steps" in response.text
        assert "/api/test" in response.text


class TestEnvironmentVariables:
    """Test environment variable loading."""

    def test_app_can_load_env(self):
        """Test that app loads without errors when env is available."""
        # Just verify the app instance exists
        assert app is not None
        assert app.title == "PM Backend"
        assert app.version == "0.1.0"


class TestAppMetadata:
    """Test application metadata."""

    def test_app_title(self):
        """Test app title is set."""
        assert app.title == "PM Backend"

    def test_app_version(self):
        """Test app version is set."""
        assert app.version == "0.1.0"

    def test_app_has_routes(self):
        """Test app has registered routes."""
        routes = [route.path for route in app.routes]
        assert "/api/test" in routes
        assert any(route.path == "/" or route.path == "" for route in app.routes)
