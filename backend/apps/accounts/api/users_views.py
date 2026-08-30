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

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name", "role"]


class UsersViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Read-only directory of users who belong to the active company."""

    permission_classes = [IsAuthenticated, IsCompanyMember]
    serializer_class = MemberSerializer
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["email", "date_joined"]

    def get_queryset(self) -> QuerySet[User]:
        if getattr(self, "swagger_fake_view", False):  # schema generation
            return User.objects.none()

        role_within_company = Subquery(
            Membership.objects.filter(
                user=OuterRef("pk"),
                company=self.request.company,
                is_active=True,
            ).values("role")[:1]
        )
        return (
            User.objects.filter(
                memberships__company=self.request.company,
                memberships__is_active=True,
            )
            .annotate(role=role_within_company)
            .order_by("date_joined")
        )
