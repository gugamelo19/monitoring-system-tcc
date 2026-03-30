import uuid
from django.conf import settings
from django.db import models
from apps.anomalies.models import Anomaly


class Alert(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In progress"
        RESOLVED = "RESOLVED", "Resolved"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False positive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    anomaly = models.OneToOneField(
        Anomaly, on_delete=models.CASCADE, related_name="alert")
    title = models.CharField(max_length=150)
    message = models.TextField()
    severity = models.CharField(
        max_length=10, choices=Anomaly.SeverityLevel.choices)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_alerts",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
