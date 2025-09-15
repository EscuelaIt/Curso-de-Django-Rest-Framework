from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model for banking system.
    Extends AbstractUser to maintain Django Auth compatibility.
    Conceptually separated from Customer to allow multiple access methods.
    """

    ROLE_CHOICES = [
        ("CUSTOMER", "Cliente"),
        ("OPERATOR", "Operador"),
        ("ADMIN", "Administrador"),
    ]

    # Additional fields (username, email, password come from AbstractUser)
    first_names = models.CharField(max_length=100, help_text="First names of the user")
    last_names = models.CharField(max_length=100, help_text="Last names of the user")
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, help_text="User role in the system"
    )

    # Relationship with customer (optional - only for CUSTOMER role)
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
        help_text="Associated customer (only for CUSTOMER role)",
    )

    # Banking security fields
    last_access = models.DateTimeField(
        null=True, blank=True, help_text="Last system access"
    )
    failed_attempts = models.PositiveIntegerField(
        default=0, help_text="Number of failed login attempts"
    )
    blocked_until = models.DateTimeField(
        null=True, blank=True, help_text="Date until which the user is blocked"
    )

    # Control fields (date_joined comes from AbstractUser)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["username"], name="idx_user_username"),
            models.Index(fields=["email"], name="idx_user_email"),
            models.Index(fields=["customer"], name="idx_user_customer"),
            models.Index(fields=["role"], name="idx_user_role"),
        ]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def clean(self):
        """Custom validations"""
        super().clean()

        # Validate user-customer relationship according to role
        if self.role == "CUSTOMER" and not self.customer:
            raise ValidationError(
                "Los usuarios con rol CLIENTE deben tener un cliente asociado"
            )

        if self.role in ["OPERATOR", "ADMIN"] and self.customer:
            raise ValidationError(
                "Los usuarios OPERADOR/ADMIN no pueden tener cliente asociado"
            )

    @property
    def full_name(self):
        """Returns the user's full name"""
        return f"{self.first_names} {self.last_names}"

    @property
    def is_blocked(self):
        """Checks if the user is temporarily blocked"""
        if not self.blocked_until:
            return False
        return timezone.now() < self.blocked_until

    def block_temporarily(self, minutes=30):
        """Blocks the user temporarily"""
        self.blocked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save(update_fields=["blocked_until"])

    def unblock(self):
        """Unblocks the user"""
        self.blocked_until = None
        self.failed_attempts = 0
        self.save(update_fields=["blocked_until", "failed_attempts"])

    def register_failed_attempt(self):
        """Registers a failed login attempt"""
        self.failed_attempts += 1
        if self.failed_attempts >= 3:  # Block after 3 attempts
            self.block_temporarily()
        else:
            self.save(update_fields=["failed_attempts"])

    def register_successful_access(self):
        """Registers a successful access"""
        self.last_access = timezone.now()
        self.failed_attempts = 0
        self.blocked_until = None
        self.save(update_fields=["last_access", "failed_attempts", "blocked_until"])
