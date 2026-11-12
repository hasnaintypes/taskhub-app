from rest_framework.permissions import BasePermission

from .models import Role


class IsAdmin(BasePermission):
    """Admin-only actions: create users, administrative user management [RBAC-02]."""

    message = "Only Admin may perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == Role.ADMIN)


class IsAdminOrManager(BasePermission):
    """Admin or Manager: view user list, create/assign/view-all tasks [RBAC-02/03/04]."""

    message = "Only Admin or Manager may perform this action."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN, Role.MANAGER)
        )
