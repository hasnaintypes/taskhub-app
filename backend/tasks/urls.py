from django.urls import path

from .views import TaskAssignView, TaskDetailView, TaskListCreateView

urlpatterns = [
    path("tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("tasks/<int:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("tasks/<int:pk>/assign/", TaskAssignView.as_view(), name="task-assign"),
]
