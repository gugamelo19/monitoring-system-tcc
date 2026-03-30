import random
import time

from services.event_factory import EventFactory


class EventSimulator:
    def __init__(self, api_client):
        self.api_client = api_client

    def send_normal_traffic(self, total: int = 20) -> None:
        print(f"\n[INFO] Enviando {total} eventos de tráfego normal...")
        generators = [
            EventFactory.icmp_event,
            EventFactory.tcp_event,
            EventFactory.dns_event,
        ]

        for index in range(total):
            payload = random.choice(generators)()
            response = self.api_client.send_event(payload)
            print(
                f"[NORMAL] Evento {index + 1}/{total} enviado: {response['message']}")
            time.sleep(0.2)

    def simulate_icmp_burst(self, source_ip: str = "192.168.0.250", total: int = 25) -> None:
        print(f"\n[INFO] Simulando burst ICMP com {total} eventos...")
        for index in range(total):
            payload = EventFactory.icmp_event(source_ip=source_ip)
            response = self.api_client.send_event(payload)
            print(
                f"[ICMP BURST] Evento {index + 1}/{total} enviado: {response['message']}")
            time.sleep(0.05)

    def simulate_port_scan(self, source_ip: str = "192.168.0.251") -> None:
        print("\n[INFO] Simulando port scan TCP...")
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306]
        for index, port in enumerate(ports, start=1):
            payload = EventFactory.tcp_event(
                source_ip=source_ip, destination_port=port)
            response = self.api_client.send_event(payload)
            print(
                f"[PORT SCAN] Porta {port} ({index}/{len(ports)}) enviada: {response['message']}")
            time.sleep(0.05)

    def simulate_dns_burst(self, source_ip: str = "192.168.0.252", total: int = 35) -> None:
        print(f"\n[INFO] Simulando burst DNS com {total} eventos...")
        for index in range(total):
            payload = EventFactory.dns_event(source_ip=source_ip)
            response = self.api_client.send_event(payload)
            print(
                f"[DNS BURST] Evento {index + 1}/{total} enviado: {response['message']}")
            time.sleep(0.05)
