from decimal import Decimal

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Transaction model.
    Includes account and user information with computed fields.
    """

    source_account_number = serializers.CharField(
        source="source_account.account_number", read_only=True
    )
    destination_account_number = serializers.CharField(
        source="destination_account.account_number", read_only=True
    )
    user_name = serializers.CharField(source="user.full_name", read_only=True)
    amount_display = serializers.CharField(
        read_only=True, help_text="Formatted amount with currency"
    )
    is_pending = serializers.BooleanField(
        read_only=True, help_text="Whether transaction is pending"
    )
    is_processed = serializers.BooleanField(
        read_only=True, help_text="Whether transaction is processed"
    )
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference_number",
            "transaction_type",
            "transaction_type_display",
            "source_account",
            "source_account_number",
            "destination_account",
            "destination_account_number",
            "amount",
            "currency",
            "amount_display",
            "description",
            "previous_balance",
            "new_balance",
            "transaction_date",
            "processing_date",
            "status",
            "status_display",
            "user",
            "user_name",
            "ip_address",
            "user_agent",
            "is_pending",
            "is_processed",
        ]
        read_only_fields = [
            "id",
            "reference_number",
            "transaction_date",
            "processing_date",
            "source_account_number",
            "destination_account_number",
            "user_name",
            "amount_display",
            "is_pending",
            "is_processed",
            "transaction_type_display",
            "status_display",
            "previous_balance",
            "new_balance",
        ]


class TransactionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new transactions.
    Contract-first approach with comprehensive validation.
    """

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "source_account",
            "destination_account",
            "amount",
            "currency",
            "description",
        ]
        extra_kwargs = {
            "transaction_type": {
                "required": True,
                "help_text": "Type of transaction (DEPOSIT, WITHDRAWAL, TRANSFER_OUT, TRANSFER_IN)",
            },
            "source_account": {
                "required": True,
                "help_text": "Source account for the transaction",
            },
            "amount": {
                "required": True,
                "help_text": "Transaction amount (must be positive)",
            },
            "currency": {
                "required": True,
                "help_text": "Transaction currency (must match account currency)",
            },
            "description": {
                "required": False,
                "help_text": "Optional transaction description",
            },
        }

    def validate_amount(self, value):
        """Validate transaction amount"""
        if value <= 0:
            raise serializers.ValidationError("Transaction amount must be positive")
        return value

    def validate(self, attrs):
        """Comprehensive transaction validation"""
        transaction_type = attrs.get("transaction_type")
        source_account = attrs.get("source_account")
        destination_account = attrs.get("destination_account")
        amount = attrs.get("amount")
        currency = attrs.get("currency")

        # Validate transaction type requirements
        if (
            transaction_type in ["TRANSFER_OUT", "TRANSFER_IN"]
            and not destination_account
        ):
            raise serializers.ValidationError(
                "Transfer transactions require destination account"
            )

        if transaction_type in ["DEPOSIT", "WITHDRAWAL"] and destination_account:
            raise serializers.ValidationError(
                "Deposit and withdrawal transactions should not have destination account"
            )

        # Validate accounts are different for transfers
        if destination_account and source_account == destination_account:
            raise serializers.ValidationError(
                "Source and destination accounts cannot be the same"
            )

        # Validate currency matches account currency
        if source_account and currency != source_account.currency:
            raise serializers.ValidationError(
                "Transaction currency must match source account currency"
            )

        if destination_account and currency != destination_account.currency:
            raise serializers.ValidationError(
                "Transaction currency must match destination account currency"
            )

        # Validate account status
        if source_account and source_account.status != "ACTIVE":
            raise serializers.ValidationError("Source account must be active")

        if destination_account and destination_account.status != "ACTIVE":
            raise serializers.ValidationError("Destination account must be active")

        # Validate sufficient balance for withdrawals and transfers
        if transaction_type in ["WITHDRAWAL", "TRANSFER_OUT"]:
            if source_account and amount > source_account.available_balance:
                raise serializers.ValidationError("Insufficient available balance")

        return attrs

    def create(self, validated_data):
        """Create transaction with audit information"""
        request = self.context.get("request")
        if request:
            validated_data["user"] = request.user
            validated_data["ip_address"] = self.get_client_ip(request)
            validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

        # Set balance information
        source_account = validated_data["source_account"]
        validated_data["previous_balance"] = source_account.current_balance

        # Calculate new balance based on transaction type
        amount = validated_data["amount"]
        transaction_type = validated_data["transaction_type"]

        if transaction_type in ["DEPOSIT", "TRANSFER_IN"]:
            validated_data["new_balance"] = source_account.current_balance + amount
        elif transaction_type in ["WITHDRAWAL", "TRANSFER_OUT"]:
            validated_data["new_balance"] = source_account.current_balance - amount

        return super().create(validated_data)

    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for transaction listings.
    Optimized for list views with essential information.
    """

    source_account_number = serializers.CharField(
        source="source_account.account_number", read_only=True
    )
    destination_account_number = serializers.CharField(
        source="destination_account.account_number", read_only=True
    )
    amount_display = serializers.CharField(read_only=True)
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "reference_number",
            "transaction_type",
            "transaction_type_display",
            "source_account_number",
            "destination_account_number",
            "amount_display",
            "status",
            "status_display",
            "transaction_date",
            "user_name",
        ]


class TransactionStatusSerializer(serializers.Serializer):
    """
    Serializer for transaction status updates.
    Contract-first for transaction processing endpoints.
    """

    STATUS_CHOICES = [
        ("PROCESSED", "Processed"),
        ("REJECTED", "Rejected"),
        ("REVERSED", "Reversed"),
    ]

    status = serializers.ChoiceField(
        choices=STATUS_CHOICES, help_text="New status for the transaction"
    )
    reason = serializers.CharField(
        max_length=200, required=False, help_text="Optional reason for status change"
    )

    def validate_status(self, value):
        """Validate status transition rules"""
        transaction = self.context.get("transaction")
        if transaction:
            current_status = transaction.status

            # Define allowed transitions
            allowed_transitions = {
                "PENDING": ["PROCESSED", "REJECTED"],
                "PROCESSED": ["REVERSED"],
                "REJECTED": [],
                "REVERSED": [],
            }

            if value not in allowed_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )

        return value


class DepositSerializer(serializers.Serializer):
    """
    Specialized serializer for deposit operations.
    Contract-first approach for specific transaction type.
    """

    account_number = serializers.CharField(
        max_length=20, help_text="Account number to deposit to"
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Deposit amount (must be positive)",
    )
    description = serializers.CharField(
        max_length=500, required=False, help_text="Optional deposit description"
    )

    def validate_account_number(self, value):
        """Validate account exists and is active"""
        from accounts.models import SavingsAccount

        try:
            account = SavingsAccount.objects.get(account_number=value)
            if account.status != "ACTIVE":
                raise serializers.ValidationError("Account must be active")
            return value
        except SavingsAccount.DoesNotExist:
            raise serializers.ValidationError("Account not found")


class WithdrawalSerializer(serializers.Serializer):
    """
    Specialized serializer for withdrawal operations.
    Contract-first with balance validation.
    """

    account_number = serializers.CharField(
        max_length=20, help_text="Account number to withdraw from"
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Withdrawal amount (must be positive)",
    )
    description = serializers.CharField(
        max_length=500, required=False, help_text="Optional withdrawal description"
    )

    def validate(self, attrs):
        """Validate withdrawal constraints"""
        from accounts.models import SavingsAccount

        account_number = attrs.get("account_number")
        amount = attrs.get("amount")

        try:
            account = SavingsAccount.objects.get(account_number=account_number)
            if account.status != "ACTIVE":
                raise serializers.ValidationError("Account must be active")

            if amount > account.available_balance:
                raise serializers.ValidationError("Insufficient available balance")

        except SavingsAccount.DoesNotExist:
            raise serializers.ValidationError("Account not found")

        return attrs


class TransferSerializer(serializers.Serializer):
    """
    Specialized serializer for transfer operations.
    Contract-first with comprehensive validation.
    """

    source_account_number = serializers.CharField(
        max_length=20, help_text="Source account number"
    )
    destination_account_number = serializers.CharField(
        max_length=20, help_text="Destination account number"
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Transfer amount (must be positive)",
    )
    description = serializers.CharField(
        max_length=500, required=False, help_text="Optional transfer description"
    )

    def validate(self, attrs):
        """Validate transfer constraints"""
        from accounts.models import SavingsAccount

        source_number = attrs.get("source_account_number")
        dest_number = attrs.get("destination_account_number")
        amount = attrs.get("amount")

        # Validate accounts are different
        if source_number == dest_number:
            raise serializers.ValidationError(
                "Source and destination accounts cannot be the same"
            )

        # Validate source account
        try:
            source_account = SavingsAccount.objects.get(account_number=source_number)
            if source_account.status != "ACTIVE":
                raise serializers.ValidationError("Source account must be active")

            if amount > source_account.available_balance:
                raise serializers.ValidationError("Insufficient available balance")

        except SavingsAccount.DoesNotExist:
            raise serializers.ValidationError("Source account not found")

        # Validate destination account
        try:
            dest_account = SavingsAccount.objects.get(account_number=dest_number)
            if dest_account.status != "ACTIVE":
                raise serializers.ValidationError("Destination account must be active")

            # Validate same currency
            if source_account.currency != dest_account.currency:
                raise serializers.ValidationError(
                    "Accounts must have the same currency"
                )

        except SavingsAccount.DoesNotExist:
            raise serializers.ValidationError("Destination account not found")

        return attrs
