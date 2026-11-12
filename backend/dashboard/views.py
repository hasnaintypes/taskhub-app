from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_dashboard_stats


class DashboardStatsView(APIView):
    """GET /api/dashboard/stats/ [CACHE-01]."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_dashboard_stats(request.user))
