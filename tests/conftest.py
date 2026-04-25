import os

# ─── Must happen BEFORE app is imported ───────────────────────────
os.environ["DATABASE_URL"]  = "sqlite:///:memory:"
os.environ["STATIC_TOKEN"]  = "test-static-token"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
# ──────────────────────────────────────────────────────────────────

import pytest
from app import create_app


@pytest.fixture(scope="module")
def app():
    test_app = create_app()
    test_app.config["TESTING"] = True
    yield test_app


@pytest.fixture(scope="module")
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-static-token"}