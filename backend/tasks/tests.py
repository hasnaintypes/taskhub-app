from unittest.mock import patch

import pytest
from django.db import transaction

from tasks.models import Task, TaskAssignmentEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def task_assigned_to_employee(employee_user, admin_user):
    return Task.objects.create(title="Assigned task", created_by=admin_user, assigned_to=employee_user)


class TestTaskRBAC:
    """Covers RBAC-03...07/10 and the brief's minimum test table."""

    def test_employee_sees_only_own_tasks(self, login, employee_user, other_employee_user, admin_user):
        Task.objects.create(title="Mine", created_by=admin_user, assigned_to=employee_user)
        Task.objects.create(title="Not mine", created_by=admin_user, assigned_to=other_employee_user)

        client, _ = login("employee1")
        response = client.get("/api/tasks/")
        titles = [t["title"] for t in response.data["results"]]
        assert titles == ["Mine"]

    def test_employee_cannot_create_task(self, login, employee_user):
        client, csrf_token = login("employee1")
        response = client.post(
            "/api/tasks/", {"title": "Nope"}, format="json", HTTP_X_CSRFTOKEN=csrf_token
        )
        assert response.status_code == 403

    def test_employee_deleting_a_task_is_rejected(self, login, task_assigned_to_employee):
        client, csrf_token = login("employee1")
        response = client.delete(
            f"/api/tasks/{task_assigned_to_employee.id}/", HTTP_X_CSRFTOKEN=csrf_token
        )
        assert response.status_code == 403

    def test_employee_reading_another_users_task_is_rejected(
        self, login, employee_user, other_employee_user, admin_user
    ):
        other_task = Task.objects.create(
            title="Someone else's", created_by=admin_user, assigned_to=other_employee_user
        )
        client, _ = login("employee1")
        response = client.get(f"/api/tasks/{other_task.id}/")
        assert response.status_code == 403

    def test_manager_can_view_all_tasks_but_not_delete(
        self, login, manager_user, task_assigned_to_employee
    ):
        client, csrf_token = login("manager")
        assert client.get("/api/tasks/").status_code == 200
        response = client.delete(
            f"/api/tasks/{task_assigned_to_employee.id}/", HTTP_X_CSRFTOKEN=csrf_token
        )
        assert response.status_code == 403

    def test_admin_cannot_reassign_via_generic_patch(
        self, login, admin_user, task_assigned_to_employee, employee_user, other_employee_user
    ):
        """`assigned_to` is read-only on general PATCH — reassignment must
        go through /assign/ so a TaskAssignmentEvent + notification are
        always created [CELERY-01]."""
        client, csrf_token = login("admin")
        response = client.patch(
            f"/api/tasks/{task_assigned_to_employee.id}/",
            {"assigned_to": other_employee_user.id},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 200
        task_assigned_to_employee.refresh_from_db()
        assert task_assigned_to_employee.assigned_to_id == employee_user.id  # unchanged
        from tasks.models import TaskAssignmentEvent

        assert not TaskAssignmentEvent.objects.filter(task=task_assigned_to_employee).exists()

    def test_admin_general_edit_invalidates_dashboard_cache(
        self, login, admin_user, task_assigned_to_employee, employee_user, django_capture_on_commit_callbacks
    ):
        from dashboard.services import _cache_key, get_dashboard_stats

        get_dashboard_stats(employee_user)  # warm the cache
        from django.core.cache import cache

        assert cache.get(_cache_key(employee_user.id)) is not None

        client, csrf_token = login("admin")
        with django_capture_on_commit_callbacks(execute=True):
            response = client.patch(
                f"/api/tasks/{task_assigned_to_employee.id}/",
                {"status": "completed"},
                format="json",
                HTTP_X_CSRFTOKEN=csrf_token,
            )
        assert response.status_code == 200
        assert cache.get(_cache_key(employee_user.id)) is None  # invalidated by the edit

    def test_task_mutation_invalidates_every_admin_and_managers_cache(
        self, login, admin_user, manager_user, task_assigned_to_employee, django_capture_on_commit_callbacks
    ):
        """Regression test: a mutation by one Admin must also invalidate a
        *different, uninvolved* Manager's cached "all tasks" aggregate —
        each Admin/Manager has their own per-user cache key (CACHE-05), so
        all of them need invalidating together, not just the acting user
        and the directly-affected assignee/creator [CACHE-04]."""
        from dashboard.services import _cache_key, get_dashboard_stats

        get_dashboard_stats(manager_user)  # warm the bystander Manager's cache
        from django.core.cache import cache

        assert cache.get(_cache_key(manager_user.id)) is not None

        client, csrf_token = login("admin")
        with django_capture_on_commit_callbacks(execute=True):
            response = client.post(
                "/api/tasks/", {"title": "New unassigned task"}, format="json", HTTP_X_CSRFTOKEN=csrf_token
            )
        assert response.status_code == 201

        # The bystander Manager never touched this task, but their cached
        # "all tasks" total is now stale and must have been invalidated.
        assert cache.get(_cache_key(manager_user.id)) is None

    def test_admin_can_delete_task(self, login, admin_user, task_assigned_to_employee):
        client, csrf_token = login("admin")
        response = client.delete(
            f"/api/tasks/{task_assigned_to_employee.id}/", HTTP_X_CSRFTOKEN=csrf_token
        )
        assert response.status_code == 204
        assert not Task.objects.filter(id=task_assigned_to_employee.id).exists()

    def test_employee_can_only_update_status_not_other_fields(
        self, login, task_assigned_to_employee, employee_user
    ):
        client, csrf_token = login("employee1")
        response = client.patch(
            f"/api/tasks/{task_assigned_to_employee.id}/",
            {"status": "completed", "title": "Hijacked title"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        assert response.status_code == 200
        task_assigned_to_employee.refresh_from_db()
        assert task_assigned_to_employee.status == "completed"
        assert task_assigned_to_employee.title == "Assigned task"  # unchanged


class TestAssignmentAndNotifications:
    """Covers CELERY-01...09."""

    def test_assign_persists_before_enqueue_and_only_after_commit(
        self,
        login,
        admin_user,
        employee_user,
        task_assigned_to_employee,
        other_employee_user,
        django_capture_on_commit_callbacks,
    ):
        client, csrf_token = login("admin")
        with patch("tasks.services.send_assignment_email") as mocked_task:
            with django_capture_on_commit_callbacks(execute=True):
                response = client.post(
                    f"/api/tasks/{task_assigned_to_employee.id}/assign/",
                    {"assigned_to": other_employee_user.id},
                    format="json",
                    HTTP_X_CSRFTOKEN=csrf_token,
                )
            assert response.status_code == 202
            task_assigned_to_employee.refresh_from_db()
            assert task_assigned_to_employee.assigned_to_id == other_employee_user.id
            assert mocked_task.delay.called

    def test_rolled_back_assignment_never_enqueues(
        self, admin_user, employee_user, other_employee_user, django_capture_on_commit_callbacks
    ):
        from tasks.services import assign_task

        task = Task.objects.create(title="Rollback me", created_by=admin_user, assigned_to=employee_user)

        with patch("tasks.services.send_assignment_email") as mocked_task:
            with django_capture_on_commit_callbacks(execute=True):
                try:
                    with transaction.atomic():
                        assign_task(task=task, assigned_to=other_employee_user, assigned_by=admin_user)
                        raise RuntimeError("force rollback")
                except RuntimeError:
                    pass

        mocked_task.delay.assert_not_called()
        task.refresh_from_db()
        assert task.assigned_to_id == employee_user.id  # unchanged by the rollback

    def test_repeated_delivery_of_same_event_does_not_duplicate_notify(
        self, admin_user, employee_user
    ):
        from notifications.tasks import send_assignment_email

        task = Task.objects.create(title="Idempotency check", created_by=admin_user, assigned_to=employee_user)
        event = TaskAssignmentEvent.objects.create(
            task=task, assigned_to=employee_user, assigned_by=admin_user
        )

        send_assignment_email.run(str(event.id))
        event.refresh_from_db()
        assert event.notified is True

        with patch("notifications.tasks.send_mail") as mocked_send_mail:
            send_assignment_email.run(str(event.id))  # simulate a retry of the SAME event
            mocked_send_mail.assert_not_called()

    def test_reassignment_creates_a_new_event_eligible_to_notify(
        self, admin_user, employee_user, other_employee_user, django_capture_on_commit_callbacks
    ):
        from tasks.services import assign_task

        task = Task.objects.create(title="Reassign me", created_by=admin_user, assigned_to=employee_user)

        with patch("tasks.services.send_assignment_email") as mocked_task:
            with django_capture_on_commit_callbacks(execute=True):
                e1 = assign_task(task=task, assigned_to=employee_user, assigned_by=admin_user)
                e2 = assign_task(task=task, assigned_to=other_employee_user, assigned_by=admin_user)

            assert e1.id != e2.id
            assert mocked_task.delay.call_count == 2
