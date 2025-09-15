from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from datetime import date
from .models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Customer model.
    Includes computed fields and validation for banking requirements.
    """
    
    full_name = serializers.CharField(read_only=True, help_text="Customer's full name")
    age = serializers.IntegerField(read_only=True, help_text="Customer's current age")
    full_document = serializers.CharField(read_only=True, help_text="Document type and number")
    accounts_count = serializers.SerializerMethodField(help_text="Number of savings accounts")
    
    class Meta:
        model = Customer
        fields = [
            'id', 'document_type', 'document_number', 'first_names', 'last_names',
            'email', 'phone', 'birth_date', 'address', 'status', 'version',
            'created_at', 'full_name', 'age', 'full_document',
            'accounts_count'
        ]
        read_only_fields = [
            'id', 'created_at', 'version', 'full_name', 
            'age', 'full_document', 'accounts_count'
        ]
        extra_kwargs = {
            'document_type': {'required': True},
            'document_number': {'required': True},
            'first_names': {'required': True},
            'last_names': {'required': True},
            'email': {'required': True},
            'phone': {'required': True},
            'birth_date': {'required': True},
            'address': {'required': True},
        }
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_accounts_count(self, obj):
        """Get number of savings accounts for this customer"""
        return obj.savings_accounts.count()
    
    def validate_birth_date(self, value):
        """Validate minimum age requirement (18 years)"""
        if value:
            age = (date.today() - value).days // 365
            if age < 18:
                raise serializers.ValidationError("Customer must be at least 18 years old")
        return value
    
    
    def validate(self, attrs):
        """Custom validation for document format"""
        document_type = attrs.get('document_type')
        document_number = attrs.get('document_number')
        
        if document_type and document_number:
            if document_type == 'DNI' and len(document_number) != 8:
                raise serializers.ValidationError("DNI must have exactly 8 digits")
            elif document_type == 'CE' and len(document_number) != 9:
                raise serializers.ValidationError("Carnet de Extranjería must have exactly 9 characters")
        
        return attrs


class CustomerCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new customers.
    Contract-first approach with all required validations.
    """
    
    class Meta:
        model = Customer
        fields = [
            'document_type', 'document_number', 'first_names', 'last_names',
            'email', 'phone', 'birth_date', 'address'
        ]
        extra_kwargs = {
            'document_type': {'required': True, 'help_text': 'Type of identity document'},
            'document_number': {'required': True, 'help_text': 'Document number (8 digits for DNI, 9 for CE)'},
            'first_names': {'required': True, 'help_text': "Customer's first names"},
            'last_names': {'required': True, 'help_text': "Customer's last names"},
            'email': {'required': True, 'help_text': 'Unique email address'},
            'phone': {'required': True, 'help_text': 'Contact phone number'},
            'birth_date': {'required': True, 'help_text': 'Date of birth (must be 18+ years old)'},
            'address': {'required': True, 'help_text': 'Complete address'},
        }
    
    def validate_birth_date(self, value):
        """Validate minimum age requirement"""
        if value:
            age = (date.today() - value).days // 365
            if age < 18:
                raise serializers.ValidationError("Customer must be at least 18 years old")
        return value
    
    def validate_email(self, value):
        """Validate email domain restriction for new customers"""
        if not value:
            raise serializers.ValidationError("Email is required")
        
        # Business rule: only escuela.it domain allowed
        if not value.lower().endswith('@escuela.it'):
            raise serializers.ValidationError("Only @escuela.it email addresses are allowed")
        
        # Check uniqueness
        if Customer.objects.filter(email=value).exists():
            raise serializers.ValidationError("A customer with this email already exists")
        
        return value.lower()  # Normalize to lowercase
    
    def validate(self, attrs):
        """Document format validation"""
        document_type = attrs.get('document_type')
        document_number = attrs.get('document_number')
        
        if document_type and document_number:
            if document_type == 'DNI' and len(document_number) != 8:
                raise serializers.ValidationError("DNI must have exactly 8 digits")
            elif document_type == 'CE' and len(document_number) != 9:
                raise serializers.ValidationError("Carnet de Extranjería must have exactly 9 characters")
        
        return attrs


class CustomerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating customer information.
    Excludes document fields that shouldn't be changed.
    """
    
    class Meta:
        model = Customer
        fields = [
            'first_names', 'last_names', 'email', 'phone', 'address'
        ]
        extra_kwargs = {
            'email': {'required': False},
        }
    
    def validate_email(self, value):
        """Validate email domain restriction for updates"""
        if value and not value.lower().endswith('@escuela.it'):
            raise serializers.ValidationError("Only @escuela.it email addresses are allowed")
        return value.lower() if value else value


class CustomerListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for customer listings.
    Optimized for list views with essential information.
    """
    
    full_name = serializers.CharField(read_only=True)
    full_document = serializers.CharField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    accounts_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Customer
        fields = [
            'id', 'full_name', 'full_document', 'email', 'phone',
            'age', 'status', 'status_display', 'accounts_count', 'created_at'
        ]
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_accounts_count(self, obj):
        """Get number of savings accounts"""
        return obj.savings_accounts.count()


class CustomerStatusSerializer(serializers.Serializer):
    """
    Serializer for customer status change operations.
    Contract-first for status management endpoints.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
    ]
    
    status = serializers.ChoiceField(
        choices=STATUS_CHOICES,
        help_text="New status for the customer"
    )
    reason = serializers.CharField(
        max_length=200,
        required=False,
        help_text="Optional reason for status change"
    )


class CustomerSummarySerializer(serializers.ModelSerializer):
    """
    Summary serializer with financial information.
    Includes account balances and transaction counts.
    """
    
    full_name = serializers.CharField(read_only=True)
    accounts_count = serializers.SerializerMethodField()
    total_balance = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    
    class Meta:
        model = Customer
        fields = [
            'id', 'full_name', 'email', 'status', 'accounts_count',
            'total_balance', 'recent_transactions', 'created_at'
        ]
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_accounts_count(self, obj):
        """Number of active savings accounts"""
        return obj.savings_accounts.filter(status='ACTIVE').count()
    
    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_total_balance(self, obj):
        """Total balance across all active accounts"""
        from django.db.models import Sum
        total = obj.savings_accounts.filter(status='ACTIVE').aggregate(
            total=Sum('current_balance')
        )['total']
        return total or 0
    
    @extend_schema_field(OpenApiTypes.INT)
    def get_recent_transactions(self, obj):
        """Count of transactions in last 30 days"""
        from django.utils import timezone
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Count transactions from all customer accounts
        from transactions.models import Transaction
        return Transaction.objects.filter(
            source_account__customer=obj,
            transaction_date__gte=thirty_days_ago
        ).count()
