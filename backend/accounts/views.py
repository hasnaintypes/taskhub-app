import logging

from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsAdmin, IsAdminOrManager
from .serializers import LoginSerializer, UserCreateSerializer, UserSerializer

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name="get")
class SessionView(APIView):
    """GET /api/auth/session/ — bootstrap endpoint.

    Always sets the CSRF cookie (readable by Angular, not HttpOnly) and
    reports whether the current session is authenticated [AUTH-04, AUTH-10].
    """

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"authenticated": request.user.is_authenticated})


class LoginView(APIView):
    """POST /api/auth/login/ [AUTH-01]."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)  # rotates the session key [SEC-01]
        logger.info("user_login", extra={"user_id": user.id, "role": user.role})
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/ [AUTH-02]."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info("user_logout", extra={"user_id": request.user.id})
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """GET /api/auth/me/ [AUTH-03]."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserListCreateView(generics.ListCreateAPIView):
    """GET /api/users/ (Admin, Manager) · POST /api/users/ (Admin only) [RBAC-02]."""

    queryset = User.objects.all().order_by("username")

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAdmin()]
        return [IsAdminOrManager()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer
