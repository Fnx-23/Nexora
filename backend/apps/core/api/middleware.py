"""
Exposure gating for infrastructure surfaces (audit L-10).

Two developer/operator surfaces are gated per request by environment-driven
feature flags:

* ``/admin/**``            -> ``ADMIN_ENABLED``
* ``/api/schema|docs|redoc`` -> ``API_DOCS_ENABLED``

A disabled surface answers 404 — indistinguishable from a route that does
not exist — without touching any business view. Flags are read per request,
so toggling them takes effect immediately (no restart) and both states are
testable.

Defaults live in settings: development enables everything; production
disables the schema/docs endpoints unless explicitly opted in
(see ``config/settings/production.py``).
"""

from django.conf import settings
from django.http import Http404

from apps.core.request_context import reset_actor

_DOCS_PREFIXES = ("/api/schema", "/api/docs", "/api/redoc")


class SurfaceExposureMiddleware:
    """404-gate admin and API documentation according to feature flags."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/admin/") and not getattr(settings, "ADMIN_ENABLED", True):
            raise Http404("Admin is disabled.")
        if path.startswith(_DOCS_PREFIXES) and not getattr(settings, "API_DOCS_ENABLED", True):
            raise Http404("API documentation is disabled.")
        return self.get_response(request)


class RequestActorMiddleware:
    """Clear the request-scoped audit actor once each request completes.

    The actor is *set* later in the request lifecycle, at the DRF permission
    layer (``apps.core.api.context.apply_company_context``), because JWT
    authentication runs there rather than in Django middleware. This middleware
    only guarantees teardown: worker threads are pooled and ``ContextVar`` state
    persists on a thread, so without an explicit reset one request's actor could
    bleed into the next request served by the same thread.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        reset_actor()
        try:
            return self.get_response(request)
        finally:
            reset_actor()
