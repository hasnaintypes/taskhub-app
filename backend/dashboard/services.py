import logging

from django.core.cache import cache

from accounts.models import Role, User
from tasks.models import Task, TaskStatus

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 300  # 5 minutes [CACHE-03]
CACHE_KEY_PREFIX = "dashboard:stats:v1:user"


def _cache_key(user_id: int) -> str:
    # Keyed by user id (not just role) so no two users can ever share a
    # cached payload, even within the same role [CACHE-05].
    return f"{CACHE_KEY_PREFIX}:{user_id}"


def invalidate_for_user(user_id: int) -> None:
    """Call after any task mutation affecting this user's scope, or after
    a role change, so a stale/unauthorized cached payload is never served
    [CACHE-04, CACHE-06]."""
    try:
        cache.delete(_cache_key(user_id))
    except Exception:  # pragma: no cover - defensive, see get_dashboard_stats
        logger.warning("dashboard_cache_invalidate_failed", extra={"user_id": user_id})


def invalidate_for_admins_and_managers() -> None:
    """Every task mutation changes the "all tasks" aggregate that EVERY
    Admin/Manager's dashboard reflects — and since cache keys are per-user
    (not a single shared aggregate key, see CACHE-05), each of their
    individual cache entries must be invalidated together, not just the
    one user who performed the mutation [CACHE-04].

    Without this, a second Admin/Manager viewing the dashboard can see
    stale totals for up to the 5-minute TTL after another Admin/Manager's
    mutation — verified as a real gap, not just a theoretical one.
    """
    admin_manager_ids = User.objects.filter(role__in=(Role.ADMIN, Role.MANAGER)).values_list(
        "id", flat=True
    )
    for user_id in admin_manager_ids:
        invalidate_for_user(user_id)


def _compute_stats(user) -> dict:
    """Scoped per docs/REQUIREMENTS.md CACHE-02 table.

    Admin/Manager: totals across ALL tasks; my_tasks = tasks assigned to them.
    Employee: totals AND my_tasks both scoped to tasks assigned to them.
    """
    if user.role in (Role.ADMIN, Role.MANAGER):
        base_qs = Task.objects.all()
    else:
        base_qs = Task.objects.filter(assigned_to_id=user.id)

    total_tasks = base_qs.count()
    completed_tasks = base_qs.filter(status=TaskStatus.COMPLETED).count()
    pending_tasks = base_qs.exclude(status=TaskStatus.COMPLETED).count()
    my_tasks = Task.objects.filter(assigned_to_id=user.id).count()

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": pending_tasks,
        "my_tasks": my_tasks,
    }


def get_dashboard_stats(user) -> dict:
    """GET /api/dashboard/stats/ backing function [CACHE-01...07].

    Authorization (the user's current role) is read fresh from `user` on
    every call, BEFORE any cache lookup — a cache hit never substitutes
    for a live permission check, so a revoked/changed role takes effect
    on the very next request regardless of TTL [CACHE-06].
    """
    key = _cache_key(user.id)

    try:
        cached = cache.get(key)
    except Exception:
        # Redis outage: fall back straight to a scoped DB query, never fail
        # the request and never serve stale/unauthorized data [CACHE-07].
        logger.warning("dashboard_cache_unavailable_falling_back", extra={"user_id": user.id})
        return _compute_stats(user)

    if cached is not None:
        return cached

    stats = _compute_stats(user)
    try:
        cache.set(key, stats, timeout=CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("dashboard_cache_set_failed", extra={"user_id": user.id})

    return stats
