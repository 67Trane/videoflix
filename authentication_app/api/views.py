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

User = get_user_model()


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        path = reverse("activate", kwargs={"uidb64": uidb64, "token": token})
        activation_url = request.build_absolute_uri(path)

        # E-Mail versenden (nutzt DEFAULT_FROM_EMAIL / SMTP aus deiner .env)
        send_mail(
            subject="Activate your Videoflix account",
            message=(
                "Hi,\n\n"
                "Please confirm your registration by clicking the link below:\n"
                f"{activation_url}\n\n"
                "If you didn’t sign up for Videoflix, you can safely ignore this email."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=False,
        )

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

        # Idempotent: if already active, still return 200
        if user.is_active:
            return Response(
                {"detail": "Account is already activated."}, status=status.HTTP_200_OK
            )

        # Verify token and activate
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response(
                {"detail": "Account activated successfully."}, status=status.HTTP_200_OK
            )

        # Token invalid or expired
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

        response = Response({"detail": "Token refreshed", "access": access_token})

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

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        path = reverse("password_confirm", kwargs={"uidb64": uidb64, "token": token})
        reset_url = request.build_absolute_uri(path)

        send_mail(
            subject="Reset your Videoflix password",
            message=(
                "Hi,\n\n"
                "We received a request to reset your password.\n"
                f"Click the link below (valid for a limited time):\n{reset_url}\n\n"
                "If you didn’t request this, you can safely ignore this email."
            ),
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            recipient_list=[user.email],
            fail_silently=True,  # in development you can set this to False
        )

        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        # 1) user auflösen
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 2) token prüfen
        if not token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3) jetzt validieren – mit user im Context
        ser = PasswordResetConfirmSerializer(data=request.data, context={"user": user})
        ser.is_valid(raise_exception=True)

        # 4) Passwort setzen
        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])

        # 5) (Optional) Invalidate all refresh tokens if blacklist is enabled
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken,
                BlacklistedToken,
            )

            for t in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=t)
        except Exception:
            # Blacklist not enabled or not migrated: ignore
            pass

        # 6) Return success + (optional) clear JWT cookies to force fresh login everywhere
        resp = Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
        # If you store JWTs in cookies, it’s sensible to clear them now:
        resp.delete_cookie("access_token", path="/", samesite="Lax")
        resp.delete_cookie("refresh_token", path="/", samesite="Lax")
        return resp
