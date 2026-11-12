from django.urls import path

from .views import LoginView, LogoutView, MeView, SessionView, UserListCreateView

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/me/", MeView.as_view(), name="auth-me"),
    path("auth/session/", SessionView.as_view(), name="auth-session"),
    path("users/", UserListCreateView.as_view(), name="user-list-create"),
]
