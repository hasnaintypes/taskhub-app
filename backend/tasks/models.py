import uuid

from django.conf import settings
from django.db import models


class TaskStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In progress"
    COMPLETED = "completed", "Completed"


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        on_delete=models.SET_NULL,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_tasks",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["assigned_to", "status"]),
            models.Index(fields=["created_by"]),
        ]

    def __str__(self) -> str:
        return self.title


class TaskAssignmentEvent(models.Model):
    """One row per assignment action — the idempotency anchor for Celery
    notifications [CELERY-08/09/10, see docs/ARCHITECTURE.md §3].

    A retry of the SAME event (same `id`) must never double-notify; a NEW
    assign/reassign call always creates a new row and is eligible to notify.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(Task, related_name="assignment_events", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assignment_events_received",
        on_delete=models.CASCADE,
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="assignment_events_created",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"TaskAssignmentEvent({self.id}) task={self.task_id} -> {self.assigned_to_id}"
