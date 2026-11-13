from rest_framework.permissions import BasePermission

from accounts.models import Role


class IsTaskVisible(BasePermission):
    """Object-level visibility AND write-access guard [RBAC-04/05/06/10]:
    Admin/Manager may view or write any task; an Employee may only view or
    write a task assigned to them. Used for GET, PATCH and DELETE alike —
    prevents IDOR on reads and unauthorized writes alike.

    For PATCH specifically, this only confirms the requester may touch the
    object at all; *which* fields are writable is additionally restricted
    by the view's serializer selection (`TaskStatusUpdateSerializer` for an
    Employee vs. the full `TaskSerializer` for Admin/Manager) [RBAC-A1].
    """

    message = "You do not have access to this task."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.role in (Role.ADMIN, Role.MANAGER):
            return True
        return obj.assigned_to_id == user.id


class CanDeleteTask(BasePermission):
    """Admin only [RBAC-07]."""

    message = "Only Admin may delete tasks."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class CanCreateOrAssignTask(BasePermission):
    """Admin or Manager [RBAC-03, CELERY-01]."""

    message = "Only Admin or Manager may create or assign tasks."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.MANAGER)
        )
