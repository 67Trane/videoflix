from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.conf import settings
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .services import send_activation_email, send_password_reset_email
from django.shortcuts import redirect

User = get_user_model()


class RegistrationView(APIView):
    """API endpoint for user registration.

    - Accepts email and password (via RegistrationSerializer).
    - Creates a new inactive user account.
    - Sends an activation email with a token link.
    - Returns the new user’s ID and email, along with the activation token.

    Permissions:
        - Publicly accessible (AllowAny).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST requests to register a new user.

        Args:
            request (Request): DRF request containing user registration data.

        Returns:
            Response: JSON with user ID, email, and activation token
                      or validation errors with HTTP 400.
        """
        serializer = RegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Send activation email and return token for testing/debugging
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
    """API endpoint for account activation via email link.

    - Decodes the user ID from the activation link (base64 encoded).
    - Verifies the activation token.
    - Activates the user account if the token is valid.
    - Handles cases where the link is invalid, already used, or expired.

    Permissions:
        - Publicly accessible (AllowAny).
    """

    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        """Handle GET requests to activate a user account.

        Args:
            request (Request): DRF request object.
            uidb64 (str): Base64 encoded user ID from the activation link.
            token (str): Token generated for account activation.

        Returns:
            Response: JSON message indicating success or failure.
        """
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
                {"detail": "Account is already activated."},
                status=status.HTTP_200_OK,
            )

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response({"detail": "user is active"})

        return Response(
            {"detail": "Activation failed or token has expired."},
            status=status.HTTP_400_BAD_REQUEST,
        )


class LoginView(TokenObtainPairView):
    """API endpoint for user login with JWT authentication.

    - Validates credentials using the LoginSerializer.
    - Issues an access token and refresh token.
    - Stores both tokens in HTTP-only cookies for security.
    - Returns a success message and basic user info.

    Permissions:
        - Publicly accessible (AllowAny).
    """

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle POST requests for user login.

        Steps:
            1. Validate user credentials with serializer.
            2. Generate JWT access and refresh tokens.
            3. Store tokens securely in HttpOnly cookies.
            4. Return a success response with user info.

        Args:
            request (Request): DRF request object with login credentials.

        Returns:
            Response: JSON containing success message and user details.
                      Sets 'access_token' and 'refresh_token' cookies.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user

        # Call parent method to generate tokens
        response = super().post(request, *args, **kwargs)
        refresh = response.data.get("refresh")
        access = response.data.get("access")

        # Store tokens in HttpOnly cookies
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

        # Replace default response body with custom payload
        response.data = {
            "detail": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
            },
        }
        return response


class LogoutAndBlacklistView(APIView):
    """API endpoint for user logout and token blacklisting.

    - Reads the refresh token from cookies.
    - Blacklists the refresh token so it cannot be reused.
    - Deletes both access and refresh token cookies.
    - Ensures the user is fully logged out.

    Permissions:
        - Publicly accessible (AllowAny) since only the cookie is required.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Handle POST requests to log out a user.

        Steps:
            1. Retrieve refresh token from cookies.
            2. Blacklist the refresh token to prevent reuse.
            3. Delete access and refresh token cookies.
            4. Return a logout confirmation response.

        Args:
            request (Request): DRF request object with cookies.

        Returns:
            Response: JSON confirmation of logout.
                      Deletes authentication cookies.
        """
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
                "detail": (
                    "Logout successful! All tokens have been deleted. "
                    "The refresh token is now invalid."
                )
            },
            status=status.HTTP_200_OK,
        )
        # Remove authentication cookies
        resp.delete_cookie("access_token", path="/", samesite="Lax")
        resp.delete_cookie("refresh_token", path="/", samesite="Lax")
        return resp


class CookieTokenRefreshView(TokenRefreshView):
    """API endpoint to refresh the access token using a refresh token stored in cookies.

    - Reads the refresh token from the HttpOnly cookie.
    - Validates the refresh token.
    - Issues a new access token.
    - Stores the new access token in an HttpOnly cookie.
    - Returns a confirmation response.

    Permissions:
        - Publicly accessible (no explicit authentication required),
          since refresh token is taken from cookies.
    """

    def post(self, request, *args, **kwargs):
        """Handle POST requests to refresh the access token.

        Steps:
            1. Retrieve refresh token from cookies.
            2. Validate the refresh token using the serializer.
            3. If valid, generate a new access token.
            4. Store the new access token in an HttpOnly cookie.
            5. Return a success response with the new access token.

        Args:
            request (Request): DRF request object containing cookies.

        Returns:
            Response: JSON confirmation with new access token.
                      Sets 'access_token' cookie.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token is None:
            return Response(
                {"detail": "Refresh token not found!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data={"refresh": refresh_token})

        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            return Response(
                {"detail": "Refresh token invalid!"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = serializer.validated_data.get("access")

        response = Response({"detail": "Token refreshed", "access": access_token})

        # Store the new access token in HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=settings.COOKIE_SECURE,
            samesite="Lax",
        )

        return response


class PasswordResetRequestView(APIView):
    """API endpoint to request a password reset.

    - Accepts an email address from the user.
    - If a matching account exists, sends a password reset email with a token link.
    - If no account exists, still responds with success (to prevent email enumeration).
    - Always returns HTTP 200 to avoid leaking account existence.

    Permissions:
        - Publicly accessible (AllowAny).
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle POST requests for password reset.

        Args:
            request (Request): DRF request containing an email address.

        Returns:
            Response: JSON message confirming that a reset email has been sent.
                      Always returns HTTP 200, even if no matching user is found.
        """
        ser = PasswordResetRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        User = get_user_model()

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Prevents leaking whether the email exists in the system
            return Response(
                {"detail": "An email has been sent to reset your password."},
                status=status.HTTP_200_OK,
            )

        # Send password reset email with tokenized link
        send_password_reset_email(user, request)

        return Response(
            {"detail": "An email has been sent to reset your password."},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """API endpoint to confirm password reset.

    - Validates the reset link (UID + token).
    - Allows the user to set a new password.
    - Invalidates all existing JWT tokens for security.
    - Clears authentication cookies to force fresh login.

    Permissions:
        - Publicly accessible (AllowAny), as the reset token is the key.
    """

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Handle POST requests to reset a user's password.

        Args:
            request (Request): DRF request containing the new password.
            uidb64 (str): Base64 encoded user ID from the reset link.
            token (str): Password reset token.

        Returns:
            Response: JSON message confirming password reset success.
                      Also clears access/refresh token cookies.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate and set the new password
        ser = PasswordResetConfirmSerializer(data=request.data, context={"user": user})
        ser.is_valid(raise_exception=True)

        user.set_password(ser.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Invalidate all existing JWT tokens for the user (force logout everywhere)
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                OutstandingToken,
                BlacklistedToken,
            )

            for t in OutstandingToken.objects.filter(user=user):
                BlacklistedToken.objects.get_or_create(token=t)
        except Exception:
            # Fail silently if token blacklist app is not enabled
            pass

        resp = Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )

        # Clear authentication cookies
        resp.delete_cookie("access_token", path="/", samesite="Lax")
        resp.delete_cookie("refresh_token", path="/", samesite="Lax")
        return resp
