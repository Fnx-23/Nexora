"""
Company slug allocation race regression tests (audit L-13).

Two concurrent registrations of the same company name compute the same
candidate slug; the database unique constraint must arbitrate without
surfacing a 500.
"""

import pytest
from apps.accounts.services import register_company
from apps.companies.models import Company
from django.db import IntegrityError

from tests.conftest import DEFAULT_PASSWORD

PASSWORD = DEFAULT_PASSWORD


def _register(email: str, company_name: str):
    return register_company(
        email=email,
        password=PASSWORD,
        first_name="A",
        last_name="B",
        company_name=company_name,
    )


@pytest.mark.django_db
def test_free_slug_is_used_unchanged():
    result = _register("owner1@acme.test", "Fresh Co")

    assert result.company.slug == "fresh-co"


@pytest.mark.django_db
def test_taken_slug_gets_next_suffix():
    _register("owner1@acme.test", "Acme")
    result = _register("owner2@acme.test", "Acme")

    assert result.company.slug == "acme-2"
    assert Company.objects.filter(slug__in=["acme", "acme-2"]).count() == 2


@pytest.mark.django_db
def test_concurrent_slug_race_retries_and_succeeds(monkeypatch):
    """Simulate the race: the first INSERT loses, the retry wins — no 500."""
    real_create = Company.objects.create
    attempts = {"count": 0}

    def racy_create(*args, **kwargs):
        if attempts["count"] == 0:
            attempts["count"] += 1
            raise IntegrityError("duplicate key value violates unique constraint")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(Company.objects, "create", racy_create)

    result = _register("racer@acme.test", "Clash Co")

    assert attempts["count"] == 1
    assert result.company.slug == "clash-co-2"
    assert Company.objects.filter(slug=result.company.slug).exists()


@pytest.mark.django_db
def test_persistent_slug_clash_surfaces_domain_error(monkeypatch):
    """If every attempt collides, callers get ApplicationError — never a raw 500."""
    monkeypatch.setattr(
        Company.objects,
        "create",
        lambda *a, **kw: (_ for _ in ()).throw(IntegrityError("always clashing")),
    )

    from apps.core.exceptions import ApplicationError

    with pytest.raises(ApplicationError):
        _register("doomed@acme.test", "Hopeless Co")


@pytest.mark.django_db
def test_api_registration_survives_simultaneous_same_name_companies(api_client):
    """End-to-end: two same-named companies through the API both succeed."""
    from tests.conftest import DEFAULT_PASSWORD as P

    def payload(email):
        return {
            "email": email,
            "password": P,
            "first_name": "A",
            "last_name": "B",
            "company_name": "Same Name Inc",
        }

    first = api_client.post("/api/v1/auth/register/", payload("one@same.test"))
    second = api_client.post("/api/v1/auth/register/", payload("two@same.test"))

    assert first.status_code == 201
    assert second.status_code == 201
    slugs = {first.json()["company"]["slug"], second.json()["company"]["slug"]}
    assert len(slugs) == 2
    assert Company.objects.filter(slug__in=slugs).count() == 2
