from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import SavingsAccount
from .serializers import (
    SavingsAccountBalanceSerializer,
    SavingsAccountCreateSerializer,
    SavingsAccountListSerializer,
    SavingsAccountSerializer,
    SavingsAccountStatusSerializer,
    SavingsAccountSummarySerializer,
    SavingsAccountUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List all savings accounts",
        description="Retrieve a paginated list of all savings accounts.",
        tags=["Accounts"],
    ),
    create=extend_schema(
        summary="Create a new savings account",
        description="Create a new savings account for a customer.",
        tags=["Accounts"],
    ),
    retrieve=extend_schema(
        summary="Get account details",
        description="Retrieve detailed information about a specific account.",
        tags=["Accounts"],
    ),
    update=extend_schema(
        summary="Update account information",
        description="Update account information.",
        tags=["Accounts"],
    ),
    destroy=extend_schema(
        summary="Delete account",
        description="Delete an account from the system.",
        tags=["Accounts"],
    ),
)
class SavingsAccountViewSet(viewsets.ModelViewSet):
    """ViewSet for managing savings accounts."""

    queryset = SavingsAccount.objects.all().select_related("customer")
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "currency", "customer"]
    search_fields = ["account_number", "customer__first_names", "customer__last_names"]
    ordering_fields = ["account_number", "current_balance", "opening_date"]
    ordering = ["-opening_date"]

    def get_serializer_class(self):
        if self.action == "create":
            return SavingsAccountCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return SavingsAccountUpdateSerializer
        elif self.action == "list":
            return SavingsAccountListSerializer
        elif self.action == "balance":
            return SavingsAccountBalanceSerializer
        elif self.action == "change_status":
            return SavingsAccountStatusSerializer
        elif self.action == "summary":
            return SavingsAccountSummarySerializer
        return SavingsAccountSerializer

    @extend_schema(
        summary="Get account balance",
        description="Get current balance information for an account.",
        tags=["Accounts"],
    )
    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        account = self.get_object()
        serializer = SavingsAccountBalanceSerializer(account)
        return Response(serializer.data)

    @extend_schema(
        summary="Change account status",
        description="Change the status of an account (ACTIVE, BLOCKED, CLOSED).",
        request=SavingsAccountStatusSerializer,
        tags=["Accounts"],
    )
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        account = self.get_object()
        serializer = self.get_serializer(
            data=request.data, context={"account": account}
        )
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        account.status = new_status
        account.save(update_fields=["status"])

        return Response({"message": f"Account status changed to {new_status}"})

    @extend_schema(
        summary="Get account summary",
        description="Get account summary with transaction statistics.",
        tags=["Accounts"],
    )
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        account = self.get_object()
        serializer = SavingsAccountSummarySerializer(account)
        return Response(serializer.data)
