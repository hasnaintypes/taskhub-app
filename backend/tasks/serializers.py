from rest_framework import serializers

from accounts.models import User

from .models import Task


class TaskSerializer(serializers.ModelSerializer):
    """Read/write serializer for Admin/Manager — used for list, retrieve and
    general field edits (title/description/status).

    `assigned_to` is deliberately READ-ONLY here: reassignment must go
    through `POST /api/tasks/{id}/assign/` so it always creates a
    `TaskAssignmentEvent` and triggers the notification pipeline. Allowing
    it on a generic PATCH would let a reassignment silently skip
    CELERY-01's notification requirement [RBAC-A1].
    """

    assigned_to = serializers.PrimaryKeyRelatedField(read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "assigned_to",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "assigned_to", "created_by", "created_at", "updated_at"]


class TaskCreateSerializer(TaskSerializer):
    """Create-only variant: `assigned_to` is writable here because an
    initial assignee at creation time is handled by `services.create_task`,
    which creates the matching `TaskAssignmentEvent` itself — the same
    guarantee the read-only restriction above protects on update."""

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), allow_null=True, required=False
    )

    class Meta(TaskSerializer.Meta):
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]


class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """Restricted serializer for an assignee updating only `status` [RBAC-06, RBAC-A1]."""

    class Meta:
        model = Task
        fields = ["id", "status"]
        read_only_fields = ["id"]


class AssignTaskSerializer(serializers.Serializer):
    """POST /api/tasks/{id}/assign/ body: {"assigned_to": <user_id>} [CELERY-01]."""

    assigned_to = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    def validate_assigned_to(self, user: User) -> User:
        # Business rule: tasks are assigned to people who actually do the work.
        # Admin/Manager accounts may still receive a task (e.g. assign to self),
        # so no role restriction is applied here beyond "must be a real user".
        return user
