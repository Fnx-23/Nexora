from django.contrib import admin

from apps.tasks.models import Task


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
