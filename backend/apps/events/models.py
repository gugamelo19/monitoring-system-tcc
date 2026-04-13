from django.db import models


class NetworkEvent(models.Model):
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.CASCADE,
        related_name="events",
    )
    protocol = models.CharField(max_length=20)
    source_ip = models.GenericIPAddressField()
    destination_ip = models.GenericIPAddressField()
    source_port = models.IntegerField(null=True, blank=True)
    destination_port = models.IntegerField(null=True, blank=True)
    packet_size = models.IntegerField(null=True, blank=True)
    tcp_flags = models.CharField(max_length=50, blank=True, default="")
    dns_query = models.CharField(max_length=255, blank=True, default="")
    icmp_type = models.IntegerField(null=True, blank=True)
    icmp_code = models.IntegerField(null=True, blank=True)
    event_timestamp = models.DateTimeField()
    raw_summary = models.TextField(blank=True, default="")
    collector_name = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.protocol} - {self.asset.name}"
