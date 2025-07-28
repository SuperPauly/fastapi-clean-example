"""
Integration tests for the FastAPI application.

These tests verify the integration between different components
and ensure the application works correctly as a whole.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestApplicationIntegration:
    """Integration tests for the complete application."""

    def test_application_startup(self):
        """Test that the application starts up correctly."""
        # Test that the app can be imported and instantiated
        assert app is not None
        assert app.title == "FastAPI Clean Architecture Template"
        assert app.version == "2.1.0"

    def test_endpoint_chain(self):
        """Test a chain of endpoint calls."""
        # Test root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        
        # Test health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        # Test API status
        status_response = client.get("/api/v1/status")
        assert status_response.status_code == 200
        
        # Verify consistency across endpoints
        root_data = root_response.json()
        health_data = health_response.json()
        
        assert root_data["version"] == health_data["version"]

    def test_cors_headers(self):
        """Test CORS headers are properly set."""
        response = client.get("/")
        
        # In a real application, you would configure CORS middleware
        # and test for proper CORS headers
        assert response.status_code == 200

    def test_error_handling(self):
        """Test application error handling."""
        # Test 404 handling
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Test method not allowed
        response = client.post("/")
        assert response.status_code == 405

    @pytest.mark.slow
    def test_performance_baseline(self):
        """Test basic performance characteristics."""
        import time
        
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()
        
        assert response.status_code == 200
        # Basic performance check - should respond within 1 second
        assert (end_time - start_time) < 1.0


@pytest.mark.integration
class TestExternalIntegrations:
    """Test external service integrations."""

    def test_database_connection_placeholder(self):
        """Placeholder test for database integration."""
        # In a real application, this would test database connectivity
        # For now, we'll just ensure the test framework works
        assert True

    def test_redis_connection_placeholder(self):
        """Placeholder test for Redis integration."""
        # In a real application, this would test Redis connectivity
        # For now, we'll just ensure the test framework works
        assert True

    def test_external_api_placeholder(self):
        """Placeholder test for external API integration."""
        # In a real application, this would test external API calls
        # For now, we'll just ensure the test framework works
        assert True

