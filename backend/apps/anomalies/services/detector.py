from datetime import timedelta
from django.utils import timezone

from apps.events.models import NetworkEvent
from apps.anomalies.models import Anomaly
from apps.alerts.models import Alert


class AnomalyDetectorService:
    @staticmethod
    def analyze_event(event: NetworkEvent) -> None:
        if event.protocol == "ICMP":
            AnomalyDetectorService._check_high_icmp_rate(event)

        elif event.protocol == "TCP":
            AnomalyDetectorService._check_port_scan(event)

        elif event.protocol == "DNS":
            AnomalyDetectorService._check_dns_burst(event)

    @staticmethod
    def _anomaly_exists(event: NetworkEvent, anomaly_type: str, seconds: int = 60) -> bool:
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
        if AnomalyDetectorService._anomaly_exists(event, anomaly_type):
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

    @staticmethod
    def _check_high_icmp_rate(event: NetworkEvent) -> None:
        window_start = event.event_timestamp - timedelta(seconds=30)

        count = NetworkEvent.objects.filter(
            protocol="ICMP",
            source_ip=event.source_ip,
            event_timestamp__gte=window_start,
            event_timestamp__lte=event.event_timestamp,
        ).count()

        if count > 20:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="HIGH_ICMP_RATE",
                description="Alta taxa de requisições ICMP detectada em curto intervalo.",
                severity=Anomaly.SeverityLevel.MEDIUM,
                score=70.00,
                detection_rule="icmp_rate_over_20_in_30s",
                title="Alta taxa de ICMP detectada",
                message="Foi identificado um volume incomum de requisições ICMP em um curto intervalo.",
            )

    @staticmethod
    def _check_port_scan(event: NetworkEvent) -> None:
        window_start = event.event_timestamp - timedelta(minutes=1)

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

        if len(list(distinct_ports)) > 10:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="PORT_SCAN_SUSPECT",
                description="Possível varredura de portas detectada com múltiplas tentativas em portas distintas.",
                severity=Anomaly.SeverityLevel.HIGH,
                score=85.00,
                detection_rule="distinct_tcp_ports_over_10_in_1m",
                title="Suspeita de port scan",
                message="Um mesmo IP de origem acessou múltiplas portas em curto período.",
            )

    @staticmethod
    def _check_dns_burst(event: NetworkEvent) -> None:
        window_start = event.event_timestamp - timedelta(minutes=1)

        count = NetworkEvent.objects.filter(
            protocol="DNS",
            source_ip=event.source_ip,
            event_timestamp__gte=window_start,
            event_timestamp__lte=event.event_timestamp,
        ).count()

        if count > 30:
            AnomalyDetectorService._create_anomaly_and_alert(
                event=event,
                anomaly_type="DNS_QUERY_BURST",
                description="Excesso de consultas DNS detectado em curto intervalo.",
                severity=Anomaly.SeverityLevel.MEDIUM,
                score=75.00,
                detection_rule="dns_queries_over_30_in_1m",
                title="Burst de consultas DNS",
                message="Foi identificado um volume anormal de consultas DNS em curto período.",
            )
