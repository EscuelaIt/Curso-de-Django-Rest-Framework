from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from datetime import date


class Customer(models.Model):
    """
    Model for natural persons who are bank customers.
    Represents the business entity that owns banking products.
    Separated from User to allow multiple access methods.
    """
    
    DOCUMENT_TYPE_CHOICES = [
        ('DNI', 'Documento Nacional de Identidad'),
        ('CE', 'Carnet de Extranjería'),
        ('PASSPORT', 'Pasaporte'),
    ]
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Activo'),
        ('INACTIVE', 'Inactivo'),
        ('SUSPENDED', 'Suspendido'),
    ]
    
    # Identification fields
    document_type = models.CharField(
        max_length=10,
        choices=DOCUMENT_TYPE_CHOICES,
        help_text="Type of identity document"
    )
    document_number = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[A-Z0-9]+$', 'Only uppercase letters and numbers')],
        help_text="Document number without spaces or hyphens"
    )
    
    # Personal information
    first_names = models.CharField(max_length=100, help_text="Customer's first names")
    last_names = models.CharField(max_length=100, help_text="Customer's last names")
    email = models.EmailField(unique=True, help_text="Customer's unique email")
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?[0-9\-\s]+$', 'Invalid phone format')],
        help_text="Contact phone number"
    )
    birth_date = models.DateField(help_text="Date of birth")
    address = models.TextField(help_text="Complete address")
    
    # Control fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Registration date in the system"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last data update"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        help_text="Current customer status"
    )
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version for change control"
    )
    
    class Meta:
        db_table = 'customers'
        constraints = [
            models.UniqueConstraint(
                fields=['document_type', 'document_number'],
                name='unique_customer_document'
            )
        ]
        indexes = [
            models.Index(fields=['document_type', 'document_number'], name='idx_customer_document'),
            models.Index(fields=['email'], name='idx_customer_email'),
            models.Index(fields=['status'], name='idx_customer_status'),
            models.Index(fields=['created_at'], name='idx_customer_created_at'),
        ]
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
    
    def __str__(self):
        return f"{self.full_name} ({self.document_number})"
    
    def clean(self):
        """Custom validations"""
        super().clean()
        
        # Validate minimum age (18 years)
        if self.birth_date:
            age = (date.today() - self.birth_date).days // 365
            if age < 18:
                raise ValidationError('El cliente debe ser mayor de edad (18 años)')
        
        # Validate document format according to type
        if self.document_type == 'DNI' and len(self.document_number) != 8:
            raise ValidationError('El DNI debe tener 8 dígitos')
        elif self.document_type == 'CE' and len(self.document_number) != 9:
            raise ValidationError('El Carnet de Extranjería debe tener 9 caracteres')
        
        # Validate email domain restriction
        if self.email:
            if not self.email.lower().endswith('@escuela.it'):
                raise ValidationError('Solo se permiten correos del dominio @escuela.it')
            
            # Normalize email to lowercase
            self.email = self.email.lower()
    
    @property
    def full_name(self):
        """Returns the customer's full name"""
        return f"{self.first_names} {self.last_names}"
    
    @property
    def age(self):
        """Calculates the customer's current age"""
        if not self.birth_date:
            return None
        return (date.today() - self.birth_date).days // 365
    
    @property
    def full_document(self):
        """Returns the document with its type"""
        return f"{self.get_document_type_display()}: {self.document_number}"
    
    def save(self, *args, **kwargs):
        """Override save for validations and versioning"""
        self.full_clean()
        
        # Increment version on each update (except first time)
        if self.pk:
            self.version += 1
        
        super().save(*args, **kwargs)
    
    def activate(self):
        """Activates the customer"""
        self.status = 'ACTIVE'
        self.save(update_fields=['status'])
    
    def suspend(self):
        """Suspends the customer"""
        self.status = 'SUSPENDED'
        self.save(update_fields=['status'])
    
    def deactivate(self):
        """Deactivates the customer"""
        self.status = 'INACTIVE'
        self.save(update_fields=['status'])
