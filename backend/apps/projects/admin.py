from django.contrib import admin

from apps.projects.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "company",
        "customer",
        "manager",
        "status",
        "priority",
        "start_date",
        "deadline",
    ]
    list_filter = ["status", "priority"]
    search_fields = ["name"]
