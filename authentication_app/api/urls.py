from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    ActivateView,
    LogoutAndBlacklistView,
    CookieTokenRefreshView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)

# URL routing for authentication and account management.
urlpatterns = [
    # User registration (creates a new account and sends activation email).
    path("register/", RegistrationView.as_view(), name="registration"),

    # User login (returns JWT access/refresh tokens in cookies).
    path("login/", LoginView.as_view(), name="login"),

    # User logout (blacklists the refresh token and clears cookies).
    path("logout/", LogoutAndBlacklistView.as_view(), name="logout"),

    # Obtain a new access token using a valid refresh token (cookie-based).
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),

    # Account activation link (sent by email after registration).
    path("activate/<uidb64>/<token>/", ActivateView.as_view(), name="activate"),

    # Request a password reset (sends reset email with token).
    path("password_reset/", PasswordResetRequestView.as_view(),
         name="password_reset"),

    # Confirm password reset (validate token and set new password).
    path(
        "password_confirm/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_confirm",
    ),
]
