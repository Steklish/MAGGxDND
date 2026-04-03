"""
Tests for health check and root endpoints
"""
import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus


class TestHealthEndpoints:
    """Test suite for health check endpoints."""

    def test_health_check(self, client: TestClient):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_serves_ui_or_docs(self, client: TestClient):
        """Test root endpoint serves UI or info."""
        response = client.get("/")
        
        # Should either serve UI (HTML) or return API info
        assert response.status_code == HTTPStatus.OK
        # Either HTML content or JSON
        assert response.headers["content-type"].startswith(
            ("text/html", "application/json")
        )

    def test_docs_available(self, client: TestClient):
        """Test Swagger docs are available."""
        response = client.get("/docs")
        
        assert response.status_code == HTTPStatus.OK
        assert "text/html" in response.headers["content-type"]

    def test_openapi_schema_available(self, client: TestClient):
        """Test OpenAPI schema is available."""
        response = client.get("/openapi.json")
        
        assert response.status_code == HTTPStatus.OK
        data = response.json()
        assert "openapi" in data or "swagger" in data
        assert "paths" in data
        assert "info" in data
