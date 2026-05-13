from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.anomalies.models import FalsePositiveFeedback

from .models import Alert
from .serializers import AlertSerializer


class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.select_related(
        "anomaly", "anomaly__asset", "anomaly__event", "assigned_to").all()
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "head", "options"]

    def perform_update(self, serializer):
        instance = serializer.save()

        if instance.status == Alert.Status.RESOLVED and instance.resolved_at is None:
            instance.resolved_at = timezone.now()
            instance.save(update_fields=["resolved_at"])

        if instance.status == Alert.Status.FALSE_POSITIVE:
            self._register_false_positive_feedback(instance)

    @staticmethod
    def _register_false_positive_feedback(alert: Alert) -> None:
        """
        Quando um alerta é marcado como FALSE_POSITIVE pelo operador,
        registra (ou atualiza) um FalsePositiveFeedback associado ao
        par (source_ip da anomalia, tipo da anomalia). Esse registro é
        consultado pelo detector para suprimir futuras anomalias
        equivalentes dentro do período definido em settings.
        """
        anomaly = alert.anomaly
        event = anomaly.event

        hours = settings.DETECTOR_THRESHOLDS["FALSE_POSITIVE_SUPPRESS_HOURS"]
        suppress_until = timezone.now() + timedelta(hours=hours)

        FalsePositiveFeedback.objects.update_or_create(
            source_ip=event.source_ip,
            anomaly_type=anomaly.anomaly_type,
            defaults={
                "suppress_until": suppress_until,
                "note": (
                    f"Gerado automaticamente a partir do alerta "
                    f"{alert.id} (anomalia {anomaly.id})."
                ),
            },
        )
