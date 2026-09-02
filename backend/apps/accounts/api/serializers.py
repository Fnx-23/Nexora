"""Serializers for accounts (auth, registration, current user)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.accounts.validation import validate_avatar_image
from apps.companies.api.serializers import CompanySerializer, MembershipSerializer

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    created_at = serializers.DateTimeField(source="date_joined", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "avatar",
            "full_name",
            "is_email_verified",
            "created_at",
        ]


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Short-lived JWT access token.")
    refresh = serializers.CharField(help_text="Long-lived JWT refresh token.")
    user = UserSerializer(read_only=True)


class LoginSerializer(TokenObtainPairSerializer):
    """Extends the default token response with the authenticated user."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class MeSerializer(UserSerializer):
    memberships = serializers.SerializerMethodField()
    active_company = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [*UserSerializer.Meta.fields, "memberships", "active_company"]

    @extend_schema_field(MembershipSerializer(many=True))
    def get_memberships(self, obj) -> list[dict]:
        memberships = (
            obj.memberships.filter(is_active=True, company__is_active=True)
            .select_related("company")
            .order_by("created_at")
        )
        return MembershipSerializer(memberships, many=True).data

    @extend_schema_field(CompanySerializer(allow_null=True))
    def get_active_company(self, obj):
        request = self.context.get("request")
        company = getattr(request, "company", None)
        return CompanySerializer(company).data if company else None


class AvatarUpdateSerializer(serializers.ModelSerializer):
    """
    Minimal profile mutation: avatar upload, first_name, last_name.

    All security checks live in ``apps.accounts.validation.validate_avatar_image``.
    """

    class Meta:
        model = User
        fields = ["avatar", "first_name", "last_name"]

    def validate_avatar(self, value):
        return validate_avatar_image(value)


class RegisterInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company_name = serializers.CharField(max_length=120, trim_whitespace=True)

    def validate_email(self, value: str) -> str:
        return value.lower()

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value


class RegisterResponseSerializer(serializers.Serializer):
    """Shapes the registration payload for both clients and OpenAPI docs."""

    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    tokens = serializers.DictField(
        child=serializers.CharField(),
        help_text="JWT access/refresh pair for the new account.",
    )
