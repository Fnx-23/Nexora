"""
Per-request company (tenant) context resolution.

The active company is derived from the authenticated user's memberships:

1. The ``X-Company-Id`` header, when it matches one of the user's active
   memberships. This future-proofs the API for users belonging to several
   companies.
2. Otherwise, the user's oldest active membership.

The result is cached on the request so permissions, viewsets and serializers
all observe the same tenant for the duration of a request.
"""

from __future__ import annotations

import uuid

from django.http import HttpRequest
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.companies.models import Company, Membership
from apps.core.request_context import set_actor


def apply_company_context(request: HttpRequest) -> Company | None:
    """Resolve the company context and expose it on the request.

    Also records the authenticated user as the current audit *actor* (read by
    model signals in ``apps.activities``). This is the single choke point every
    tenant-scoped request passes through via the ``IsCompanyMember`` permission,
    which keeps audit-actor capture out of individual views.
    """
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        set_actor(user)

    company, membership = resolve_company(request)
    if company is not None and membership is not None:
        request.company = company
        request.company_role = membership.role
    return company


def resolve_company(request: HttpRequest) -> tuple[Company | None, Membership | None]:
    """Return the ``(company, membership)`` context for the request.

    The active company is derived from the authenticated user's memberships:

    1. The ``X-Company-Id`` header, when it matches one of the user's active
       memberships (future-proofs the API for multi-company users).
    2. Otherwise, the user's oldest active membership (default behaviour).

    When ``X-Company-Id`` is *explicitly* provided but cannot be honored
    (malformed, foreign, or nonexistent company) the request is rejected
    rather than silently falling back to a different tenant. This prevents a
    stale/wrong header from transparently operating on the wrong company.
    """
    if hasattr(request, "_company_context"):
        return request._company_context

    company: Company | None = None
    membership: Membership | None = None

    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        memberships = list(
            Membership.objects.filter(
                user=user,
                is_active=True,
                company__is_active=True,
            )
            .select_related("company")
            .order_by("created_at")
        )

        requested_id = (request.headers.get("X-Company-Id", "") or "").strip()
        target: Membership | None = None
        if requested_id:
            try:
                uuid.UUID(requested_id)
            except ValueError:
                raise ValidationError("X-Company-Id must be a valid UUID.") from None
            target = next(
                (m for m in memberships if str(m.company_id) == requested_id),
                None,
            )
            if target is None:
                raise PermissionDenied("You are not a member of the requested company.")
        elif memberships:
            target = memberships[0]

        if target is not None:
            company = target.company
            membership = target

    request._company_context = (company, membership)  # type: ignore[attr-defined]
    return request._company_context  # type: ignore[attr-defined]
