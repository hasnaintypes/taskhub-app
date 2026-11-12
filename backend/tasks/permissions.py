from rest_framework.permissions import BasePermission

from accounts.models import Role


class IsTaskVisible(BasePermission):
    """Object-level visibility [RBAC-04/05/10]: Admin/Manager see all tasks;
    an Employee may only see a task assigned to them. Prevents IDOR."""

    message = "You do not have access to this task."

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.role in (Role.ADMIN, Role.MANAGER):
            return True
        return obj.assigned_to_id == user.id


class CanEditTaskFields(BasePermission):
    """Write-side guard for PATCH /api/tasks/{id}/ [RBAC-06, RBAC-A1].

    Admin/Manager may edit any field on any task. The assignee may only
    reach this view to change `status` — the serializer selection in the
    view (TaskStatusUpdateSerializer vs TaskSerializer) is what actually
    restricts *which* fields are writable; this permission only confirms
    the requester is allowed to write to the object at all.
    """

    message = "You cannot modify this task."

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
