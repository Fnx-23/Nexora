"""Metadata sanitization for audit records.

The audit log must **never** persist sensitive information (passwords, tokens,
secrets, session identifiers, government or payment identifiers, ...). Signal
handlers already construct metadata from a small allow-list of harmless fields,
but :func:`sanitize_metadata` is the defense-in-depth backstop applied to every
record: it drops sensitive-looking keys, coerces values to JSON-safe
primitives, and caps size/depth so a stray large or nested payload cannot bloat
the table.
"""

from __future__ import annotations

import re
from typing import Any

_SENSITIVE_KEY_TOKENS: tuple[str, ...] = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "apikey",
    "accesskey",
    "refreshtoken",
    "authorization",
    "bearer",
    "credential",
    "privatekey",
    "session",
    "cookie",
    "ssn",
    "socialsecurity",
    "creditcard",
    "cardnumber",
    "cvv",
    "cvc",
    "securitycode",
    "passcode",
    "otp",
    "salt",
    "signature",
)

_MAX_DEPTH = 4
_MAX_KEYS_PER_DICT = 50
_MAX_LIST_ITEMS = 50
_MAX_STRING_LENGTH = 500

_NON_ALNUM = re.compile(r"[^a-z0-9]")

_JSON_PRIMITIVES = (bool, int, float)


def _normalize_key(key: Any) -> str:
    return _NON_ALNUM.sub("", str(key).lower())


def is_sensitive_key(key: Any) -> bool:
    """Return ``True`` if ``key`` looks like it names a secret/credential."""
    normalized = _normalize_key(key)
    return any(token in normalized for token in _SENSITIVE_KEY_TOKENS)


def _coerce_scalar(value: Any) -> Any:
    if value is None or isinstance(value, _JSON_PRIMITIVES):
        return value
    text = str(value)
    if len(text) > _MAX_STRING_LENGTH:
        text = text[:_MAX_STRING_LENGTH] + "…"
    return text


def _sanitize(value: Any, depth: int) -> Any:
    if value is None or isinstance(value, (*_JSON_PRIMITIVES, str)):
        return _coerce_scalar(value)

    if isinstance(value, dict):
        if depth >= _MAX_DEPTH:
            return "[nested]"
        result: dict[str, Any] = {}
        for raw_key, raw_value in list(value.items())[:_MAX_KEYS_PER_DICT]:
            key = str(raw_key)
            if is_sensitive_key(key):
                result[key] = "[REDACTED]"
                continue
            result[key] = _sanitize(raw_value, depth + 1)
        return result

    if isinstance(value, (list | tuple | set)):
        if depth >= _MAX_DEPTH:
            return "[nested]"
        return [_sanitize(item, depth + 1) for item in list(value)[:_MAX_LIST_ITEMS]]

    return _coerce_scalar(value)


def sanitize_metadata(metadata: Any) -> dict[str, Any]:
    """Return a JSON-safe, secret-free copy of ``metadata``.

    Always returns a ``dict``: non-dict input is discarded in favour of an empty
    mapping so the stored shape is predictable.
    """
    if not isinstance(metadata, dict):
        return {}
    return _sanitize(metadata, depth=0)
