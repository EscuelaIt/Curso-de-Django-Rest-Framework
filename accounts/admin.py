from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import SavingsAccount


@admin.register(SavingsAccount)
class SavingsAccountAdmin(admin.ModelAdmin):
    """
    Admin configuration for SavingsAccount model.
    Optimized for banking account management.
    """

    # Fields shown in list
    list_display = (
        "account_number",
        "customer_link",
        "balance_display_formatted",
        "currency",
        "status",
        "opening_date",
        "last_movement_date",
        "version",
    )

    # Side filters
    list_filter = (
        "status",
        "currency",
        "opening_date",
        "customer__status",
    )

    # Search fields
    search_fields = (
        "account_number",
        "customer__first_names",
        "customer__last_names",
        "customer__document_number",
        "customer__email",
    )

    # Default ordering
    ordering = ("-opening_date",)

    # Inline editable fields
    list_editable = ("status",)

    # Fieldset configuration for the form
    fieldsets = (
        (
            "Información de Cuenta",
            {"fields": ("account_number", "customer", "currency")},
        ),
        ("Saldos", {"fields": ("current_balance", "available_balance")}),
        ("Estado y Control", {"fields": ("status", "version")}),
        (
            "Fechas",
            {
                "fields": ("opening_date", "last_movement_date"),
                "classes": ("collapse",),
            },
        ),
    )

    # Read-only fields
    readonly_fields = ("opening_date", "version")

    # Date filters
    date_hierarchy = "opening_date"

    def customer_link(self, obj):
        """Shows customer with link to customer admin"""
        if obj.customer:
            return format_html(
                '<a href="{}?id={}">{}</a>',
                reverse("admin:customers_customer_changelist"),
                obj.customer.id,
                obj.customer.full_name,
            )
        return "-"

    customer_link.short_description = "Cliente"

    def balance_display_formatted(self, obj):
        """Shows formatted balance with color coding"""
        balance = obj.current_balance
        if balance == 0:
            color = "gray"
        elif balance < 100:
            color = "orange"
        else:
            color = "green"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            balance,
            obj.currency,
        )

    balance_display_formatted.short_description = "Saldo Actual"

    def status_display(self, obj):
        """Shows status with colors"""
        colors = {"ACTIVE": "green", "BLOCKED": "orange", "CLOSED": "red"}
        color = colors.get(obj.status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_display.short_description = "Estado"

    def get_queryset(self, request):
        """Optimizes queries with select_related"""
        return super().get_queryset(request).select_related("customer")

    # Custom actions
    actions = ["activate_accounts", "block_accounts", "close_accounts"]

    def activate_accounts(self, request, queryset):
        """Activates selected accounts"""
        count = queryset.update(status="ACTIVE")
        self.message_user(request, f"{count} cuenta(s) activada(s) exitosamente.")

    activate_accounts.short_description = "Activar cuentas seleccionadas"

    def block_accounts(self, request, queryset):
        """Blocks selected accounts"""
        count = queryset.update(status="BLOCKED")
        self.message_user(request, f"{count} cuenta(s) bloqueada(s) exitosamente.")

    block_accounts.short_description = "Bloquear cuentas seleccionadas"

    def close_accounts(self, request, queryset):
        """Closes selected accounts"""
        # Only close accounts with zero balance
        zero_balance_accounts = queryset.filter(current_balance=0)
        count = zero_balance_accounts.update(status="CLOSED")

        if count < queryset.count():
            self.message_user(
                request,
                f"{count} cuenta(s) cerrada(s). Solo se pueden cerrar cuentas con saldo cero.",
                level="WARNING",
            )
        else:
            self.message_user(request, f"{count} cuenta(s) cerrada(s) exitosamente.")

    close_accounts.short_description = "Cerrar cuentas seleccionadas (solo saldo cero)"

    # Additional configuration
    list_per_page = 25
    list_max_show_all = 100

    def save_model(self, request, obj, form, change):
        """Override for additional logic if needed"""
        super().save_model(request, obj, form, change)
