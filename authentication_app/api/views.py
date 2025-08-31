from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.conf import settings
from django.utils.encoding import force_bytes, force_str
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .services import send_activation_email, send_password_reset_email

User = get_user_model()


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        token = send_activation_email(user, request)

        return Response(
            {
                "user": {
                    "id": user.id,
                    "email": user.email,
                },
                "token": token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid activation link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"detail": "Account is already activated."}, status=status.HTTP_200_OK
            )

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response(
                {"detail": "Account activated successfully."}, status=status.HTTP_200_OK
            )

        return Response(
            {"detail": "Activation failed or token has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        access = response.data.get("access")

        response.set_cookie(
            key="access_token",
            value=access,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
        )

        response.data = {
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
            },
        }
        return response


class LogoutAndBlacklistView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_cookie = request.COOKIES.get("refresh_token")

        if not refresh_cookie:
            return Response(
                {"detail": "Refresh-Token missing"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RefreshToken(refresh_cookie).blacklist()
        except TokenError:
            return Response(
                {"detail": "Refresh-Token expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        resp = Response(
            {
                "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
            },
            status=status.HTTP_200_OK,
        )
        resp.delete_cookie("access_token", path="/", samesite="Lax")
        resp.delete_cookie("refresh_token", path="/", samesite="Lax")
        return resp


class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except:
            return Response(
                {"detail": "Refresh token invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")

        response = Response(
            {"detail": "Token refreshed", "access": access_token})

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
        )

        return response


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        User = get_user_model()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "An email has been sent to reset your password."},
                status=status.HTTP_200_OK,
            )

        send_password_reset_email(user, request)

        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ser = PasswordResetConfirmSerializer(
            data=request.data, context={"user": user})
        ser.is_valid(raise_exception=True)

        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])

        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken,
                BlacklistedToken,
            )

            for t in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=t)
        except Exception:

            pass

        resp = Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )

        resp.delete_cookie("access_token", path="/", samesite="Lax")
        resp.delete_cookie("refresh_token", path="/", samesite="Lax")
        return resp
