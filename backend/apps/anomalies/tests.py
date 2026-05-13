"""
Testes unitários do AnomalyDetectorService.

Cobertura:
- Disparo de cada uma das três regras (HIGH_ICMP_RATE,
  PORT_SCAN_SUSPECT, DNS_QUERY_BURST) acima do limiar.
- Não-disparo quando o volume está abaixo do limiar.
- Supressão por TrustedSource (allowlist).
- Supressão por FalsePositiveFeedback ativo.
- Deduplicação dentro da janela configurada.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.alerts.models import Alert
from apps.anomalies.models import (
    Anomaly,
    FalsePositiveFeedback,
    TrustedSource,
)
from apps.anomalies.services.detector import AnomalyDetectorService
from apps.assets.models import Asset
from apps.events.models import NetworkEvent


class DetectorTestCase(TestCase):
    """
    Base class com utilitários compartilhados pelos testes.
    Cria um ativo e expõe helpers para sintetizar eventos.
    """

    def setUp(self) -> None:
        self.asset = Asset.objects.create(
            name="Servidor Teste",
            ip_address="192.168.0.10",
            asset_type=Asset.AssetType.SERVER,
            status=Asset.AssetStatus.ONLINE,
            is_monitored=True,
        )
        self.attacker_ip = "203.0.113.50"

    def _make_icmp(self, source_ip: str, when=None) -> NetworkEvent:
        return NetworkEvent.objects.create(
            asset=self.asset,
            protocol="ICMP",
            source_ip=source_ip,
            destination_ip=self.asset.ip_address,
            icmp_type=8,
            icmp_code=0,
            event_timestamp=when or timezone.now(),
            raw_summary="ICMP echo request",
            collector_name="test",
        )

    def _make_tcp(self, source_ip: str, port: int,
                  when=None) -> NetworkEvent:
        return NetworkEvent.objects.create(
            asset=self.asset,
            protocol="TCP",
            source_ip=source_ip,
            destination_ip=self.asset.ip_address,
            source_port=49152,
            destination_port=port,
            tcp_flags="SYN",
            event_timestamp=when or timezone.now(),
            raw_summary=f"TCP attempt to port {port}",
            collector_name="test",
        )

    def _make_dns(self, source_ip: str, when=None) -> NetworkEvent:
        return NetworkEvent.objects.create(
            asset=self.asset,
            protocol="DNS",
            source_ip=source_ip,
            destination_ip=self.asset.ip_address,
            destination_port=53,
            dns_query="exemplo.com",
            event_timestamp=when or timezone.now(),
            raw_summary="DNS query",
            collector_name="test",
        )


class IcmpRuleTests(DetectorTestCase):
    def test_dispara_quando_acima_do_limiar(self):
        for _ in range(21):
            self._make_icmp(self.attacker_ip)
        # O último evento dispara a análise (count > 20).
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        anomalias = Anomaly.objects.filter(anomaly_type="HIGH_ICMP_RATE")
        self.assertEqual(anomalias.count(), 1)
        self.assertEqual(anomalias.first().severity,
                         Anomaly.SeverityLevel.MEDIUM)
        # Alerta correspondente foi criado.
        self.assertEqual(
            Alert.objects.filter(anomaly__anomaly_type="HIGH_ICMP_RATE").count(),
            1,
        )

    def test_nao_dispara_abaixo_do_limiar(self):
        # 15 eventos < limiar de 20.
        for _ in range(14):
            self._make_icmp(self.attacker_ip)
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertFalse(
            Anomaly.objects.filter(anomaly_type="HIGH_ICMP_RATE").exists()
        )


class PortScanRuleTests(DetectorTestCase):
    def test_dispara_com_mais_de_dez_portas_distintas(self):
        portas = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443]  # 11
        for port in portas:
            self._make_tcp(self.attacker_ip, port)
        last = self._make_tcp(self.attacker_ip, 445)
        AnomalyDetectorService.analyze_event(last)

        self.assertEqual(
            Anomaly.objects.filter(anomaly_type="PORT_SCAN_SUSPECT").count(),
            1,
        )

    def test_nao_dispara_com_poucas_portas(self):
        for port in [80, 443]:
            self._make_tcp(self.attacker_ip, port)
        last = self._make_tcp(self.attacker_ip, 8080)
        AnomalyDetectorService.analyze_event(last)

        self.assertFalse(
            Anomaly.objects.filter(anomaly_type="PORT_SCAN_SUSPECT").exists()
        )

    def test_nao_dispara_se_muitos_eventos_na_mesma_porta(self):
        # 30 eventos, todos na mesma porta -> 1 porta distinta.
        for _ in range(30):
            self._make_tcp(self.attacker_ip, 22)
        last = self._make_tcp(self.attacker_ip, 22)
        AnomalyDetectorService.analyze_event(last)

        self.assertFalse(
            Anomaly.objects.filter(anomaly_type="PORT_SCAN_SUSPECT").exists()
        )


class DnsBurstRuleTests(DetectorTestCase):
    def test_dispara_acima_de_trinta_consultas(self):
        for _ in range(31):
            self._make_dns(self.attacker_ip)
        last = self._make_dns(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertEqual(
            Anomaly.objects.filter(anomaly_type="DNS_QUERY_BURST").count(),
            1,
        )

    def test_nao_dispara_em_consultas_normais(self):
        for _ in range(10):
            self._make_dns(self.attacker_ip)
        last = self._make_dns(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertFalse(
            Anomaly.objects.filter(anomaly_type="DNS_QUERY_BURST").exists()
        )


class TrustedSourceTests(DetectorTestCase):
    def test_allowlist_suprime_qualquer_anomalia(self):
        TrustedSource.objects.create(
            ip_address=self.attacker_ip,
            description="Servidor de monitoramento Zabbix",
            is_active=True,
        )

        # Volume suficiente para disparar a regra ICMP.
        for _ in range(25):
            self._make_icmp(self.attacker_ip)
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertEqual(Anomaly.objects.count(), 0)
        self.assertEqual(Alert.objects.count(), 0)

    def test_allowlist_inativa_nao_suprime(self):
        TrustedSource.objects.create(
            ip_address=self.attacker_ip,
            is_active=False,
        )

        for _ in range(21):
            self._make_icmp(self.attacker_ip)
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertEqual(Anomaly.objects.count(), 1)


class FalsePositiveFeedbackTests(DetectorTestCase):
    def test_feedback_ativo_suprime_anomalia(self):
        FalsePositiveFeedback.objects.create(
            source_ip=self.attacker_ip,
            anomaly_type="HIGH_ICMP_RATE",
            suppress_until=timezone.now() + timedelta(hours=24),
        )

        for _ in range(25):
            self._make_icmp(self.attacker_ip)
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertFalse(
            Anomaly.objects.filter(anomaly_type="HIGH_ICMP_RATE").exists()
        )

    def test_feedback_expirado_nao_suprime(self):
        FalsePositiveFeedback.objects.create(
            source_ip=self.attacker_ip,
            anomaly_type="HIGH_ICMP_RATE",
            suppress_until=timezone.now() - timedelta(hours=1),
        )

        for _ in range(21):
            self._make_icmp(self.attacker_ip)
        last = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(last)

        self.assertTrue(
            Anomaly.objects.filter(anomaly_type="HIGH_ICMP_RATE").exists()
        )


class DeduplicationTests(DetectorTestCase):
    def test_duas_chamadas_dentro_da_janela_geram_uma_anomalia(self):
        for _ in range(25):
            self._make_icmp(self.attacker_ip)
        first = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(first)

        # Mais eventos e segunda chamada dentro de 60s.
        for _ in range(5):
            self._make_icmp(self.attacker_ip)
        second = self._make_icmp(self.attacker_ip)
        AnomalyDetectorService.analyze_event(second)

        self.assertEqual(
            Anomaly.objects.filter(anomaly_type="HIGH_ICMP_RATE").count(),
            1,
        )
