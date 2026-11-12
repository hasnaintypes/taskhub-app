from django.contrib import admin

from .models import Task, TaskAssignmentEvent


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "assigned_to", "created_by", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description")


@admin.register(TaskAssignmentEvent)
class TaskAssignmentEventAdmin(admin.ModelAdmin):
    list_display = ("id", "task", "assigned_to", "assigned_by", "notified", "created_at")
    list_filter = ("notified",)
