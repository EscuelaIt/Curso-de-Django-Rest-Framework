from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from .models import Customer
from .serializers import (
    CustomerCreateSerializer,
    CustomerListSerializer,
    CustomerSerializer,
    CustomerStatusSerializer,
    CustomerSummarySerializer,
    CustomerUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List all customers",
        description="Retrieve a paginated list of all customers.",
        tags=["Customers"],
    ),
    create=extend_schema(
        summary="Create a new customer",
        description="Create a new customer in the banking system.",
        tags=["Customers"],
    ),
    retrieve=extend_schema(
        summary="Get customer details",
        description="Retrieve detailed information about a specific customer.",
        tags=["Customers"],
    ),
    update=extend_schema(
        summary="Update customer information",
        description="Update customer information.",
        tags=["Customers"],
    ),
    destroy=extend_schema(
        summary="Delete customer",
        description="Delete a customer from the system.",
        tags=["Customers"],
    ),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """ViewSet for managing bank customers."""

    queryset = Customer.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "document_type"]
    search_fields = ["first_names", "last_names", "email", "document_number"]
    ordering_fields = ["first_names", "last_names", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return CustomerCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return CustomerUpdateSerializer
        elif self.action == "list":
            return CustomerListSerializer
        elif self.action == "change_status":
            return CustomerStatusSerializer
        elif self.action == "summary":
            return CustomerSummarySerializer
        return CustomerSerializer

    @extend_schema(
        summary="Change customer status",
        description="Change the status of a customer (ACTIVE, INACTIVE, SUSPENDED).",
        request=CustomerStatusSerializer,
        tags=["Customers"],
    )
    @action(detail=True, methods=["post"])
    def change_status(self, request, pk=None):
        customer = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data["status"]
        customer.status = new_status
        customer.save(update_fields=["status"])

        return Response({"message": f"Customer status changed to {new_status}"})

    @extend_schema(
        summary="Get customer summary",
        description="Get customer summary with account and transaction information.",
        tags=["Customers"],
    )
    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        customer = self.get_object()
        serializer = CustomerSummarySerializer(customer)
        return Response(serializer.data)
