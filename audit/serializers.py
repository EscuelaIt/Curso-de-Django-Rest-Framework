from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from .models import Audit


class AuditSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Audit model.
    Read-only serializer for audit trail viewing.
    """
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    operation_display = serializers.CharField(read_only=True, help_text="Human-readable operation name")
    has_data_changes = serializers.BooleanField(read_only=True, help_text="Whether data changes are recorded")
    changed_fields = serializers.ListField(read_only=True, help_text="List of fields that were changed")
    changes_summary = serializers.CharField(source='get_changes_summary', read_only=True)
    
    class Meta:
        model = Audit
        fields = [
            'id', 'affected_table', 'record_id', 'operation', 'operation_display',
            'previous_data', 'new_data', 'user', 'user_name', 'user_full_name',
            'operation_date', 'ip_address', 'user_agent', 'context',
            'has_data_changes', 'changed_fields', 'changes_summary'
        ]
        read_only_fields = '__all__'  # Audit records are read-only


class AuditListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for audit listings.
    Optimized for list views with essential information.
    """
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    changes_summary = serializers.CharField(source='get_changes_summary', read_only=True)
    
    class Meta:
        model = Audit
        fields = [
            'id', 'affected_table', 'record_id', 'operation', 'operation_display',
            'user_name', 'operation_date', 'context', 'changes_summary'
        ]


class AuditDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for individual audit records.
    Includes complete change information and metadata.
    """
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    operation_display = serializers.CharField(source='get_operation_display', read_only=True)
    has_data_changes = serializers.BooleanField(read_only=True)
    changed_fields = serializers.ListField(read_only=True)
    changes_summary = serializers.CharField(source='get_changes_summary', read_only=True)
    field_changes = serializers.SerializerMethodField(help_text="Detailed field-by-field changes")
    
    class Meta:
        model = Audit
        fields = [
            'id', 'affected_table', 'record_id', 'operation', 'operation_display',
            'previous_data', 'new_data', 'user', 'user_name', 'user_full_name', 'user_email',
            'operation_date', 'ip_address', 'user_agent', 'context',
            'has_data_changes', 'changed_fields', 'changes_summary', 'field_changes'
        ]
    
    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_field_changes(self, obj):
        """Get detailed field-by-field changes"""
        if not (obj.previous_data and obj.new_data):
            return {}
        
        changes = {}
        for field in obj.changed_fields:
            old_value, new_value = obj.get_field_change(field)
            changes[field] = {
                'old_value': old_value,
                'new_value': new_value
            }
        return changes


class AuditFilterSerializer(serializers.Serializer):
    """
    Serializer for audit filtering parameters.
    Contract-first approach for search and filter endpoints.
    """
    
    affected_table = serializers.CharField(
        required=False,
        help_text="Filter by affected database table"
    )
    record_id = serializers.IntegerField(
        required=False,
        help_text="Filter by specific record ID"
    )
    operation = serializers.ChoiceField(
        choices=Audit.OPERATION_CHOICES,
        required=False,
        help_text="Filter by operation type"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filter by user who performed the operation"
    )
    date_from = serializers.DateTimeField(
        required=False,
        help_text="Filter operations from this date (inclusive)"
    )
    date_to = serializers.DateTimeField(
        required=False,
        help_text="Filter operations until this date (inclusive)"
    )
    context = serializers.CharField(
        required=False,
        help_text="Filter by operation context"
    )
    ip_address = serializers.IPAddressField(
        required=False,
        help_text="Filter by IP address"
    )
    
    def validate(self, attrs):
        """Validate date range"""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from cannot be later than date_to")
        
        return attrs


class AuditSummarySerializer(serializers.Serializer):
    """
    Serializer for audit statistics and summaries.
    Contract-first for dashboard and reporting endpoints.
    """
    
    total_operations = serializers.IntegerField(read_only=True, help_text="Total number of operations")
    operations_by_type = serializers.DictField(read_only=True, help_text="Count of operations by type")
    operations_by_table = serializers.DictField(read_only=True, help_text="Count of operations by table")
    operations_by_user = serializers.DictField(read_only=True, help_text="Count of operations by user")
    recent_activity = serializers.ListField(read_only=True, help_text="Recent audit entries")
    date_range = serializers.DictField(read_only=True, help_text="Date range of the summary")


class AuditTableSummarySerializer(serializers.Serializer):
    """
    Serializer for table-specific audit summaries.
    Shows audit activity for a specific database table.
    """
    
    table_name = serializers.CharField(read_only=True, help_text="Database table name")
    total_operations = serializers.IntegerField(read_only=True, help_text="Total operations on this table")
    operations_by_type = serializers.DictField(read_only=True, help_text="Operations breakdown by type")
    most_active_users = serializers.ListField(read_only=True, help_text="Users with most operations on this table")
    recent_changes = serializers.ListField(read_only=True, help_text="Recent changes to this table")
    affected_records = serializers.IntegerField(read_only=True, help_text="Number of unique records affected")


class AuditUserActivitySerializer(serializers.Serializer):
    """
    Serializer for user-specific audit activity.
    Shows what a specific user has been doing.
    """
    
    user_id = serializers.IntegerField(read_only=True)
    user_name = serializers.CharField(read_only=True)
    user_full_name = serializers.CharField(read_only=True)
    total_operations = serializers.IntegerField(read_only=True, help_text="Total operations by this user")
    operations_by_type = serializers.DictField(read_only=True, help_text="Operations breakdown by type")
    operations_by_table = serializers.DictField(read_only=True, help_text="Operations breakdown by table")
    recent_activity = serializers.ListField(read_only=True, help_text="Recent operations by this user")
    first_activity = serializers.DateTimeField(read_only=True, help_text="Date of first recorded activity")
    last_activity = serializers.DateTimeField(read_only=True, help_text="Date of most recent activity")


class AuditRecordHistorySerializer(serializers.Serializer):
    """
    Serializer for tracking changes to a specific record.
    Shows complete history of changes to a database record.
    """
    
    table_name = serializers.CharField(read_only=True)
    record_id = serializers.IntegerField(read_only=True)
    total_changes = serializers.IntegerField(read_only=True, help_text="Total number of changes")
    creation_date = serializers.DateTimeField(read_only=True, help_text="When the record was created")
    last_modified = serializers.DateTimeField(read_only=True, help_text="When the record was last modified")
    change_history = serializers.ListField(read_only=True, help_text="Chronological list of all changes")
    users_involved = serializers.ListField(read_only=True, help_text="Users who have modified this record")
    current_status = serializers.CharField(read_only=True, help_text="Current status of the record")


class AuditExportSerializer(serializers.Serializer):
    """
    Serializer for audit export requests.
    Contract-first for generating audit reports.
    """
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
    ]
    
    format = serializers.ChoiceField(
        choices=FORMAT_CHOICES,
        default='json',
        help_text="Export format"
    )
    date_from = serializers.DateTimeField(
        required=True,
        help_text="Start date for export (required)"
    )
    date_to = serializers.DateTimeField(
        required=True,
        help_text="End date for export (required)"
    )
    affected_table = serializers.CharField(
        required=False,
        help_text="Filter by specific table (optional)"
    )
    operation = serializers.ChoiceField(
        choices=Audit.OPERATION_CHOICES,
        required=False,
        help_text="Filter by operation type (optional)"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filter by specific user (optional)"
    )
    include_data_changes = serializers.BooleanField(
        default=True,
        help_text="Include detailed data changes in export"
    )
    
    def validate(self, attrs):
        """Validate export parameters"""
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        
        if date_from > date_to:
            raise serializers.ValidationError("date_from cannot be later than date_to")
        
        # Limit export range to prevent performance issues
        from datetime import timedelta
        max_range = timedelta(days=365)  # 1 year maximum
        if (date_to - date_from) > max_range:
            raise serializers.ValidationError("Export range cannot exceed 365 days")
        
        return attrs
