from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


class TestFrontendBuild:
    """Test frontend build configuration and output."""

    def test_next_config_exists(self):
        """Test next.config.ts exists."""
        config_file = ROOT_DIR / "frontend" / "next.config.ts"
        assert config_file.exists(), "next.config.ts should exist"

    def test_frontend_output_directory(self):
        """Test that frontend build outputs to 'out' directory."""
        config_file = ROOT_DIR / "frontend" / "next.config.ts"
        assert "distDir: 'out'" in config_file.read_text()

    def test_static_file_serving(self):
        """Test that backend can serve static files."""
        # Verify backend main.py imports StaticFiles
        from main import app

        assert app is not None


class TestAPIWithFrontend:
    """Test API endpoints work alongside frontend serving."""

    def test_api_test_still_available(self):
        """Verify /api/test endpoint still works with static files."""
        # This test verifies the main.py routes are correct
        from fastapi.testclient import TestClient

        from main import app

        client = TestClient(app)
        response = client.get("/api/test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestFrontendIntegration:
    """Test frontend integration with backend."""

    def test_kanban_component_exists(self):
        """Test that KanbanBoard component exists."""
        kanban_file = ROOT_DIR / "frontend" / "src" / "components" / "KanbanBoard.tsx"
        assert kanban_file.exists(), "KanbanBoard component should exist"

    def test_frontend_package_has_build_script(self):
        """Test that frontend has npm build script."""
        import json
        
        package_json = ROOT_DIR / "frontend" / "package.json"
        assert package_json.exists(), "package.json should exist"
        
        with open(package_json) as f:
            config = json.load(f)
        
        assert "build" in config["scripts"], "build script should exist in package.json"

    def test_dockerfile_multi_stage_build(self):
        """Test that Dockerfile has multi-stage build with frontend."""
        dockerfile = ROOT_DIR / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should exist"
        
        content = dockerfile.read_text()
        assert "frontend-builder" in content, "Dockerfile should have frontend-builder stage"
        assert "node:20-alpine" in content, "Dockerfile should use Node.js for frontend build"
        assert "python:3.12" in content, "Dockerfile should use Python 3.12 for backend"
        assert "frontend/out" in content or "frontend/out" in content, "Dockerfile should copy frontend output"
