from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin configuration for Transaction model.
    Optimized for banking transaction management and audit.
    """
    
    # Fields shown in list
    list_display = (
        'reference_number',
        'transaction_type_display',
        'source_account_link',
        'destination_account_link',
        'amount_display_formatted',
        'status',
        'transaction_date',
        'user_link'
    )
    
    # Side filters
    list_filter = (
        'transaction_type',
        'status',
        'currency',
        'transaction_date',
        'processing_date',
        'source_account__customer__status',
    )
    
    # Search fields
    search_fields = (
        'reference_number',
        'source_account__account_number',
        'destination_account__account_number',
        'source_account__customer__first_names',
        'source_account__customer__last_names',
        'source_account__customer__document_number',
        'user__username',
        'description'
    )
    
    # Default ordering
    ordering = ('-transaction_date',)
    
    # Inline editable fields
    list_editable = ('status',)
    
    # Fieldset configuration for the form
    fieldsets = (
        ('Información de Transacción', {
            'fields': (
                'reference_number',
                'transaction_type',
                'description'
            )
        }),
        ('Cuentas Involucradas', {
            'fields': (
                'source_account',
                'destination_account'
            )
        }),
        ('Detalles Financieros', {
            'fields': (
                'amount',
                'currency',
                'previous_balance',
                'new_balance'
            )
        }),
        ('Estado y Fechas', {
            'fields': (
                'status',
                'transaction_date',
                'processing_date'
            )
        }),
        ('Auditoría', {
            'fields': (
                'user',
                'ip_address',
                'user_agent'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Read-only fields
    readonly_fields = (
        'reference_number',
        'transaction_date',
        'previous_balance',
        'new_balance'
    )
    
    # Date filters
    date_hierarchy = 'transaction_date'
    
    def transaction_type_display(self, obj):
        """Shows transaction type with color coding"""
        colors = {
            'DEPOSIT': 'green',
            'WITHDRAWAL': 'orange',
            'TRANSFER_OUT': 'red',
            'TRANSFER_IN': 'blue'
        }
        color = colors.get(obj.transaction_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Tipo'
    
    def source_account_link(self, obj):
        """Shows source account with link"""
        if obj.source_account:
            return format_html(
                '<a href="{}?id={}">{}</a>',
                reverse('admin:accounts_savingsaccount_changelist'),
                obj.source_account.id,
                obj.source_account.account_number
            )
        return '-'
    source_account_link.short_description = 'Cuenta Origen'
    
    def destination_account_link(self, obj):
        """Shows destination account with link"""
        if obj.destination_account:
            return format_html(
                '<a href="{}?id={}">{}</a>',
                reverse('admin:accounts_savingsaccount_changelist'),
                obj.destination_account.id,
                obj.destination_account.account_number
            )
        return '-'
    destination_account_link.short_description = 'Cuenta Destino'
    
    def amount_display_formatted(self, obj):
        """Shows formatted amount with color coding"""
        if obj.transaction_type in ['WITHDRAWAL', 'TRANSFER_OUT']:
            color = 'red'
            symbol = '-'
        else:
            color = 'green'
            symbol = '+'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{} {}</span>',
            color,
            symbol,
            obj.amount,
            obj.currency
        )
    amount_display_formatted.short_description = 'Monto'
    
    def status_display(self, obj):
        """Shows status with colors"""
        colors = {
            'PENDING': 'orange',
            'PROCESSED': 'green',
            'REJECTED': 'red',
            'REVERSED': 'purple'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Estado'
    
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
    
    def get_queryset(self, request):
        """Optimizes queries with select_related"""
        return super().get_queryset(request).select_related(
            'source_account',
            'destination_account', 
            'user',
            'source_account__customer'
        )
    
    # Custom actions
    actions = ['process_transactions', 'reject_transactions']
    
    def process_transactions(self, request, queryset):
        """Processes selected pending transactions"""
        pending_transactions = queryset.filter(status='PENDING')
        count = 0
        
        for transaction in pending_transactions:
            transaction.process()
            count += 1
        
        self.message_user(
            request,
            f'{count} transacción(es) procesada(s) exitosamente.'
        )
    process_transactions.short_description = "Procesar transacciones pendientes"
    
    def reject_transactions(self, request, queryset):
        """Rejects selected pending transactions"""
        pending_transactions = queryset.filter(status='PENDING')
        count = 0
        
        for transaction in pending_transactions:
            transaction.reject()
            count += 1
        
        self.message_user(
            request,
            f'{count} transacción(es) rechazada(s) exitosamente.'
        )
    reject_transactions.short_description = "Rechazar transacciones pendientes"
    
    # Additional configuration
    list_per_page = 25
    list_max_show_all = 100
    
    def save_model(self, request, obj, form, change):
        """Override for additional logic if needed"""
        super().save_model(request, obj, form, change)
