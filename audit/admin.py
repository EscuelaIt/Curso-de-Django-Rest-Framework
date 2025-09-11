from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
import json
from .models import Audit


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    """
    Admin configuration for Audit model.
    Optimized for audit trail visualization and analysis.
    """
    
    # Fields shown in list
    list_display = (
        'operation_date',
        'affected_table_display',
        'record_id',
        'operation_display_colored',
        'user_link',
        'changes_summary_short',
        'context_display'
    )
    
    # Side filters
    list_filter = (
        'operation',
        'affected_table',
        'operation_date',
        'context',
        'user__role',
    )
    
    # Search fields
    search_fields = (
        'affected_table',
        'record_id',
        'user__username',
        'user__first_names',
        'user__last_names',
        'ip_address',
        'context'
    )
    
    # Default ordering
    ordering = ('-operation_date',)
    
    # Fieldset configuration for the form
    fieldsets = (
        ('Información de la Operación', {
            'fields': (
                'affected_table',
                'record_id',
                'operation',
                'operation_date'
            )
        }),
        ('Usuario y Contexto', {
            'fields': (
                'user',
                'context',
                'ip_address',
                'user_agent'
            )
        }),
        ('Datos Anteriores', {
            'fields': ('previous_data_formatted',),
            'classes': ('collapse',)
        }),
        ('Datos Nuevos', {
            'fields': ('new_data_formatted',),
            'classes': ('collapse',)
        }),
        ('Resumen de Cambios', {
            'fields': ('changes_summary_detailed',),
            'classes': ('wide',)
        })
    )
    
    # Read-only fields
    readonly_fields = (
        'affected_table',
        'record_id',
        'operation',
        'operation_date',
        'user',
        'ip_address',
        'user_agent',
        'context',
        'previous_data_formatted',
        'new_data_formatted',
        'changes_summary_detailed'
    )
    
    # Date filters
    date_hierarchy = 'operation_date'
    
    def has_add_permission(self, request):
        """Audit records should not be manually created"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit records should not be modified"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit records should not be deleted"""
        return False
    
    def affected_table_display(self, obj):
        """Shows table name with icon"""
        icons = {
            'customers': '👤',
            'users': '🔐',
            'savings_accounts': '💰',
            'transactions': '💸',
            'audit': '📋'
        }
        icon = icons.get(obj.affected_table, '📄')
        return f"{icon} {obj.affected_table}"
    affected_table_display.short_description = 'Tabla'
    
    def operation_display_colored(self, obj):
        """Shows operation with color coding"""
        colors = {
            'INSERT': 'green',
            'UPDATE': 'orange',
            'DELETE': 'red'
        }
        color = colors.get(obj.operation, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_operation_display()
        )
    operation_display_colored.short_description = 'Operación'
    
    def user_link(self, obj):
        """Shows user with link"""
        if obj.user:
            return format_html(
                '<a href="{}?id={}">{}</a>',
                reverse('admin:users_user_changelist'),
                obj.user.id,
                obj.user.username
            )
        return '-'
    user_link.short_description = 'Usuario'
    
    def changes_summary_short(self, obj):
        """Shows a short summary of changes"""
        summary = obj.get_changes_summary()
        if len(summary) > 50:
            return f"{summary[:47]}..."
        return summary
    changes_summary_short.short_description = 'Resumen'
    
    def context_display(self, obj):
        """Shows context with icon"""
        if not obj.context:
            return '-'
        
        icons = {
            'admin_panel': '⚙️',
            'api_rest': '🔗',
            'web_app': '🌐',
            'mobile_app': '📱',
            'system': '🤖'
        }
        icon = icons.get(obj.context, '📝')
        return f"{icon} {obj.context}"
    context_display.short_description = 'Contexto'
    
    def previous_data_formatted(self, obj):
        """Shows formatted previous data"""
        if not obj.previous_data:
            return "Sin datos anteriores"
        
        try:
            formatted = json.dumps(obj.previous_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
        except:
            return str(obj.previous_data)
    previous_data_formatted.short_description = 'Datos Anteriores'
    
    def new_data_formatted(self, obj):
        """Shows formatted new data"""
        if not obj.new_data:
            return "Sin datos nuevos"
        
        try:
            formatted = json.dumps(obj.new_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f8f8f8; padding: 10px; border-radius: 4px;">{}</pre>', formatted)
        except:
            return str(obj.new_data)
    new_data_formatted.short_description = 'Datos Nuevos'
    
    def changes_summary_detailed(self, obj):
        """Shows detailed changes summary"""
        if obj.operation == 'INSERT':
            return format_html(
                '<div style="color: green; font-weight: bold;">✅ Nuevo registro creado</div>'
                '<div>Tabla: <strong>{}</strong></div>'
                '<div>ID: <strong>{}</strong></div>',
                obj.affected_table,
                obj.record_id
            )
        elif obj.operation == 'DELETE':
            return format_html(
                '<div style="color: red; font-weight: bold;">❌ Registro eliminado</div>'
                '<div>Tabla: <strong>{}</strong></div>'
                '<div>ID: <strong>{}</strong></div>',
                obj.affected_table,
                obj.record_id
            )
        elif obj.operation == 'UPDATE':
            changed_fields = obj.changed_fields
            if not changed_fields:
                return format_html(
                    '<div style="color: gray;">ℹ️ Actualización sin cambios detectados</div>'
                )
            
            changes_html = []
            for field in changed_fields:
                old_value, new_value = obj.get_field_change(field)
                changes_html.append(
                    f'<div><strong>{field}:</strong> '
                    f'<span style="color: red; text-decoration: line-through;">{old_value}</span> '
                    f'→ <span style="color: green;">{new_value}</span></div>'
                )
            
            return format_html(
                '<div style="color: orange; font-weight: bold;">📝 Campos modificados:</div>'
                '{}',
                mark_safe(''.join(changes_html))
            )
        
        return obj.get_changes_summary()
    changes_summary_detailed.short_description = 'Detalle de Cambios'
    
    def get_queryset(self, request):
        """Optimizes queries with select_related"""
        return super().get_queryset(request).select_related('user')
    
    # Custom actions
    actions = ['export_audit_report']
    
    def export_audit_report(self, request, queryset):
        """Exports selected audit records (placeholder for future implementation)"""
        count = queryset.count()
        self.message_user(
            request,
            f'Funcionalidad de exportación pendiente. {count} registro(s) seleccionado(s).'
        )
    export_audit_report.short_description = "Exportar registros de auditoría"
    
    # Additional configuration
    list_per_page = 50
    list_max_show_all = 200
    
    def changelist_view(self, request, extra_context=None):
        """Add extra context to changelist view"""
        extra_context = extra_context or {}
        
        # Add some statistics
        total_records = Audit.objects.count()
        recent_records = Audit.objects.filter(
            operation_date__gte=timezone.now() - timezone.timedelta(days=7)
        ).count()
        
        extra_context.update({
            'total_audit_records': total_records,
            'recent_audit_records': recent_records,
        })
        
        return super().changelist_view(request, extra_context)


# Additional admin customizations
admin.site.site_header = "Sistema Bancario - Administración"
admin.site.site_title = "Banco Admin"
admin.site.index_title = "Panel de Administración Bancaria"
