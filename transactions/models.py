from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal
import random
import string
from datetime import datetime


class Transaction(models.Model):
    """
    Model for all banking transactions.
    Handles deposits, withdrawals and transfers.
    """
    
    TYPE_CHOICES = [
        ('DEPOSIT', 'Depósito'),
        ('WITHDRAWAL', 'Retiro'),
        ('TRANSFER_OUT', 'Transferencia Salida'),
        ('TRANSFER_IN', 'Transferencia Entrada'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSED', 'Procesada'),
        ('REJECTED', 'Rechazada'),
        ('REVERSED', 'Reversada'),
    ]
    
    CURRENCY_CHOICES = [
        ('PEN', 'Soles Peruanos'),
        ('USD', 'Dólares Americanos'),
        ('EUR', 'Euros'),
    ]
    
    # Main fields
    reference_number = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Unique transaction reference number"
    )
    transaction_type = models.CharField(
        max_length=30, 
        choices=TYPE_CHOICES,
        help_text="Type of transaction"
    )
    
    # Involved accounts
    source_account = models.ForeignKey(
        'accounts.SavingsAccount',
        on_delete=models.PROTECT,
        related_name='outgoing_transactions',
        help_text="Source account for the transaction"
    )
    destination_account = models.ForeignKey(
        'accounts.SavingsAccount',
        on_delete=models.PROTECT,
        related_name='incoming_transactions',
        null=True,
        blank=True,
        help_text="Destination account (only for transfers)"
    )
    
    # Financial fields
    amount = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transaction amount"
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='PEN',
        help_text="Transaction currency"
    )
    description = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Transaction description"
    )
    
    # Balance control fields
    previous_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Balance before transaction"
    )
    new_balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Balance after transaction"
    )
    
    # Time fields
    transaction_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Transaction creation date"
    )
    processing_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="Transaction processing date"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        help_text="Transaction status"
    )
    
    # Audit fields
    user = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text="User who executed the transaction"
    )
    ip_address = models.GenericIPAddressField(
        help_text="IP address of origin"
    )
    user_agent = models.CharField(
        max_length=500, 
        blank=True,
        help_text="User agent information"
    )
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['reference_number'], name='idx_transaction_reference'),
            models.Index(fields=['source_account'], name='idx_transaction_source'),
            models.Index(fields=['transaction_date'], name='idx_transaction_date'),
            models.Index(fields=['status'], name='idx_transaction_status'),
            models.Index(fields=['transaction_type'], name='idx_transaction_type'),
        ]
        verbose_name = 'Transacción'
        verbose_name_plural = 'Transacciones'
    
    def __str__(self):
        return f"{self.reference_number} - {self.transaction_type} - {self.amount} {self.currency}"
    
    def clean(self):
        """Custom validations"""
        super().clean()
        
        # Validate that source and destination accounts are different
        if self.destination_account and self.source_account == self.destination_account:
            raise ValidationError('Source and destination accounts cannot be the same')
        
        # Validate that transfers have destination account
        if self.transaction_type in ['TRANSFER_OUT', 'TRANSFER_IN'] and not self.destination_account:
            raise ValidationError('Transfers require destination account')
        
        # Validate that deposits and withdrawals don't have destination account
        if self.transaction_type in ['DEPOSIT', 'WITHDRAWAL'] and self.destination_account:
            raise ValidationError('Deposits and withdrawals should not have destination account')
    
    @property
    def amount_display(self):
        """Returns formatted amount with currency"""
        return f"{self.amount} {self.currency}"
    
    @property
    def is_pending(self):
        """Checks if transaction is pending"""
        return self.status == 'PENDING'
    
    @property
    def is_processed(self):
        """Checks if transaction is processed"""
        return self.status == 'PROCESSED'
    
    def save(self, *args, **kwargs):
        """Override save for validations and reference generation"""
        # Generate reference number if it doesn't exist (before validation)
        if not self.reference_number:
            self.reference_number = self._generate_reference_number()
        
        # Set balance fields if not provided (before validation)
        if self.previous_balance is None:
            self.previous_balance = self.source_account.current_balance if self.source_account else 0
        
        if self.new_balance is None and self.source_account:
            if self.transaction_type == 'DEPOSIT':
                self.new_balance = self.previous_balance + self.amount
            elif self.transaction_type == 'WITHDRAWAL':
                self.new_balance = self.previous_balance - self.amount
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def _generate_reference_number(self):
        """Generates a unique reference number"""
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"TXN{date_part}{random_part}"
    
    def process(self):
        """Marks transaction as processed"""
        from django.utils import timezone
        self.status = 'PROCESSED'
        self.processing_date = timezone.now()
        self.save(update_fields=['status', 'processing_date'])
    
    def reject(self):
        """Marks transaction as rejected"""
        self.status = 'REJECTED'
        self.save(update_fields=['status'])
    
    def reverse(self):
        """Marks transaction as reversed"""
        self.status = 'REVERSED'
        self.save(update_fields=['status'])
