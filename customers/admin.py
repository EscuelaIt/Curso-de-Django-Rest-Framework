from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin configuration for Customer model.
    Optimized for banking management with validations and clear visualization.
    """
    
    # Fields shown in list
    list_display = (
        'document_number',
        'full_name',
        'full_document',
        'email',
        'phone',
        'age_display',
        'status',
        'created_at',
        'associated_users_count'
    )
    
    # Side filters
    list_filter = (
        'status',
        'document_type',
        'created_at',
        'updated_at'
    )
    
    # Search fields
    search_fields = (
        'document_number',
        'first_names',
        'last_names',
        'email',
        'phone'
    )
    
    # Default ordering
    ordering = ('-created_at',)
    
    # Inline editable fields
    list_editable = ('status',)
    
    # Fieldset configuration for the form
    fieldsets = (
        ('Identificación', {
            'fields': (
                'document_type',
                'document_number'
            )
        }),
        ('Información Personal', {
            'fields': (
                'first_names',
                'last_names',
                'birth_date',
                'email',
                'phone',
                'address'
            )
        }),
        ('Estado y Control', {
            'fields': (
                'status',
                'version'
            )
        }),
        ('Fechas del Sistema', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Read-only fields
    readonly_fields = (
        'created_at',
        'updated_at',
        'version'
    )
    
    # Date filters
    date_hierarchy = 'created_at'
    
    def age_display(self, obj):
        """Shows the calculated age"""
        age = obj.age
        if age:
            if age < 18:
                return format_html(
                    '<span style="color: red;">{} años (Menor)</span>',
                    age
                )
            elif age >= 65:
                return format_html(
                    '<span style="color: blue;">{} años (Senior)</span>',
                    age
                )
            else:
                return f"{age} años"
        return '-'
    age_display.short_description = 'Edad'
    
    def associated_users_count(self, obj):
        """Counts users associated with the customer"""
        count = obj.users.count()
        if count > 0:
            return format_html(
                '<a href="{}?customer__id__exact={}">{} usuario(s)</a>',
                reverse('admin:users_user_changelist'),
                obj.id,
                count
            )
        return '0 usuarios'
    associated_users_count.short_description = 'Usuarios'
    
    def get_queryset(self, request):
        """Optimizes queries with prefetch_related"""
        return super().get_queryset(request).prefetch_related('users')
    
    # Custom actions
    actions = ['activate_customers', 'suspend_customers', 'deactivate_customers']
    
    def activate_customers(self, request, queryset):
        """Activates selected customers"""
        count = queryset.update(status='ACTIVE')
        self.message_user(
            request,
            f'{count} cliente(s) activado(s) exitosamente.'
        )
    activate_customers.short_description = "Activar clientes seleccionados"
    
    def suspend_customers(self, request, queryset):
        """Suspends selected customers"""
        count = queryset.update(status='SUSPENDED')
        self.message_user(
            request,
            f'{count} cliente(s) suspendido(s) exitosamente.'
        )
    suspend_customers.short_description = "Suspender clientes seleccionados"
    
    def deactivate_customers(self, request, queryset):
        """Deactivates selected customers"""
        count = queryset.update(status='INACTIVE')
        self.message_user(
            request,
            f'{count} cliente(s) inactivado(s) exitosamente.'
        )
    deactivate_customers.short_description = "Inactivar clientes seleccionados"
    
    # Additional configuration
    list_per_page = 25
    list_max_show_all = 100
    
    def save_model(self, request, obj, form, change):
        """Override for additional logging if needed"""
        super().save_model(request, obj, form, change)
        
        # Here we could add custom logging
        if change:
            # Log changes to existing customer
            pass
        else:
            # Log new customer
            pass