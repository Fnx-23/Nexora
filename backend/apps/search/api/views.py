"""Global search endpoint."""

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.api.permissions import IsCompanyMember
from apps.search.services import search_company


@extend_schema(
    tags=["Search"],
    summary="Global search across the active company",
    description=(
        "Returns grouped matches for projects, customers, tasks and team "
        "members within the caller's active company. Each category is "
        "hard-limited, and queries never cross the tenant boundary."
    ),
    parameters=[
        OpenApiParameter(
            name="q",
            description="Search term (case-insensitive substring).",
            required=False,
            type=str,
        ),
    ],
)
class SearchView(APIView):
    """Single efficient query set for the command palette."""

    permission_classes = [IsAuthenticated, IsCompanyMember]

    def get(self, request):
        return Response(search_company(request.company, request.query_params.get("q")))
