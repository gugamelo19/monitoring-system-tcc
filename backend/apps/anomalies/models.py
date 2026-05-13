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


class TrustedSource(models.Model):
    """
    IP de origem confiável que é ignorado pelo motor de detecção
    (allowlist). Utilizado para suprimir falsos positivos previsíveis,
    como servidores legítimos de monitoramento (Zabbix, Nagios) ou
    scanners de inventário contratados.

    Quando o IP de origem de um evento está cadastrado nesta tabela,
    o AnomalyDetectorService não avalia o evento.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ip_address = models.GenericIPAddressField(unique=True)
    description = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ip_address"]
        verbose_name = "Trusted source"
        verbose_name_plural = "Trusted sources"

    def __str__(self):
        return f"{self.ip_address} ({self.description})" if self.description \
            else self.ip_address


class FalsePositiveFeedback(models.Model):
    """
    Registro produzido quando um operador marca um alerta como
    FALSE_POSITIVE. Suprime futuras anomalias do mesmo tipo, originárias
    do mesmo source_ip, até a data definida em ``suppress_until``.

    Esse mecanismo realimenta o detector com a opinião humana, evitando
    que o sistema gere repetidamente alertas que o operador já julgou
    irrelevantes.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_ip = models.GenericIPAddressField()
    anomaly_type = models.CharField(max_length=100)
    suppress_until = models.DateTimeField()
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-suppress_until"]
        unique_together = ("source_ip", "anomaly_type")
        verbose_name = "False positive feedback"
        verbose_name_plural = "False positive feedbacks"

    def __str__(self):
        return f"{self.anomaly_type} @ {self.source_ip} -> {self.suppress_until:%Y-%m-%d %H:%M}"
