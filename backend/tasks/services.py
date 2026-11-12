from django.db import transaction
from django.db.models import QuerySet

from accounts.models import Role, User
from dashboard.services import invalidate_for_user
from notifications.tasks import send_assignment_email

from .models import Task, TaskAssignmentEvent


def scoped_queryset_for_user(user: User) -> QuerySet[Task]:
    """List/detail visibility scope [RBAC-04/05]: Admin/Manager see all
    tasks; Employee sees only tasks assigned to them."""
    if user.role in (Role.ADMIN, Role.MANAGER):
        return Task.objects.all()
    return Task.objects.filter(assigned_to_id=user.id)


def _invalidate_dashboard_for(*user_ids: int | None) -> None:
    for user_id in user_ids:
        if user_id is not None:
            invalidate_for_user(user_id)


def create_task(*, created_by: User, validated_data: dict) -> Task:
    """Create a task, optionally with an initial assignee. An initial
    assignee constitutes an assignment event just like `assign_task`
    [see docs/ARCHITECTURE.md §6 invalidation rules]."""
    assigned_to = validated_data.get("assigned_to")

    with transaction.atomic():
        task = Task.objects.create(created_by=created_by, **validated_data)

        event = None
        if assigned_to is not None:
            event = TaskAssignmentEvent.objects.create(
                task=task, assigned_to=assigned_to, assigned_by=created_by
            )

        transaction.on_commit(lambda: _invalidate_dashboard_for(created_by.id, getattr(assigned_to, "id", None)))
        if event is not None:
            transaction.on_commit(lambda: send_assignment_email.delay(str(event.id)))

    return task


def assign_task(*, task: Task, assigned_to: User, assigned_by: User) -> TaskAssignmentEvent:
    """POST /api/tasks/{id}/assign/ [CELERY-01...04].

    Persists the assignment and a new TaskAssignmentEvent row in one
    transaction; the Celery job is enqueued only via `transaction.on_commit`
    so a rolled-back assignment never queues a notification.
    """
    previous_assignee_id = task.assigned_to_id

    with transaction.atomic():
        task.assigned_to = assigned_to
        task.save(update_fields=["assigned_to", "updated_at"])

        event = TaskAssignmentEvent.objects.create(
            task=task, assigned_to=assigned_to, assigned_by=assigned_by
        )

        transaction.on_commit(
            lambda: _invalidate_dashboard_for(previous_assignee_id, assigned_to.id, assigned_by.id)
        )
        transaction.on_commit(lambda: send_assignment_email.delay(str(event.id)))

    return event


def delete_task(*, task: Task) -> None:
    affected_user_id = task.assigned_to_id
    with transaction.atomic():
        task.delete()
        transaction.on_commit(lambda: _invalidate_dashboard_for(affected_user_id))


def update_task_fields(*, task: Task, validated_data: dict) -> Task:
    """General Admin/Manager edit (title/description/status — never
    `assigned_to`, which is excluded from this serializer's writable
    fields and only reachable via `assign_task` [CACHE-04]."""
    with transaction.atomic():
        for field, value in validated_data.items():
            setattr(task, field, value)
        task.save()
        transaction.on_commit(lambda: _invalidate_dashboard_for(task.assigned_to_id, task.created_by_id))
    return task


def update_task_status(*, task: Task, status: str) -> Task:
    with transaction.atomic():
        task.status = status
        task.save(update_fields=["status", "updated_at"])
        transaction.on_commit(lambda: _invalidate_dashboard_for(task.assigned_to_id, task.created_by_id))
    return task
