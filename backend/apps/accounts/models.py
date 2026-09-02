"""Custom user model: email-based authentication."""

from __future__ import annotations

import os
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.core.db.models import UUIDModel


def avatar_upload_path(instance: User, filename: str) -> str:
    """
    Storage path for avatars under the user's UUID directory.

    The client-supplied name is deliberately discarded (only its validated
    extension is kept): stored names are random hex, which rules out path
    traversal, unicode look-alikes and collisions by construction.
    """
    extension = os.path.splitext(filename)[1].lower()
    return f"avatars/{instance.id}/{uuid4().hex}{extension}"


class UserManager(BaseUserManager):
    """Manager where email is the unique identifier."""

    use_in_migrations = True

    def normalize_email(self, email: str) -> str:
        """
        Lowercase the entire address, not just the domain.

        Nexora treats email addresses as case-insensitive identifiers, so the
        local part and the domain are both normalized before storage or
        lookup. This overrides Django's default, which only lowercases the
        domain.
        """
        email = email or ""
        return email.strip().lower()

    def get_by_natural_key(self, username):
        """Case-insensitive lookup so authentication ignores email casing."""
        field_name = self.model.USERNAME_FIELD
        return self.get(**{f"{field_name}__iexact": username})

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True.")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDModel):
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    avatar = models.FileField(upload_to=avatar_upload_path, blank=True)
    is_active = models.BooleanField(default=True)
    is_email_verified = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self) -> str:
        return self.email

    def get_full_name(self) -> str:
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def save(self, *args, **kwargs):
        self.email = type(self).objects.normalize_email(self.email)
        super().save(*args, **kwargs)
