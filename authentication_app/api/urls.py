from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import (
    RegistrationView,
    LoginView,
    ActivateView,
    LogoutAndBlacklistView,
    CookieTokenRefreshView,
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("register/", RegistrationView.as_view(), name="registration"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutAndBlacklistView.as_view(), name="logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("activate/<uidb64>/<token>/", ActivateView.as_view(), name="activate"),
]
