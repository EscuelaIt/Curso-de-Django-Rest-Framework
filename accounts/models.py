from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import random


class SavingsAccount(models.Model):
    """
    Model for savings accounts.
    Only handles savings accounts for natural persons.
    """
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Activa'),
        ('BLOCKED', 'Bloqueada'),
        ('CLOSED', 'Cerrada'),
    ]
    
    CURRENCY_CHOICES = [
        ('PEN', 'Soles Peruanos'),
        ('USD', 'Dólares Americanos'),
        ('EUR', 'Euros'),
    ]
    
    # Main fields
    account_number = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Unique bank account number"
    )
    customer = models.ForeignKey(
        'customers.Customer', 
        on_delete=models.PROTECT,
        related_name='savings_accounts',
        help_text="Account owner customer"
    )
    
    # Financial fields
    current_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Current account balance"
    )
    available_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Available balance for operations"
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='PEN',
        help_text="Account currency"
    )
    
    # Control fields
    opening_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Account opening date"
    )
    last_movement_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date of last transaction"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        help_text="Current account status"
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version for change control"
    )
    
    class Meta:
        db_table = 'savings_accounts'
        indexes = [
            models.Index(fields=['account_number'], name='idx_account_number'),
            models.Index(fields=['customer'], name='idx_account_customer'),
            models.Index(fields=['status'], name='idx_account_status'),
            models.Index(fields=['opening_date'], name='idx_account_opening_date'),
        ]
        verbose_name = 'Cuenta de Ahorro'
        verbose_name_plural = 'Cuentas de Ahorro'
    
    def __str__(self):
        return f"Account {self.account_number} - {self.customer.full_name}"
    
    def clean(self):
        """Custom validations"""
        super().clean()
        
        if self.available_balance > self.current_balance:
            raise ValidationError('Available balance cannot be greater than current balance')
    
    @property
    def balance_display(self):
        """Returns formatted balance with currency"""
        return f"{self.current_balance} {self.currency}"
    
    @property
    def is_active(self):
        """Checks if account is active"""
        return self.status == 'ACTIVE'
    
    @property
    def is_blocked(self):
        """Checks if account is blocked"""
        return self.status == 'BLOCKED'
    
    def save(self, *args, **kwargs):
        """Override save for validations and versioning"""
        if not self.account_number:
            self.account_number = self._generate_account_number()
        
        self.full_clean()
        
        # Increment version on each update (except first time)
        if self.pk:
            self.version += 1
        
        super().save(*args, **kwargs)
    
    def _generate_account_number(self):
        """Generates a unique account number"""
        while True:
            number = f"001-{random.randint(100000, 999999)}"
            if not SavingsAccount.objects.filter(account_number=number).exists():
                return number
    
    def activate(self):
        """Activates the account"""
        self.status = 'ACTIVE'
        self.save(update_fields=['status'])
    
    def block(self):
        """Blocks the account"""
        self.status = 'BLOCKED'
        self.save(update_fields=['status'])
    
    def close(self):
        """Closes the account"""
        self.status = 'CLOSED'
        self.save(update_fields=['status'])
