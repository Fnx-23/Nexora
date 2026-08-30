"""Unit tests for audit-metadata sanitization.

These verify the defense-in-depth backstop that guarantees no sensitive
information is ever persisted in an activity's ``metadata`` (a hard requirement
of the audit log), independent of what a signal handler happens to pass in.
"""

import uuid

from apps.activities.sanitizer import is_sensitive_key, sanitize_metadata


class TestSensitiveKeyDetection:
    def test_common_secret_keys_flagged(self):
        for key in (
            "password",
            "passwd",
            "pwd",
            "api_key",
            "apiKey",
            "access_key",
            "refresh_token",
            "authorization",
            "Bearer",
            "client_secret",
            "private_key",
            "session_id",
            "cookie",
            "ssn",
            "social_security_number",
            "credit_card",
            "cardNumber",
            "cvv",
            "cvc",
            "otp",
        ):
            assert is_sensitive_key(key), key

    def test_harmless_keys_not_flagged(self):
        for key in ("name", "status", "changed_fields", "old_role", "new_status", "title"):
            assert not is_sensitive_key(key), key

    def test_detection_ignores_case_and_separators(self):
        assert is_sensitive_key("Pass-Word")
        assert is_sensitive_key("API__KEY")
        assert is_sensitive_key("refreshToken")


class TestSanitizeMetadata:
    def test_redacts_sensitive_top_level_keys(self):
        out = sanitize_metadata({"password": "hunter2", "name": "Acme"})
        assert out["password"] == "[REDACTED]"
        assert out["name"] == "Acme"

    def test_redacts_sensitive_keys_when_nested(self):
        out = sanitize_metadata({"outer": {"api_key": "abc123", "label": "ok"}})
        assert out["outer"]["api_key"] == "[REDACTED]"
        assert out["outer"]["label"] == "ok"

    def test_non_dict_input_becomes_empty_dict(self):
        assert sanitize_metadata(None) == {}
        assert sanitize_metadata("just a string") == {}
        assert sanitize_metadata([1, 2, 3]) == {}

    def test_coerces_non_json_scalars_to_strings(self):
        value = uuid.uuid4()
        out = sanitize_metadata({"entity_id": value})
        assert out["entity_id"] == str(value)

    def test_preserves_json_primitives(self):
        out = sanitize_metadata({"count": 3, "ratio": 1.5, "flag": True, "empty": None})
        assert out == {"count": 3, "ratio": 1.5, "flag": True, "empty": None}

    def test_caps_excessive_depth(self):
        deep = {"a": {"b": {"c": {"d": {"e": "too deep"}}}}}
        out = sanitize_metadata(deep)
        # Beyond the depth cap the subtree collapses to a marker rather than data.
        assert out["a"]["b"]["c"]["d"] == "[nested]"

    def test_truncates_long_strings(self):
        out = sanitize_metadata({"blob": "x" * 1000})
        assert len(out["blob"]) <= 501
        assert out["blob"].endswith("…")

    def test_truncates_large_lists(self):
        out = sanitize_metadata({"items": list(range(500))})
        assert len(out["items"]) <= 50
