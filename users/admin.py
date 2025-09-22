from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin with role-based fields.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_approved', 'is_active', 'date_joined')
    list_filter = ('role', 'is_approved', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Approval', {'fields': ('role', 'is_approved', 'phone_number')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role & Approval', {'fields': ('role', 'is_approved', 'phone_number')}),
    )
