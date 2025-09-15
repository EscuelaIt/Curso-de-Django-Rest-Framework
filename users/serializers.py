from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with complete banking system information.
    Includes role-based validation and security fields.
    """
    
    full_name = serializers.CharField(read_only=True, help_text="Full name of the user")
    is_blocked = serializers.BooleanField(read_only=True, help_text="Whether the user is temporarily blocked")
    customer_name = serializers.CharField(source='customer.full_name', read_only=True, help_text="Associated customer name")
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_names', 'last_names', 'role',
            'customer', 'customer_name', 'last_access', 'failed_attempts', 
            'blocked_until', 'is_active', 'date_joined', 'updated_at',
            'full_name', 'is_blocked'
        ]
        read_only_fields = [
            'id', 'last_access', 'failed_attempts', 'blocked_until', 
            'date_joined', 'updated_at', 'full_name', 'is_blocked', 'customer_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'first_names': {'required': True},
            'last_names': {'required': True},
            'role': {'required': True},
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users with password validation.
    Contract-first approach with detailed validation rules.
    """
    
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="Password must meet Django's validation requirements",
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Password confirmation - must match password",
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_names', 'last_names', 'role', 'customer'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_names': {'required': True},
            'last_names': {'required': True},
            'role': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation and role-customer relationship"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password confirmation doesn't match")
        
        # Validate role-customer relationship
        if attrs['role'] == 'CUSTOMER' and not attrs.get('customer'):
            raise serializers.ValidationError("Customer role requires an associated customer")
        
        if attrs['role'] in ['OPERATOR', 'ADMIN'] and attrs.get('customer'):
            raise serializers.ValidationError("Operator/Admin roles cannot have associated customer")
        
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information.
    Excludes sensitive fields that require special handling.
    """
    
    class Meta:
        model = User
        fields = [
            'email', 'first_names', 'last_names', 'is_active'
        ]
        extra_kwargs = {
            'email': {'required': False},
        }


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change operations.
    Contract-first with security validations.
    """
    
    old_password = serializers.CharField(
        write_only=True,
        help_text="Current password for verification",
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        help_text="New password must meet validation requirements",
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        help_text="Confirmation of new password",
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Validate password change request"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password confirmation doesn't match")
        return attrs
    
    def validate_old_password(self, value):
        """Validate current password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect")
        return value


class UserListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for user listings.
    Optimized for list views with minimal data.
    """
    
    full_name = serializers.CharField(read_only=True)
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'full_name', 'role', 'role_display',
            'customer_name', 'is_active', 'last_access', 'date_joined'
        ]
