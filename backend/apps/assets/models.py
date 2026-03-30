import uuid
from django.db import models


class Asset(models.Model):
    class AssetType(models.TextChoices):
        SERVER = "SERVER", "Server"
        ROUTER = "ROUTER", "Router"
        SWITCH = "SWITCH", "Switch"
        FIREWALL = "FIREWALL", "Firewall"
        WORKSTATION = "WORKSTATION", "Workstation"
        OTHER = "OTHER", "Other"

    class AssetStatus(models.TextChoices):
        ONLINE = "ONLINE", "Online"
        OFFLINE = "OFFLINE", "Offline"
        UNSTABLE = "UNSTABLE", "Unstable"
        UNKNOWN = "UNKNOWN", "Unknown"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    hostname = models.CharField(max_length=150, blank=True, null=True)
    ip_address = models.GenericIPAddressField(unique=True)
    mac_address = models.CharField(max_length=17, blank=True, null=True)
    asset_type = models.CharField(
        max_length=20, choices=AssetType.choices, default=AssetType.OTHER)
    location = models.CharField(max_length=150, blank=True, null=True)
    operating_system = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=AssetStatus.choices, default=AssetStatus.UNKNOWN)
    is_monitored = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.ip_address})"
