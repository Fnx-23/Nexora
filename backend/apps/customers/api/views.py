from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import decorators, status
from rest_framework.response import Response

from apps.companies.models import RoleChoices
from apps.core.api.permissions import role_required
from apps.core.api.views import TenantScopedModelViewSet
from apps.customers.api.serializers import CustomerSerializer
from apps.customers.models import Customer, CustomerStatus


@extend_schema_view(
    list=extend_schema(description="List customers for the active company."),
    retrieve=extend_schema(description="Retrieve a single customer."),
    create=extend_schema(description="Create a new customer."),
    update=extend_schema(description="Update a customer."),
    partial_update=extend_schema(description="Partially update a customer."),
    destroy=extend_schema(description="Permanently delete a customer."),
    archive=extend_schema(description="Soft-archive a customer (sets status to ARCHIVED)."),
)
class CustomerViewSet(TenantScopedModelViewSet):
    """CRUD + archive for the active company's customers."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filterset_fields = ["status", "is_active"]
    search_fields = ["name", "company_name", "email", "phone"]
    ordering_fields = ["name", "company_name", "created_at", "updated_at"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.action in ("destroy", "archive"):
            permissions.append(role_required(RoleChoices.MANAGER, RoleChoices.ADMIN)())
        return permissions

    @decorators.action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request, pk=None):
        """Set customer status to ARCHIVED."""
        customer = self.get_object()
        if customer.status == CustomerStatus.ARCHIVED:
            return Response(
                {"detail": "Customer is already archived."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        customer.status = CustomerStatus.ARCHIVED
        customer.is_active = False
        customer.save(update_fields=["status", "is_active", "updated_at"])
        return Response(CustomerSerializer(customer).data)
