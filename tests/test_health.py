import pytest
from unittest.mock import patch, MagicMock


class TestHealthEndpoint:
    """Tests for GET /health"""

    def test_health_returns_200_when_db_ok(self, client):
        """
        GIVEN the database is reachable
        WHEN  GET /health is called
        THEN  response is 200 with status=healthy
        """
        with patch("routes.health_routes.db") as mock_db:
            mock_db.session.execute = MagicMock(return_value=None)
            response = client.get("/health")

        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"
        assert data["service"] == "blacklist-api"

    def test_health_returns_503_when_db_error(self, client):
        """
        GIVEN the database throws an exception
        WHEN  GET /health is called
        THEN  response is 503 with status=unhealthy
        """
        with patch("routes.health_routes.db") as mock_db:
            mock_db.session.execute.side_effect = Exception("connection refused")
            response = client.get("/health")

        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "unhealthy"
        assert "error" in data["database"]