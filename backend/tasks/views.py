from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Role

from . import services
from .models import Task
from .permissions import CanCreateOrAssignTask, CanDeleteTask, IsTaskVisible
from .serializers import (
    AssignTaskSerializer,
    TaskCreateSerializer,
    TaskSerializer,
    TaskStatusUpdateSerializer,
)


class TaskListCreateView(generics.ListCreateAPIView):
    """GET /api/tasks/ (scoped by role) · POST /api/tasks/ (Admin/Manager) [RBAC-03/04/05]."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), CanCreateOrAssignTask()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        return services.scoped_queryset_for_user(self.request.user)

    def perform_create(self, serializer):
        task = services.create_task(created_by=self.request.user, validated_data=serializer.validated_data)
        serializer.instance = task


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """GET/PATCH/DELETE /api/tasks/{id}/ [RBAC-05/06/07/10]."""

    permission_classes = [IsAuthenticated, IsTaskVisible]

    def get_queryset(self):
        # Deliberately unfiltered: IsTaskVisible.has_object_permission is
        # what enforces access, so an Employee requesting another user's
        # task ID gets a clear 403 (not a 404 that would also leak whether
        # the ID exists) [RBAC-10].
        return Task.objects.all()

    def get_serializer_class(self):
        user = self.request.user
        if self.request.method in ("PATCH", "PUT") and user.role == Role.EMPLOYEE:
            return TaskStatusUpdateSerializer
        return TaskSerializer

    def perform_update(self, serializer):
        task = self.get_object()
        if self.request.user.role == Role.EMPLOYEE:
            services.update_task_status(task=task, status=serializer.validated_data["status"])
        else:
            services.update_task_fields(task=task, validated_data=serializer.validated_data)
        serializer.instance = task

    def perform_destroy(self, instance):
        # CanDeleteTask is checked explicitly here (not via permission_classes)
        # so visibility (IsTaskVisible) and delete-rights (CanDeleteTask) stay
        # independently testable [RBAC-07].
        if not CanDeleteTask().has_permission(self.request, self):
            raise PermissionDenied("Only Admin may delete tasks.")
        services.delete_task(task=instance)


class TaskAssignView(APIView):
    """POST /api/tasks/{id}/assign/ {"assigned_to": <user_id>} [CELERY-01]."""

    permission_classes = [IsAuthenticated, CanCreateOrAssignTask]

    def post(self, request, pk: int):
        task = generics.get_object_or_404(Task, pk=pk)
        serializer = AssignTaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        services.assign_task(
            task=task,
            assigned_to=serializer.validated_data["assigned_to"],
            assigned_by=request.user,
        )

        return Response({"detail": "Notification queued."}, status=status.HTTP_202_ACCEPTED)
