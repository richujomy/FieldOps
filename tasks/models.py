from django.db import models
from django.conf import settings
from service_requests.models import ServiceRequest


def task_proof_upload_path(instance, filename: str) -> str:
    return f"task_proofs/{instance.id or 'new'}/{filename}"


class Task(models.Model):
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )
    notes = models.TextField(blank=True)
    proof_upload = models.FileField(upload_to=task_proof_upload_path, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tasks"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Task #{self.id} for SR {self.service_request_id} ({self.status})"

# Create your models here.
