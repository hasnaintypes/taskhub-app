import pytest

pytestmark = pytest.mark.django_db


class TestAuthentication:
    """Covers AUTH-01/02/03/05/09, SEC-01/02 and the brief's minimum test table."""

    def test_valid_login_establishes_session(self, api_client, admin_user):
        api_client.get("/api/auth/session/")
        csrf_token = api_client.cookies["csrftoken"].value
        response = api_client.post(
            "/api/auth/login/",
            {"username": "admin", "password": "DemoPass123!"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 200
        assert response.data["role"] == "ADMIN"

    def test_invalid_login_is_rejected(self, api_client, admin_user):
        api_client.get("/api/auth/session/")
        csrf_token = api_client.cookies["csrftoken"].value
        response = api_client.post(
            "/api/auth/login/",
            {"username": "admin", "password": "wrong-password"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 400

    def test_anonymous_access_to_private_api_is_rejected(self, api_client):
        response = api_client.get("/api/auth/me/")
        # 401, not 403: "not logged in" vs. "logged in but forbidden" must
        # stay distinguishable so the frontend knows when to redirect to
        # login (see config/exceptions.py custom_exception_handler).
        assert response.status_code == 401

    def test_logout_invalidates_session(self, login, admin_user):
        client, csrf_token = login("admin")
        response = client.post("/api/auth/logout/", HTTP_X_CSRFTOKEN=csrf_token)
        assert response.status_code == 204

        response = client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_state_changing_request_without_csrf_token_is_rejected(self, login, admin_user):
        client, _csrf_token = login("admin")
        # Deliberately omit the X-CSRFToken header.
        response = client.post("/api/tasks/", {"title": "No CSRF"}, format="json")
        assert response.status_code == 403
        assert "CSRF" in str(response.content)


class TestUserManagementRBAC:
    """Covers RBAC-02."""

    def test_admin_can_list_and_create_users(self, login, admin_user):
        client, csrf_token = login("admin")
        assert client.get("/api/users/").status_code == 200

        response = client.post(
            "/api/users/",
            {
                "username": "new_employee",
                "email": "new_employee@taskhub.local",
                "role": "EMPLOYEE",
                "password": "AnotherStrongPass123!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 201

    def test_manager_can_list_but_not_create_users(self, login, manager_user):
        client, csrf_token = login("manager")
        assert client.get("/api/users/").status_code == 200

        response = client.post(
            "/api/users/",
            {
                "username": "sneaky",
                "email": "sneaky@taskhub.local",
                "role": "ADMIN",
                "password": "AnotherStrongPass123!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 403

    def test_employee_cannot_list_users(self, login, employee_user):
        client, _csrf_token = login("employee1")
        assert client.get("/api/users/").status_code == 403
