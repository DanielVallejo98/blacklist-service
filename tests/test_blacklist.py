import pytest
from unittest.mock import patch, MagicMock


VALID_PAYLOAD = {
    "email": "spammer@evil.com",
    "app_uuid": "550e8400-e29b-41d4-a716-446655440000",
    "blocked_reason": "spam",
}


class TestPostBlacklist:
    """Tests for POST /blacklists"""

    def test_add_email_success_returns_201(self, client, auth_headers):
        """
        GIVEN a valid email not yet blacklisted
        WHEN  POST /blacklists with correct token
        THEN  response is 201 with the created entry id
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model, \
             patch("routes.blacklist_routes.db") as mock_db:

            mock_model.query.filter_by.return_value.first.return_value = None
            mock_instance = MagicMock()
            mock_instance.id = 42
            mock_instance.email = VALID_PAYLOAD["email"]
            mock_model.return_value = mock_instance
            mock_db.session.add.return_value = None
            mock_db.session.commit.return_value = None

            response = client.post("/blacklists", json=VALID_PAYLOAD, headers=auth_headers)

        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert VALID_PAYLOAD["email"] in data["msg"]

    def test_add_email_without_token_returns_401(self, client):
        """
        GIVEN a request with no Authorization header
        WHEN  POST /blacklists
        THEN  response is 401
        """
        response = client.post("/blacklists", json=VALID_PAYLOAD)
        assert response.status_code == 401

    def test_add_email_with_invalid_token_returns_401(self, client):
        """
        GIVEN an invalid Bearer token
        WHEN  POST /blacklists
        THEN  response is 401
        """
        response = client.post(
            "/blacklists",
            json=VALID_PAYLOAD,
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert response.status_code == 401

    def test_add_duplicate_email_returns_409(self, client, auth_headers):
        """
        GIVEN an email already present in the blacklist
        WHEN  POST /blacklists
        THEN  response is 409 Conflict
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            mock_model.query.filter_by.return_value.first.return_value = MagicMock()
            response = client.post("/blacklists", json=VALID_PAYLOAD, headers=auth_headers)

        assert response.status_code == 409

    def test_add_email_with_non_json_body_returns_400(self, client, auth_headers):
        """
        GIVEN a request with a non-JSON body
        WHEN  POST /blacklists
        THEN  response is 400 Bad Request
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True):
            response = client.post(
                "/blacklists",
                data="not json at all",
                content_type="text/plain",
                headers=auth_headers,
            )
        assert response.status_code == 400

    def test_add_email_missing_required_field_returns_400(self, client, auth_headers):
        """
        GIVEN a payload missing the required app_uuid field
        WHEN  POST /blacklists
        THEN  response is 400 with validation errors
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            mock_model.query.filter_by.return_value.first.return_value = None
            response = client.post(
                "/blacklists",
                json={"email": "test@test.com"},
                headers=auth_headers,
            )
        assert response.status_code == 400


class TestGetBlacklist:
    """Tests for GET /blacklists/<email>"""

    def test_get_blacklisted_email_returns_true(self, client, auth_headers):
        """
        GIVEN an email that IS in the blacklist
        WHEN  GET /blacklists/<email>
        THEN  response is 200 with is_blacklisted=True
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            mock_entry = MagicMock()
            mock_entry.email = "spammer@evil.com"
            mock_entry.blocked_reason = "spam"
            mock_entry.app_uuid = "550e8400-e29b-41d4-a716-446655440000"
            mock_entry.created_at.isoformat.return_value = "2024-01-01T00:00:00"
            mock_model.query.filter_by.return_value.first.return_value = mock_entry

            response = client.get("/blacklists/spammer@evil.com", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["is_blacklisted"] is True
        assert data["email"] == "spammer@evil.com"

    def test_get_clean_email_returns_false(self, client, auth_headers):
        """
        GIVEN an email that is NOT in the blacklist
        WHEN  GET /blacklists/<email>
        THEN  response is 200 with is_blacklisted=False
        """
        with patch("routes.blacklist_routes.verify_token", return_value=True), \
             patch("routes.blacklist_routes.BlacklistEntry") as mock_model:

            mock_model.query.filter_by.return_value.first.return_value = None
            response = client.get("/blacklists/clean@safe.com", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert data["is_blacklisted"] is False
        assert data["blocked_reason"] is None

    def test_get_email_without_token_returns_401(self, client):
        """
        GIVEN no Authorization header
        WHEN  GET /blacklists/<email>
        THEN  response is 401
        """
        response = client.get("/blacklists/anyone@test.com")
        assert response.status_code == 401