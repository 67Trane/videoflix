from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed


class RegistrationSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}, "email": {"required": True}}

    def validate(self, attrs):
        password = attrs.get("password")
        confirmed_password = attrs.pop("confirmed_password", None)
        if password != confirmed_password:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match"}
            )
        validate_password(password)
        return attrs

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        email = validated_data["email"]
        user = User(email=email, username=email, is_active=False)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    username_field = "email"  # nur für Request-Parsing

    def validate(self, attrs):
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

        # Für die View verfügbar machen:
        self.user = user

        # Tokens generieren (wie bei TokenObtainPairSerializer)
        refresh = self.get_token(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    confirm_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )

        # Pass the user (from context) to Django's validators for best results
        user = self.context.get("user")
        validate_password(attrs["new_password"], user=user)
        return attrs
