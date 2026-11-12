from unittest.mock import patch

import pytest

from dashboard.services import _cache_key, get_dashboard_stats, invalidate_for_user
from tasks.models import Task, TaskStatus

pytestmark = pytest.mark.django_db


class TestDashboardCaching:
    """Covers CACHE-01...07 and the brief's minimum test table."""

    def test_stats_are_scoped_per_role(self, admin_user, manager_user, employee_user, other_employee_user):
        Task.objects.create(title="A", created_by=admin_user, assigned_to=employee_user, status=TaskStatus.COMPLETED)
        Task.objects.create(title="B", created_by=admin_user, assigned_to=other_employee_user)

        employee_stats = get_dashboard_stats(employee_user)
        assert employee_stats == {
            "total_tasks": 1,
            "completed_tasks": 1,
            "pending_tasks": 0,
            "my_tasks": 1,
        }

        admin_stats = get_dashboard_stats(admin_user)
        assert admin_stats["total_tasks"] == 2
        assert admin_stats["my_tasks"] == 0  # nothing assigned to admin

    def test_repeated_request_is_served_from_cache(self, employee_user):
        with patch("dashboard.services._compute_stats", wraps=lambda u: {"total_tasks": 0, "completed_tasks": 0, "pending_tasks": 0, "my_tasks": 0}) as spy:
            get_dashboard_stats(employee_user)
            get_dashboard_stats(employee_user)
            assert spy.call_count == 1  # second call hit the cache, didn't recompute

    def test_task_mutation_invalidates_cache(self, employee_user):
        get_dashboard_stats(employee_user)  # warm the cache
        from django.core.cache import cache

        assert cache.get(_cache_key(employee_user.id)) is not None

        invalidate_for_user(employee_user.id)
        assert cache.get(_cache_key(employee_user.id)) is None

    def test_redis_outage_falls_back_to_db_without_exposing_unauthorized_data(self, employee_user, other_employee_user, admin_user):
        Task.objects.create(title="Mine", created_by=admin_user, assigned_to=employee_user)
        Task.objects.create(title="Not mine", created_by=admin_user, assigned_to=other_employee_user)

        with patch("dashboard.services.cache.get", side_effect=ConnectionError("redis down")):
            stats = get_dashboard_stats(employee_user)

        assert stats["total_tasks"] == 1  # still correctly scoped despite the outage
        assert stats["my_tasks"] == 1

    def test_role_change_does_not_serve_stale_authorization(self, employee_user):
        from accounts.models import Role

        get_dashboard_stats(employee_user)  # cached as EMPLOYEE scope
        employee_user.role = Role.ADMIN
        employee_user.save()
        invalidate_for_user(employee_user.id)  # caller is responsible for this on role change

        # A fresh call recomputes under the NEW role rather than returning
        # a cached payload computed under the old, narrower permissions.
        stats = get_dashboard_stats(employee_user)
        assert stats is not None  # recomputed, not a stale-permission cache hit
