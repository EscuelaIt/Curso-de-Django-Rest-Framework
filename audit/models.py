import json

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Audit(models.Model):
    """
    Audit model for tracking all database operations.
    Stores complete audit trail for compliance and security.
    """

    OPERATION_CHOICES = [
        ("INSERT", "Inserción"),
        ("UPDATE", "Actualización"),
        ("DELETE", "Eliminación"),
    ]

    # Table and record identification
    affected_table = models.CharField(
        max_length=50, help_text="Name of the affected database table"
    )
    record_id = models.BigIntegerField(help_text="ID of the affected record")
    operation = models.CharField(
        max_length=10,
        choices=OPERATION_CHOICES,
        help_text="Type of database operation performed",
    )

    # Data changes
    previous_data = models.JSONField(
        null=True,
        blank=True,
        help_text="Previous data before the operation (JSON format)",
    )
    new_data = models.JSONField(
        null=True, blank=True, help_text="New data after the operation (JSON format)"
    )

    # Audit metadata
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="audit_logs",
        help_text="User who performed the operation",
    )
    operation_date = models.DateTimeField(
        auto_now_add=True, help_text="Date and time when the operation was performed"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address from which the operation was performed"
    )
    user_agent = models.CharField(
        max_length=500, blank=True, help_text="User agent information from the request"
    )

    # Additional context
    context = models.CharField(
        max_length=100,
        blank=True,
        help_text="Additional context about the operation (e.g., 'admin_panel', 'api_rest')",
    )

    class Meta:
        db_table = "audit"
        indexes = [
            models.Index(
                fields=["affected_table", "record_id"], name="idx_audit_table_record"
            ),
            models.Index(fields=["user"], name="idx_audit_user"),
            models.Index(fields=["operation_date"], name="idx_audit_date"),
            models.Index(fields=["operation"], name="idx_audit_operation"),
            models.Index(fields=["affected_table"], name="idx_audit_table"),
        ]
        ordering = ["-operation_date"]
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditorías"

    def __str__(self):
        return f"{self.affected_table}#{self.record_id} - {self.operation} by {self.user.username}"

    @property
    def operation_display(self):
        """Returns the display name of the operation"""
        return self.get_operation_display()

    @property
    def has_data_changes(self):
        """Returns True if there are data changes recorded"""
        return bool(self.previous_data or self.new_data)

    @property
    def changed_fields(self):
        """Returns a list of fields that were changed"""
        if not (self.previous_data and self.new_data):
            return []

        changed = []
        for field, new_value in self.new_data.items():
            old_value = self.previous_data.get(field)
            if old_value != new_value:
                changed.append(field)
        return changed

    def get_field_change(self, field_name):
        """Returns the old and new value for a specific field"""
        if not (self.previous_data and self.new_data):
            return None, None

        old_value = self.previous_data.get(field_name)
        new_value = self.new_data.get(field_name)
        return old_value, new_value

    def get_changes_summary(self):
        """Returns a human-readable summary of changes"""
        if self.operation == "INSERT":
            return f"Nuevo registro creado en {self.affected_table}"
        elif self.operation == "DELETE":
            return f"Registro eliminado de {self.affected_table}"
        elif self.operation == "UPDATE":
            changed = self.changed_fields
            if changed:
                return (
                    f"Campos modificados en {self.affected_table}: {', '.join(changed)}"
                )
            else:
                return f"Actualización sin cambios en {self.affected_table}"
        return f"Operación {self.operation} en {self.affected_table}"

    @classmethod
    def log_operation(
        cls,
        table_name,
        record_id,
        operation,
        user,
        ip_address,
        previous_data=None,
        new_data=None,
        user_agent="",
        context="",
    ):
        """
        Utility method to create audit log entries.

        Args:
            table_name: Name of the affected table
            record_id: ID of the affected record
            operation: Type of operation ('INSERT', 'UPDATE', 'DELETE')
            user: User who performed the operation
            ip_address: IP address of the request
            previous_data: Data before the operation (dict)
            new_data: Data after the operation (dict)
            user_agent: User agent string
            context: Additional context information
        """
        return cls.objects.create(
            affected_table=table_name,
            record_id=record_id,
            operation=operation,
            user=user,
            ip_address=ip_address,
            previous_data=previous_data,
            new_data=new_data,
            user_agent=user_agent,
            context=context,
        )

    @classmethod
    def log_insert(
        cls,
        table_name,
        record_id,
        user,
        ip_address,
        new_data,
        user_agent="",
        context="",
    ):
        """Convenience method for logging INSERT operations"""
        return cls.log_operation(
            table_name=table_name,
            record_id=record_id,
            operation="INSERT",
            user=user,
            ip_address=ip_address,
            new_data=new_data,
            user_agent=user_agent,
            context=context,
        )

    @classmethod
    def log_update(
        cls,
        table_name,
        record_id,
        user,
        ip_address,
        previous_data,
        new_data,
        user_agent="",
        context="",
    ):
        """Convenience method for logging UPDATE operations"""
        return cls.log_operation(
            table_name=table_name,
            record_id=record_id,
            operation="UPDATE",
            user=user,
            ip_address=ip_address,
            previous_data=previous_data,
            new_data=new_data,
            user_agent=user_agent,
            context=context,
        )

    @classmethod
    def log_delete(
        cls,
        table_name,
        record_id,
        user,
        ip_address,
        previous_data,
        user_agent="",
        context="",
    ):
        """Convenience method for logging DELETE operations"""
        return cls.log_operation(
            table_name=table_name,
            record_id=record_id,
            operation="DELETE",
            user=user,
            ip_address=ip_address,
            previous_data=previous_data,
            user_agent=user_agent,
            context=context,
        )
