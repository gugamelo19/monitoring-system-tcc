"""
Motor de detecção de anomalias baseado em regras de limiar.

O fluxo de avaliação para cada evento é:

1.  Se o ``source_ip`` está cadastrado como TrustedSource ativo, o
    evento é ignorado (allowlist).
2.  A regra correspondente ao protocolo do evento é executada,
    contando ocorrências dentro da janela temporal configurada.
3.  Quando o limiar é ultrapassado, antes de criar a anomalia o
    serviço verifica:
        a) se existe FalsePositiveFeedback ativo para o par
           (source_ip, anomaly_type) — neste caso, suprime;
        b) se já existe outra anomalia do mesmo tipo no mesmo asset
           dentro da janela de deduplicação — neste caso, suprime.
4.  Caso nenhuma supressão se aplique, persiste a anomalia e o alerta.

Os limiares e as janelas são lidos de ``settings.DETECTOR_THRESHOLDS``,
permitindo varredura paramétrica via variáveis de ambiente para
análise de sensibilidade.
"""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.alerts.models import Alert
from apps.anomalies.models import (
    Anomaly,
    FalsePositiveFeedback,
    TrustedSource,
)
from apps.events.models import NetworkEvent


def _thresholds() -> dict:
    return settings.DETECTOR_THRESHOLDS


class AnomalyDetectorService:
    # -------- entrada pública --------
    @staticmethod
    def analyze_event(event: NetworkEvent) -> None:
        if AnomalyDetectorService._is_trusted_source(event.source_ip):
            return

        if event.protocol == "ICMP":
            AnomalyDetectorService._check_high_icmp_rate(event)
        elif event.protocol == "TCP":
            AnomalyDetectorService._check_port_scan(event)
        elif event.protocol == "DNS":
            AnomalyDetectorService._check_dns_burst(event)

    # -------- mitigações --------
    @staticmethod
    def _is_trusted_source(source_ip: str) -> bool:
        return TrustedSource.objects.filter(
            ip_address=source_ip,
            is_active=True,
        ).exists()

    @staticmethod
    def _is_suppressed_by_feedback(source_ip: str, anomaly_type: str) -> bool:
        return FalsePositiveFeedback.objects.filter(
            source_ip=source_ip,
            anomaly_type=anomaly_type,
            suppress_until__gte=timezone.now(),
        ).exists()

    @staticmethod
    def _anomaly_exists(event: NetworkEvent,
                        anomaly_type: str,
                        seconds: int) -> bool:
        window_start = event.event_timestamp - timedelta(seconds=seconds)
        return Anomaly.objects.filter(
            asset=event.asset,
            anomaly_type=anomaly_type,
            detected_at__gte=window_start,
            detected_at__lte=timezone.now(),
        ).exists()

    @staticmethod
    def _create_anomaly_and_alert(
        *,
        event: NetworkEvent,
        anomaly_type: str,
        description: str,
        severity: str,
        score: float,
        detection_rule: str,
        title: str,
        message: str,
    ) -> None:
        thresholds = _thresholds()
        dedup_window = thresholds["DEDUPLICATION_WINDOW_SECONDS"]

        # Supressão por feedback do operador (FALSE_POSITIVE prévio).
        if AnomalyDetectorService._is_suppressed_by_feedback(
            event.source_ip, anomaly_type,
        ):
            return

        # Deduplicação por janela temporal.
        if AnomalyDetectorService._anomaly_exists(
            event, anomaly_type, seconds=dedup_window,
        ):
            return

        anomaly = Anomaly.objects.create(
            event=event,
            asset=event.asset,
            anomaly_type=anomaly_type,
            description=description,
            severity=severity,
            score=score,
            detection_rule=detection_rule,
            detected_at=timezone.now(),
        )

        Alert.objects.create(
            anomaly=anomaly,
            title=title,
            message=message,
            severity=severity,
        )

    # -------- regras --------
    @staticmethod
    def _check_high_icmp_rate(event: NetworkEvent) -> None:
        thresholds = _thresholds()
        window = thresholds["ICMP_RATE_WINDOW_SECONDS"]
        limit = thresholds["ICMP_RATE_COUNT"]

        window_start = event.event_timestamp - timedelta(seconds=window)
        count = NetworkEvent.objects.filter(
            protocol="ICMP",
            source_ip=event.source_ip,
            event_timestamp__gte=window_start,
            event_timestamp__lte=event.event_timestamp,
        ).count()

        if count > limit:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="HIGH_ICMP_RATE",
                description="Alta taxa de requisições ICMP detectada em curto intervalo.",
                severity=Anomaly.SeverityLevel.MEDIUM,
                score=70.00,
                detection_rule=f"icmp_rate_over_{limit}_in_{window}s",
                title="Alta taxa de ICMP detectada",
                message="Foi identificado um volume incomum de requisições ICMP em um curto intervalo.",
            )

    @staticmethod
    def _check_port_scan(event: NetworkEvent) -> None:
        thresholds = _thresholds()
        window = thresholds["PORT_SCAN_WINDOW_SECONDS"]
        limit = thresholds["PORT_SCAN_DISTINCT_PORTS"]

        window_start = event.event_timestamp - timedelta(seconds=window)
        distinct_ports = (
            NetworkEvent.objects.filter(
                protocol="TCP",
                source_ip=event.source_ip,
                event_timestamp__gte=window_start,
                event_timestamp__lte=event.event_timestamp,
            )
            .exclude(destination_port__isnull=True)
            .values_list("destination_port", flat=True)
            .distinct()
        )

        if distinct_ports.count() > limit:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="PORT_SCAN_SUSPECT",
                description="Possível varredura de portas detectada com múltiplas tentativas em portas distintas.",
                severity=Anomaly.SeverityLevel.HIGH,
                score=85.00,
                detection_rule=f"distinct_tcp_ports_over_{limit}_in_{window}s",
                title="Suspeita de port scan",
                message="Um mesmo IP de origem acessou múltiplas portas em curto período.",
            )

    @staticmethod
    def _check_dns_burst(event: NetworkEvent) -> None:
        thresholds = _thresholds()
        window = thresholds["DNS_BURST_WINDOW_SECONDS"]
        limit = thresholds["DNS_BURST_COUNT"]

        window_start = event.event_timestamp - timedelta(seconds=window)
        count = NetworkEvent.objects.filter(
            protocol="DNS",
            source_ip=event.source_ip,
            event_timestamp__gte=window_start,
            event_timestamp__lte=event.event_timestamp,
        ).count()

        if count > limit:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="DNS_QUERY_BURST",
                description="Excesso de consultas DNS detectado em curto intervalo.",
                severity=Anomaly.SeverityLevel.MEDIUM,
                score=75.00,
                detection_rule=f"dns_queries_over_{limit}_in_{window}s",
                title="Burst de consultas DNS",
                message="Foi identificado um volume anormal de consultas DNS em curto período.",
            )
