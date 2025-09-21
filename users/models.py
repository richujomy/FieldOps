from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('field_worker', 'Field Worker'),
        ('customer', 'Customer'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='customer',
        help_text='User role determining access permissions'
    )
    
    is_approved = models.BooleanField(
        default=False,
        help_text='Whether the field worker is approved by admin'
    )
    
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        help_text='Contact phone number'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_field_worker(self):
        return self.role == 'field_worker'
    
    @property
    def is_customer(self):
        return self.role == 'customer'
    
    @property
    def is_admin(self):
        return self.role == 'admin'
