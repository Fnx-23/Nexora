"""Dashboard aggregation endpoint — single efficient query for all KPIs."""

from datetime import date

from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.companies.models import Membership
from apps.core.api.permissions import IsCompanyMember
from apps.customers.models import Customer
from apps.projects.models import Project, ProjectStatus
from apps.tasks.models import Task, TaskStatus


class _ProjectStatusSerializer:
    """Minimal serializer for recent project list items."""

    def __init__(self, project):
        self.data = {
            "id": str(project.id),
            "name": project.name,
            "status": project.status,
            "priority": project.priority,
            "deadline": project.deadline.isoformat() if project.deadline else None,
            "updated_at": project.updated_at.isoformat(),
        }


class _TaskStatusSerializer:
    """Minimal serializer for recent task list items."""

    def __init__(self, task):
        self.data = {
            "id": str(task.id),
            "title": task.title,
            "status": task.status,
            "priority": task.priority,
            "assignee_name": (
                task.assignee.get_full_name() or task.assignee.email if task.assignee else None
            ),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "updated_at": task.updated_at.isoformat(),
        }


@extend_schema(
    tags=["Dashboard"],
    description="Aggregated dashboard data for the active company.",
)
class DashboardView(APIView):
    """Return all dashboard KPIs in a single response.

    Uses efficient aggregate queries — no N+1.
    All queries are scoped to the request's company.
    """

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        company = request.company

        project_counts = dict(
            Project.objects.filter(company=company)
            .values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        active_projects = sum(
            project_counts.get(s, 0)
            for s in (ProjectStatus.PLANNING, ProjectStatus.IN_PROGRESS, ProjectStatus.ON_HOLD)
        )
        total_projects = sum(project_counts.values())

        task_counts = dict(
            Task.objects.filter(company=company)
            .values_list("status")
            .annotate(count=Count("id"))
            .values_list("status", "count")
        )
        open_tasks = sum(
            task_counts.get(s, 0)
            for s in (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW)
        )
        completed_tasks = task_counts.get(TaskStatus.DONE, 0)
        total_tasks = sum(task_counts.values())

        today = date.today()
        overdue_tasks = Task.objects.filter(
            company=company,
            due_date__lt=today,
            status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.IN_REVIEW],
        ).count()

        total_customers = Customer.objects.filter(company=company).count()
        team_members = Membership.objects.filter(
            company=company,
            is_active=True,
        ).count()

        project_status_dist = [
            {"status": s, "label": label, "count": project_counts.get(s, 0)}
            for s, label in ProjectStatus.choices
        ]

        task_status_dist = [
            {"status": s, "label": label, "count": task_counts.get(s, 0)}
            for s, label in TaskStatus.choices
        ]

        recent_projects = Project.objects.filter(company=company).order_by("-updated_at")[:5]
        recent_tasks = (
            Task.objects.select_related("assignee")
            .filter(company=company)
            .order_by("-updated_at")[:10]
        )

        activity = []
        for p in recent_projects:
            activity.append(
                {
                    "type": "project",
                    "id": str(p.id),
                    "name": p.name,
                    "status": p.status,
                    "updated_at": p.updated_at.isoformat(),
                }
            )
        for t in recent_tasks:
            activity.append(
                {
                    "type": "task",
                    "id": str(t.id),
                    "name": t.title,
                    "status": t.status,
                    "updated_at": t.updated_at.isoformat(),
                }
            )
        activity.sort(key=lambda x: x["updated_at"], reverse=True)
        activity = activity[:10]

        return Response(
            {
                "kpis": {
                    "active_projects": active_projects,
                    "total_projects": total_projects,
                    "total_customers": total_customers,
                    "open_tasks": open_tasks,
                    "overdue_tasks": overdue_tasks,
                    "completed_tasks": completed_tasks,
                    "total_tasks": total_tasks,
                    "team_members": team_members,
                },
                "project_status_distribution": project_status_dist,
                "task_status_distribution": task_status_dist,
                "recent_projects": [_ProjectStatusSerializer(p).data for p in recent_projects],
                "recent_tasks": [_TaskStatusSerializer(t).data for t in recent_tasks],
                "activity": activity,
            }
        )
