import uuid
from django.db import models
from apps.assets.models import Asset
from apps.events.models import NetworkEvent


class Anomaly(models.Model):
    class SeverityLevel(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        UNDER_ANALYSIS = "UNDER_ANALYSIS", "Under analysis"
        CONFIRMED = "CONFIRMED", "Confirmed"
        DISMISSED = "DISMISSED", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        NetworkEvent, on_delete=models.CASCADE, related_name="anomalies")
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="anomalies")
    anomaly_type = models.CharField(max_length=100)
    description = models.TextField()
    severity = models.CharField(max_length=10, choices=SeverityLevel.choices)
    score = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True)
    detection_rule = models.CharField(max_length=150)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW)
    detected_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-detected_at"]

    def __str__(self):
        return f"{self.anomaly_type} - {self.severity}"
