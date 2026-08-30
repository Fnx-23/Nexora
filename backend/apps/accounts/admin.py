from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.core.files.uploadedfile import UploadedFile

from apps.accounts.models import User
from apps.accounts.validation import validate_avatar_image


class AvatarValidatingUserChangeForm(UserChangeForm):
    """
    Admin change form that runs the shared avatar validation on new uploads.

    Without it, staff could push an unchecked file straight through the admin,
    bypassing the API-layer validation. Only freshly uploaded files are
    inspected; an unchanged stored avatar is left untouched.
    """

    class Meta(UserChangeForm.Meta):
        model = User

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if isinstance(avatar, UploadedFile):
            validate_avatar_image(avatar)
        return avatar


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = AvatarValidatingUserChangeForm
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_active", "is_staff", "date_joined"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = [
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "avatar")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": ("email", "password1", "password2"),
            },
        ),
    ]
