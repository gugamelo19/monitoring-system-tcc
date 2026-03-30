import uuid
from django.db import models
from apps.assets.models import Asset


class NetworkEvent(models.Model):
    class ProtocolType(models.TextChoices):
        ICMP = "ICMP", "ICMP"
        TCP = "TCP", "TCP"
        DNS = "DNS", "DNS"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset = models.ForeignKey(
        Asset, on_delete=models.CASCADE, related_name="events")
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    source_port = models.PositiveIntegerField(blank=True, null=True)
    destination_port = models.PositiveIntegerField(blank=True, null=True)
    protocol = models.CharField(max_length=10, choices=ProtocolType.choices)
    transport_layer = models.CharField(max_length=20, blank=True, null=True)
    packet_size = models.PositiveIntegerField(blank=True, null=True)
    tcp_flags = models.CharField(max_length=20, blank=True, null=True)
    dns_query = models.CharField(max_length=255, blank=True, null=True)
    icmp_type = models.PositiveIntegerField(blank=True, null=True)
    icmp_code = models.PositiveIntegerField(blank=True, null=True)
    event_timestamp = models.DateTimeField()
    raw_summary = models.TextField(blank=True, null=True)
    collector_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-event_timestamp"]

    def __str__(self):
        return f"{self.protocol} {self.source_ip} -> {self.destination_ip}"
