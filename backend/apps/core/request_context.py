"""
Request-scoped "current actor" propagation for decoupled audit logging.

The audit log (see ``apps.activities``) captures *who* performed a change via
Django model signals. Signals have no access to the HTTP request, and because
authentication happens at the DRF layer (JWT), Django's classic
``AuthenticationMiddleware`` cannot see the user either. We therefore stash the
authenticated user in a :class:`contextvars.ContextVar` at the point where the
tenant context is resolved (``apps.core.api.context.apply_company_context``,
invoked by the ``IsCompanyMember`` permission) and read it back inside signal
handlers.

``ContextVar`` state is per-thread/per-async-task, so concurrent requests never
observe each other's actor. Worker threads are pooled and reused, so the value
**must** be cleared at the end of every request; that teardown lives in
``apps.core.api.middleware.RequestActorMiddleware``.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from apps.accounts.models import User

_current_actor: ContextVar[User | None] = ContextVar("nexora_current_actor", default=None)


def set_actor(user: User | None) -> Token:
    """Record the acting user for the current request context.

    Returns the :class:`~contextvars.Token` so a caller may restore the previous
    value with :func:`reset_actor` if needed.
    """
    return _current_actor.set(user)


def get_actor() -> User | None:
    """Return the acting user for the current context, or ``None`` if unset.

    ``None`` is expected and valid: it denotes a system action (management
    command, data migration, factory in tests, or an unauthenticated request).
    """
    return _current_actor.get()


def reset_actor(token: Token | None = None) -> None:
    """Clear the current actor.

    With a ``token`` the previous value is restored; without one the actor is
    reset to ``None``. Called from middleware teardown so a pooled worker thread
    never leaks one request's actor into the next.
    """
    if token is not None:
        try:
            _current_actor.reset(token)
            return
        except (ValueError, LookupError):  # pragma: no cover - defensive
            pass
    _current_actor.set(None)
