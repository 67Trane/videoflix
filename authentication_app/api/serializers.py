from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration.

    - Validates email and password during signup.
    - Ensures the user enters the same password twice.
    - Runs Django’s built-in password validation.
    - Creates an inactive user (activation via email required).
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate(self, attrs):
        """Ensure passwords match and validate password strength.

        Args:
            attrs (dict): Input data containing email, password, and confirmed_password.

        Raises:
            ValidationError: If passwords do not match or password is invalid.

        Returns:
            dict: Validated attributes without `confirmed_password`.
        """
        password = attrs.get("password")
        confirmed_password = attrs.pop("confirmed_password", None)

        if password != confirmed_password:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match"}
            )

        validate_password(password)
        return attrs

    def validate_email(self, value):
        """Normalize and validate email uniqueness.

        Args:
            value (str): Email provided by the user.

        Raises:
            ValidationError: If the email is already registered.

        Returns:
            str: Normalized email (lowercase, no leading/trailing spaces).
        """
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        """Create a new inactive user instance.

        - Username is set to the email.
        - Account is inactive until activated via email confirmation.

        Args:
            validated_data (dict): Validated registration data.

        Returns:
            User: Newly created User instance.
        """
        email = validated_data["email"]
        user = User(email=email, username=email, is_active=False)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Serializer for user login with JWT.

    - Authenticates users using email and password.
    - Requires that the account is activated before login.
    - Returns both access and refresh JWT tokens if successful.
    """

    # Use email instead of username for authentication
    username_field = "email"

    def validate(self, attrs):
        """Validate user credentials.

        Steps:
            1. Look up the user by email.
            2. Ensure the account exists and is active.
            3. Verify the password.
            4. Generate access and refresh tokens.

        Args:
            attrs (dict): Login credentials (email and password).

        Raises:
            AuthenticationFailed: If credentials are invalid or account is inactive.

        Returns:
            dict: JWT tokens {"refresh": str, "access": str}.
        """
        email = attrs.get("email")
        password = attrs.get("password")

        User = get_user_model()
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise AuthenticationFailed(
                "No active account found with the given credentials"
            )

        if not user.is_active:
            raise AuthenticationFailed("Account is not activated")

        if not user.check_password(password):
            raise AuthenticationFailed(
                "No active account found with the given credentials"
            )

        # Store the authenticated user for later use
        self.user = user

        # Generate access and refresh JWT tokens
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset.

    - Validates that the new password and confirmation match.
    - Runs Django’s password validators on the new password.
    - Requires the `user` to be passed in the serializer context
      (so validators can apply user-specific checks).
    """

    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Ensure the new password is valid and matches confirmation.

        Args:
            attrs (dict): Input data containing `new_password` and `confirm_password`.

        Raises:
            ValidationError: If passwords do not match or password is too weak.

        Returns:
            dict: Validated data with password fields.
        """
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # Run Django's built-in password validators
        user = self.context.get("user")
        validate_password(attrs["new_password"], user=user)

        return attrs
