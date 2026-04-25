import pytest
from unittest.mock import patch
from app import create_app

@pytest.fixture(scope="module")
def app():
    """
    Creates the Flask app with TESTING=True and a dummy SQLite URI
    so SQLAlchemy doesn't try to connect to a real Postgres instance.
    """
    with patch("app.db") as mock_db:
        mock_db.init_app.return_value = None
        mock_db.create_all.return_value = None
        test_app = create_app()

    test_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "STATIC_TOKEN": "test-static-token",
        "JWT_SECRET_KEY": "test-secret",
    })
    yield test_app


@pytest.fixture(scope="module")
def client(app):
    """Flask test client shared across all tests."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Valid authorization header for protected endpoints."""
    return {"Authorization": "Bearer test-static-token"}