"""
Unit tests for the main FastAPI application.

These tests verify the basic functionality of the main application
endpoints and ensure proper response formats.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestMainApplication:
    """Test cases for main application endpoints."""

    def test_root_endpoint(self):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "FastAPI Clean Architecture Template"
        assert data["version"] == "2.1.0"
        assert data["status"] == "running"
        assert data["architecture"] == "hexagonal"

    def test_health_check_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "fastapi-clean-example"
        assert data["version"] == "2.1.0"

    def test_api_status_endpoint(self):
        """Test the API status endpoint."""
        response = client.get("/api/v1/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["api_version"] == "v1"
        assert data["status"] == "operational"
        assert isinstance(data["features"], list)
        assert "hexagonal_architecture" in data["features"]
        assert "clean_code_principles" in data["features"]

    def test_nonexistent_endpoint(self):
        """Test that nonexistent endpoints return 404."""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


@pytest.mark.asyncio
class TestAsyncEndpoints:
    """Test cases for async endpoint functionality."""

    async def test_root_endpoint_async(self):
        """Test root endpoint with async client."""
        # This test demonstrates async testing patterns
        # In a real application, you would use httpx.AsyncClient
        response = client.get("/")
        assert response.status_code == 200

    async def test_health_check_async(self):
        """Test health check endpoint with async patterns."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

