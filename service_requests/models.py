from django.db import models
from django.conf import settings


class ServiceRequest(models.Model):
    """
    Customer-submitted service request.
    """
    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="service_requests",
    )
    assigned_field_worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_service_requests",
        limit_choices_to={'role': 'field_worker', 'is_approved': True},
        help_text="Field worker assigned to this service request"
    )
    description = models.TextField()
    location = models.CharField(max_length=255)
    urgency = models.CharField(
        max_length=16,
        choices=Urgency.choices,
        default=Urgency.MEDIUM,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )
    rating = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-5 rating after completion")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "service_requests"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Request #{self.id} by {self.customer_id} ({self.status})"
