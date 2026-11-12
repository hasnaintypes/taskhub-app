import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from accounts.models import Role, User

DEMO_PASSWORD = "DemoPass123!"


@pytest.fixture(autouse=True)
def clear_cache():
    """Redis is real external state, not rolled back with the test DB
    transaction — without this, a dashboard-cache entry from a previous
    test (or a previous `pytest` run, since fixture-created user IDs are
    deterministic per run) can leak in and produce a false cache hit."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def make_user(db):
    def _make(username: str, role: str) -> User:
        user = User.objects.create_user(username=username, email=f"{username}@taskhub.local", role=role)
        user.set_password(DEMO_PASSWORD)
        user.save()
        return user

    return _make


@pytest.fixture
def admin_user(make_user):
    return make_user("admin", Role.ADMIN)


@pytest.fixture
def manager_user(make_user):
    return make_user("manager", Role.MANAGER)


@pytest.fixture
def employee_user(make_user):
    return make_user("employee1", Role.EMPLOYEE)


@pytest.fixture
def other_employee_user(make_user):
    return make_user("employee2", Role.EMPLOYEE)


@pytest.fixture
def api_client():
    return APIClient(enforce_csrf_checks=True)


@pytest.fixture
def login(api_client):
    """Logs in via the real login endpoint and returns (client, csrf_token)
    so tests exercise the actual CSRF + session flow, not a shortcut."""

    def _login(username: str):
        api_client.get("/api/auth/session/")
        csrf_token = api_client.cookies["csrftoken"].value
        response = api_client.post(
            "/api/auth/login/",
            {"username": username, "password": DEMO_PASSWORD},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 200, response.data
        csrf_token = api_client.cookies["csrftoken"].value
        return api_client, csrf_token

    return _login
