from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user (safe for Admin/Manager listing)."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "date_joined"]
        read_only_fields = fields


class UserCreateSerializer(serializers.ModelSerializer):
    """Admin-only user creation [RBAC-02]."""

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role", "password"]

    def validate_role(self, value: str) -> str:
        if value not in Role.values:
            raise serializers.ValidationError("Invalid role.")
        return value

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        request = self.context.get("request")
        user = authenticate(
            request=request,
            username=attrs.get("username"),
            password=attrs.get("password"),
        )
        if user is None:
            raise serializers.ValidationError("Invalid username or password.", code="authorization")
        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.", code="authorization")
        attrs["user"] = user
        return attrs
