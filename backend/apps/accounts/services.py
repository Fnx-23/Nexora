"""Business logic for accounts and workspace registration."""

from __future__ import annotations

import dataclasses

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from apps.companies.models import Company, Membership, RoleChoices
from apps.core.exceptions import ApplicationError

User = get_user_model()

DUPLICATE_EMAIL_MESSAGE = "A user with this email already exists."
SLUG_EXHAUSTED_MESSAGE = "Could not allocate a unique company identifier."

_MAX_SLUG_ATTEMPTS = 25


@dataclasses.dataclass(frozen=True)
class RegistrationResult:
    user: User
    company: Company
    membership: Membership


def _create_company_with_unique_slug(name: str) -> Company:
    """
    Insert a company whose slug never collides, even under concurrency.

    ``slugify(name)[:50]`` is deterministic, so two simultaneous registrations
    of the same company name both compute the same candidate slug. Instead of
    a check-then-insert race, each attempt simply tries to insert; a unique
    constraint violation rolls back *that statement's* savepoint and retries
    with the next numeric suffix. The database constraint remains the single
    source of truth.
    """
    base = slugify(name)[:50] or "company"
    for counter in range(1, _MAX_SLUG_ATTEMPTS + 1):
        slug = base if counter == 1 else f"{base}-{counter}"
        try:
            with transaction.atomic():
                return Company.objects.create(name=name, slug=slug)
        except IntegrityError:
            continue
    raise ApplicationError(SLUG_EXHAUSTED_MESSAGE)


@transaction.atomic
def register_company(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    company_name: str,
) -> RegistrationResult:
    """
    Create a user together with their own company and ADMIN membership.

    This is the bootstrap path for new tenants.
    """
    email = User.objects.normalize_email(email)
    if User.objects.filter(email__iexact=email).exists():
        raise ApplicationError(DUPLICATE_EMAIL_MESSAGE)

    try:
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
    except IntegrityError:
        raise ApplicationError(DUPLICATE_EMAIL_MESSAGE) from None
    company = _create_company_with_unique_slug(company_name)
    membership = Membership.objects.create(
        company=company,
        user=user,
        role=RoleChoices.ADMIN,
    )
    return RegistrationResult(user=user, company=company, membership=membership)
