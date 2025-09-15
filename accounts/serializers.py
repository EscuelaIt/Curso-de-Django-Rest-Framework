from decimal import Decimal

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import SavingsAccount


class SavingsAccountSerializer(serializers.ModelSerializer):
    """
    Complete serializer for SavingsAccount model.
    Includes customer information and computed fields.
    """

    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    customer_document = serializers.CharField(
        source="customer.full_document", read_only=True
    )
    balance_display = serializers.CharField(
        read_only=True, help_text="Formatted balance with currency"
    )
    is_active = serializers.BooleanField(
        read_only=True, help_text="Whether account is active"
    )
    is_blocked = serializers.BooleanField(
        read_only=True, help_text="Whether account is blocked"
    )
    transactions_count = serializers.SerializerMethodField(
        help_text="Total number of transactions"
    )

    class Meta:
        model = SavingsAccount
        fields = [
            "id",
            "account_number",
            "customer",
            "customer_name",
            "customer_document",
            "current_balance",
            "available_balance",
            "currency",
            "balance_display",
            "opening_date",
            "last_movement_date",
            "status",
            "version",
            "is_active",
            "is_blocked",
            "transactions_count",
        ]
        read_only_fields = [
            "id",
            "account_number",
            "opening_date",
            "last_movement_date",
            "version",
            "customer_name",
            "customer_document",
            "balance_display",
            "is_active",
            "is_blocked",
            "transactions_count",
        ]
        extra_kwargs = {
            "customer": {"required": True, "help_text": "Account owner customer ID"},
            "currency": {
                "required": True,
                "help_text": "Account currency (PEN, USD, EUR)",
            },
        }

    @extend_schema_field(OpenApiTypes.INT)
    def get_transactions_count(self, obj):
        """Get total number of transactions for this account"""
        return obj.outgoing_transactions.count() + obj.incoming_transactions.count()

    def validate(self, attrs):
        """Custom validation for balance constraints"""
        current_balance = attrs.get(
            "current_balance",
            getattr(self.instance, "current_balance", Decimal("0.00")),
        )
        available_balance = attrs.get(
            "available_balance",
            getattr(self.instance, "available_balance", Decimal("0.00")),
        )

        if available_balance > current_balance:
            raise serializers.ValidationError(
                "Available balance cannot be greater than current balance"
            )

        return attrs


class SavingsAccountCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new savings accounts.
    Contract-first approach with validation rules.
    """

    initial_deposit = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
        help_text="Optional initial deposit amount",
    )

    class Meta:
        model = SavingsAccount
        fields = ["customer", "currency", "initial_deposit"]
        extra_kwargs = {
            "customer": {
                "required": True,
                "help_text": "Customer who will own the account",
            },
            "currency": {
                "required": True,
                "help_text": "Account currency (PEN, USD, EUR)",
            },
        }

    def create(self, validated_data):
        """Create account with optional initial deposit"""
        initial_deposit = validated_data.pop("initial_deposit", Decimal("0.00"))

        account = SavingsAccount.objects.create(**validated_data)

        # Set initial balances if deposit provided
        if initial_deposit > 0:
            account.current_balance = initial_deposit
            account.available_balance = initial_deposit
            account.save(update_fields=["current_balance", "available_balance"])

        return account


class SavingsAccountUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating account information.
    Limited fields that can be safely updated.
    """

    class Meta:
        model = SavingsAccount
        fields = ["status"]
        extra_kwargs = {
            "status": {"help_text": "Account status (ACTIVE, BLOCKED, CLOSED)"},
        }


class SavingsAccountListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for account listings.
    Optimized for list views with essential information.
    """

    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    balance_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    days_since_opening = serializers.SerializerMethodField()

    class Meta:
        model = SavingsAccount
        fields = [
            "id",
            "account_number",
            "customer_name",
            "current_balance",
            "currency",
            "balance_display",
            "status",
            "status_display",
            "opening_date",
            "last_movement_date",
            "days_since_opening",
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_days_since_opening(self, obj):
        """Calculate days since account opening"""
        from django.utils import timezone

        delta = timezone.now() - obj.opening_date
        return delta.days


class SavingsAccountBalanceSerializer(serializers.ModelSerializer):
    """
    Serializer focused on balance information.
    Used for balance inquiry endpoints.
    """

    balance_display = serializers.CharField(read_only=True)

    class Meta:
        model = SavingsAccount
        fields = [
            "account_number",
            "current_balance",
            "available_balance",
            "currency",
            "balance_display",
            "last_movement_date",
        ]


class SavingsAccountStatusSerializer(serializers.Serializer):
    """
    Serializer for account status change operations.
    Contract-first for status management endpoints.
    """

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("BLOCKED", "Blocked"),
        ("CLOSED", "Closed"),
    ]

    status = serializers.ChoiceField(
        choices=STATUS_CHOICES, help_text="New status for the account"
    )
    reason = serializers.CharField(
        max_length=200, required=False, help_text="Optional reason for status change"
    )

    def validate_status(self, value):
        """Validate status transition rules"""
        account = self.context.get("account")
        if account:
            current_status = account.status

            # Define allowed transitions
            allowed_transitions = {
                "ACTIVE": ["BLOCKED", "CLOSED"],
                "BLOCKED": ["ACTIVE", "CLOSED"],
                "CLOSED": [],  # Closed accounts cannot change status
            }

            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )

        return value


class SavingsAccountSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer with transaction statistics.
    Includes recent activity and balance history.
    """

    customer_name = serializers.CharField(source="customer.full_name", read_only=True)
    balance_display = serializers.CharField(read_only=True)
    total_transactions = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    average_monthly_balance = serializers.SerializerMethodField()

    class Meta:
        model = SavingsAccount
        fields = [
            "id",
            "account_number",
            "customer_name",
            "current_balance",
            "available_balance",
            "currency",
            "balance_display",
            "status",
            "opening_date",
            "last_movement_date",
            "total_transactions",
            "recent_transactions",
            "average_monthly_balance",
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_total_transactions(self, obj):
        """Total number of transactions"""
        return obj.outgoing_transactions.count() + obj.incoming_transactions.count()

    @extend_schema_field(OpenApiTypes.INT)
    def get_recent_transactions(self, obj):
        """Transactions in last 30 days"""
        from datetime import timedelta

        from django.utils import timezone

        thirty_days_ago = timezone.now() - timedelta(days=30)

        return (
            obj.outgoing_transactions.filter(
                transaction_date__gte=thirty_days_ago
            ).count()
            + obj.incoming_transactions.filter(
                transaction_date__gte=thirty_days_ago
            ).count()
        )

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_average_monthly_balance(self, obj):
        """Calculate average balance over account lifetime"""
        from datetime import timedelta

        from django.utils import timezone

        # Simple calculation based on current balance and account age
        # In a real system, you'd track balance history
        days_open = (timezone.now() - obj.opening_date).days
        if days_open < 30:
            return obj.current_balance

        # Simplified average - in production you'd use actual balance history
        return obj.current_balance * Decimal("0.8")  # Assume 80% of current as average
