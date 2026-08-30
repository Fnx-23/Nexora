from django.urls import path

from apps.accounts.api.views import LoginView, MeView, RefreshView, RegisterView, VerifyView

urlpatterns = [
    path("token/", LoginView.as_view(), name="token-obtain-pair"),
    path("token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("token/verify/", VerifyView.as_view(), name="token-verify"),
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
]
