from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    MANAGER = "MANAGER", "Manager"
    EMPLOYEE = "EMPLOYEE", "Employee"


class User(AbstractUser):
    """Custom user with an explicit role field.

    A `role` field (rather than Django Groups) is used for exactly three
    fixed roles — see docs/ARCHITECTURE.md §2 for the documented rationale.
    """

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.EMPLOYEE)

    @property
    def is_admin(self) -> bool:
        return self.role == Role.ADMIN

    @property
    def is_manager(self) -> bool:
        return self.role == Role.MANAGER

    @property
    def is_employee(self) -> bool:
        return self.role == Role.EMPLOYEE

    @property
    def can_manage_tasks(self) -> bool:
        """Admin or Manager: create/assign/view-all tasks [RBAC-03/04]."""
        return self.role in (Role.ADMIN, Role.MANAGER)

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"
