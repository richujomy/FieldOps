from django.contrib import admin
from .models import ServiceRequest
# Register your models here.

@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'description', 'location', 'urgency', 'status', 'rating', 'created_at', 'updated_at')
    list_filter = ('urgency', 'status', 'created_at', 'updated_at')
    search_fields = ('customer__username', 'description', 'location')
    ordering = ('-created_at',)
