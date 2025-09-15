from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import User
from .serializers import (
    PasswordChangeSerializer,
    UserCreateSerializer,
    UserListSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List all users",
        description="Retrieve a paginated list of all users in the banking system.",
        tags=["Users"],
    ),
    create=extend_schema(
        summary="Create a new user",
        description="Create a new user in the banking system.",
        tags=["Users"],
    ),
    retrieve=extend_schema(
        summary="Get user details",
        description="Retrieve detailed information about a specific user.",
        tags=["Users"],
    ),
    update=extend_schema(
        summary="Update user information",
        description="Update user information.",
        tags=["Users"],
    ),
    destroy=extend_schema(
        summary="Delete user",
        description="Delete a user from the system.",
        tags=["Users"],
    ),
)
class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for managing banking system users."""

    queryset = User.objects.all().select_related("customer")
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["role", "is_active", "customer"]
    search_fields = ["username", "email", "first_names", "last_names"]
    ordering_fields = ["username", "email", "date_joined"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return UserUpdateSerializer
        elif self.action == "list":
            return UserListSerializer
        elif self.action == "change_password":
            return PasswordChangeSerializer
        return UserSerializer

    @extend_schema(
        summary="Change user password",
        description="Change password for the authenticated user.",
        request=PasswordChangeSerializer,
        tags=["Users"],
    )
    @action(detail=False, methods=["post"])
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"message": "Password changed successfully"})

    @extend_schema(
        summary="Get current user profile",
        description="Get profile information for the currently authenticated user.",
        tags=["Users"],
    )
    @action(detail=False, methods=["get"])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
