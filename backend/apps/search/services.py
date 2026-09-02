"""Efficient, tenant-scoped global search across Nexora entities.

Every queryset is bounded (``[:PER_CATEGORY_LIMIT]`` applying a SQL-level
``LIMIT``) and filterable on indexed name fields. ``icontains`` keeps the
semantics identical on SQLite (tests) and PostgreSQL (production), and treats
LIKE metacharacters such as ``%`` and ``_`` as literal characters.
"""

from django.db.models import Q

from apps.companies.models import Membership
from apps.customers.models import Customer
from apps.projects.models import Project
from apps.tasks.models import Task

SEARCH_QUERY_MAX_LENGTH = 100
PER_CATEGORY_LIMIT = 5


def _user_label(user) -> str:
    """Full name when available, otherwise the email address."""
    if user is None:
        return None
    full_name = user.get_full_name().strip()
    return full_name or user.email


def _clean_query(raw_query: str | None) -> str:
    return (raw_query or "").strip()[:SEARCH_QUERY_MAX_LENGTH]


def search_company(company, raw_query: str | None) -> dict:
    """Return grouped, limited matches scoped to ``company``."""
    payload = {
        "query": (raw_query or "").strip(),
        "projects": [],
        "customers": [],
        "tasks": [],
        "members": [],
    }

    query = _clean_query(raw_query)
    if not query:
        return payload

    projects = (
        Project.objects.select_related("manager")
        .filter(company=company, name__icontains=query)
        .order_by("-created_at")[:PER_CATEGORY_LIMIT]
    )
    payload["projects"] = [
        {
            "id": str(project.pk),
            "name": project.name,
            "status": project.status,
            "manager_name": _user_label(project.manager),
            "link": f"/projects/{project.pk}",
        }
        for project in projects
    ]

    customers = Customer.objects.filter(company=company, name__icontains=query).order_by(
        "-created_at"
    )[:PER_CATEGORY_LIMIT]
    payload["customers"] = [
        {
            "id": str(customer.pk),
            "name": customer.name,
            "company_name": customer.company_name,
            "link": "/customers",
        }
        for customer in customers
    ]

    tasks = (
        Task.objects.select_related("project", "assignee")
        .filter(company=company, title__icontains=query)
        .order_by("-created_at")[:PER_CATEGORY_LIMIT]
    )
    payload["tasks"] = [
        {
            "id": str(task.pk),
            "title": task.title,
            "status": task.status,
            "project_name": task.project.name if task.project else None,
            "assignee_name": _user_label(task.assignee),
            "link": f"/tasks/{task.pk}",
        }
        for task in tasks
    ]

    members = (
        Membership.objects.select_related("user")
        .filter(company=company, is_active=True)
        .filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__email__icontains=query)
        )
        .order_by("-created_at")[:PER_CATEGORY_LIMIT]
    )
    payload["members"] = [
        {
            "id": str(membership.user_id),
            "name": _user_label(membership.user),
            "email": membership.user.email,
            "role": membership.role,
            "link": "/team",
        }
        for membership in members
    ]

    return payload
