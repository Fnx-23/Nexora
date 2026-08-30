"""
Scoped rate-limit throttles for anonymous authentication endpoints.

Each class maps to a named rate in ``REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]``
so limits are configurable through environment variables without code changes.
Counters live in the default cache backend: Redis in production/Docker, an
in-process store only during bare local development (production refuses to
boot without Redis — see config/settings/production.py).

Client identification honors ``NUM_PROXIES`` so that requests arriving through
the nginx edge are keyed by the real client address taken from the trusted
``X-Forwarded-For`` chain rather than by the proxy IP.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    """Guards POST /api/v1/auth/token/ against password brute force."""

    scope = "auth-login"


class RegisterThrottle(AnonRateThrottle):
    """Guards POST /api/v1/auth/register/ against bulk tenant creation."""

    scope = "auth-register"


class RefreshThrottle(AnonRateThrottle):
    """
    Guards POST /api/v1/auth/token/refresh/.

    Generous by design: a legitimate client refreshes roughly once per access-
    token lifetime per session, so even many users behind one NAT address stay
    well below the limit while token-stuffing floods get shed.
    """

    scope = "auth-refresh"
