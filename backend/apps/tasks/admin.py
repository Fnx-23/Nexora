from django.contrib import admin

from apps.tasks.models import (
    Task,
    TaskChecklistItem,
    TaskComment,
    TaskLabel,
    TaskSubtask,
)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "company",
        "project",
        "status",
        "priority",
        "assignee",
        "created_by",
        "due_date",
    ]
    list_filter = ["status", "priority"]
    search_fields = ["title"]


@admin.register(TaskLabel)
class TaskLabelAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "company"]
    search_fields = ["name"]


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ["task", "author", "created_at"]
    search_fields = ["body"]


@admin.register(TaskChecklistItem)
class TaskChecklistItemAdmin(admin.ModelAdmin):
    list_display = ["task", "text", "completed", "position"]


@admin.register(TaskSubtask)
class TaskSubtaskAdmin(admin.ModelAdmin):
    list_display = ["task", "title", "completed", "position"]
