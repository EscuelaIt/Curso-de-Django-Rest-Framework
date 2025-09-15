from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuración del admin para el modelo Usuario personalizado.
    Extiende UserAdmin para mantener funcionalidad de Django Auth.
    """

    # Campos mostrados en la lista
    list_display = (
        "username",
        "email",
        "full_name",
        "role",
        "associated_customer",
        "is_active",
        "is_blocked_display",
        "last_access",
    )

    # Filtros laterales
    list_filter = (
        "role",
        "is_active",
        "is_staff",
        "is_superuser",
        "date_joined",
        "last_access",
    )

    # Campos de búsqueda
    search_fields = (
        "username",
        "email",
        "first_names",
        "last_names",
        "customer__first_names",
        "customer__last_names",
        "customer__document_number",
    )

    # Ordenamiento por defecto
    ordering = ("-date_joined",)

    # Campos editables en línea
    list_editable = ("is_active",)

    # Configuración de fieldsets para el formulario de edición
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Información Personal", {"fields": ("first_names", "last_names", "email")}),
        ("Información Bancaria", {"fields": ("role", "customer")}),
        (
            "Seguridad",
            {
                "fields": ("failed_attempts", "blocked_until", "last_access"),
                "classes": ("collapse",),
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            "Fechas Importantes",
            {
                "fields": ("last_login", "date_joined", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    # Campos para crear usuario
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_names",
                    "last_names",
                    "role",
                    "customer",  # ← Agregado para poder seleccionar cliente al crear
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    # Campos de solo lectura
    readonly_fields = ("date_joined", "updated_at", "last_access")

    def associated_customer(self, obj):
        """Shows the associated customer if exists"""
        if obj.customer:
            return format_html(
                '<a href="/admin/customers/customer/{}/change/">{}</a>',
                obj.customer.id,
                obj.customer.full_name,
            )
        return "-"

    associated_customer.short_description = "Cliente"

    def esta_activo(self, obj):
        """Indicador visual de si el usuario está activo"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Activo</span>')
        return format_html('<span style="color: red;">✗ Inactivo</span>')

    esta_activo.short_description = "Estado"

    def is_blocked_display(self, obj):
        """Shows if the user is blocked"""
        if obj.is_blocked:
            return format_html('<span style="color: red;">🔒 Bloqueado</span>')
        return format_html('<span style="color: green;">🔓 Desbloqueado</span>')

    is_blocked_display.short_description = "Bloqueo"

    def get_queryset(self, request):
        """Optimizes queries with select_related"""
        return super().get_queryset(request).select_related("customer")

    actions = ["unblock_users", "block_users"]

    def unblock_users(self, request, queryset):
        """Action to unblock selected users"""
        count = 0
        for user in queryset:
            if user.is_blocked:
                user.unblock()
                count += 1

        self.message_user(request, f"{count} usuario(s) desbloqueado(s) exitosamente.")

    unblock_users.short_description = "Desbloquear usuarios seleccionados"

    def block_users(self, request, queryset):
        """Action to block selected users"""
        count = 0
        for user in queryset.filter(is_superuser=False):  # Don't block superusers
            user.block_temporarily()
            count += 1

        self.message_user(request, f"{count} usuario(s) bloqueado(s) exitosamente.")

    block_users.short_description = "Bloquear usuarios seleccionados"
