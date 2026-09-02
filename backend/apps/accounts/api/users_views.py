"""Team directory viewset: people belonging to the active company."""

from django.contrib.auth import get_user_model
from django.db.models import OuterRef, QuerySet, Subquery
from rest_framework import mixins, serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.companies.models import Membership
from apps.core.api.permissions import IsCompanyMember

User = get_user_model()


class MemberSerializer(serializers.ModelSerializer):
    """Flat representation of a company member (user fields + company role)."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)
    role = serializers.CharField(read_only=True)
    membership_id = serializers.UUIDField(read_only=True)
    membership_active = serializers.BooleanField(read_only=True)
    joined_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "role",
            "membership_id",
            "membership_active",
            "joined_at",
        ]


class UsersViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only directory of users who belong to the active company."""

    permission_classes = [IsAuthenticated, IsCompanyMember]
    serializer_class = MemberSerializer
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined"]

    def get_queryset(self) -> QuerySet[User]:
        if getattr(self, "swagger_fake_view", False):
            return User.objects.none()

        active_membership = Membership.objects.filter(
            user=OuterRef("pk"),
            company=self.request.company,
        )
        role_within_company = Subquery(active_membership.values("role")[:1])
        membership_id = Subquery(active_membership.values("id")[:1])
        membership_active = Subquery(active_membership.values("is_active")[:1])
        joined_at = Subquery(active_membership.values("created_at")[:1])

        return (
            User.objects.filter(
                memberships__company=self.request.company,
            )
            .distinct()
            .annotate(
                role=role_within_company,
                membership_id=membership_id,
                membership_active=membership_active,
                joined_at=joined_at,
            )
            .order_by("-membership_active", "date_joined")
        )
