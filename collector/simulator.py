import random
import time

from services.event_factory import EventFactory


class EventSimulator:
    def __init__(self, api_client):
        self.api_client = api_client

    @staticmethod
    def describe_event_response(response: dict) -> str:
        event_id = response.get("id")
        protocol = response.get("protocol", "UNKNOWN")
        asset_name = response.get("asset_name")

        details = [f"id={event_id}" if event_id is not None else None,
                   f"protocol={protocol}"]
        if asset_name:
            details.append(f"asset={asset_name}")

        return ", ".join(part for part in details if part)

    def get_monitored_assets(self) -> list[dict]:
        assets = self.api_client.get_assets()
        monitored_assets = [
            asset for asset in assets if asset.get("is_monitored", False)
        ]
        return monitored_assets

    def send_normal_traffic(self, total: int = 20) -> None:
        print(f"\n[INFO] Enviando {total} eventos de tráfego normal...")

        assets = self.get_monitored_assets()
        if not assets:
            print("[WARN] Nenhum ativo monitorado encontrado.")
            return

        generators = [
            EventFactory.icmp_event,
            EventFactory.tcp_event,
            EventFactory.dns_event,
        ]

        for index in range(total):
            asset = random.choice(assets)
            generator = random.choice(generators)

            payload = generator(
                asset_id=asset["id"],
                destination_ip=asset["ip_address"],
            )

            response = self.api_client.send_event(payload)
            print(
                f"[NORMAL] Evento {index + 1}/{total} enviado para "
                f"{asset['name']} ({asset['ip_address']}): "
                f"{self.describe_event_response(response)}"
            )
            time.sleep(0.2)

    def monitor_assets_once(self) -> None:
        assets = self.get_monitored_assets()

        if not assets:
            print("[WARN] Nenhum ativo monitorado encontrado.")
            return

        print(f"\n[INFO] Monitorando {len(assets)} ativos cadastrados...")

        for asset in assets:
            payload = EventFactory.icmp_event(
                asset_id=asset["id"],
                destination_ip=asset["ip_address"],
            )
            response = self.api_client.send_event(payload)
            print(
                f"[MONITOR] Ativo {asset['name']} "
                f"({asset['ip_address']}) -> "
                f"{self.describe_event_response(response)}"
            )
            time.sleep(0.2)

    def simulate_icmp_burst(
        self,
        total: int = 25,
        target_asset: dict | None = None,
    ) -> None:
        assets = self.get_monitored_assets()

        if not assets:
            print("[WARN] Nenhum ativo monitorado encontrado.")
            return

        asset = target_asset or random.choice(assets)

        print(
            f"\n[INFO] Simulando burst ICMP com {total} eventos "
            f"no ativo {asset['name']} ({asset['ip_address']})..."
        )

        attacker_ip = EventFactory.suspicious_source_ip()

        for index in range(total):
            payload = EventFactory.icmp_event(
                asset_id=asset["id"],
                source_ip=attacker_ip,
                destination_ip=asset["ip_address"],
            )
            response = self.api_client.send_event(payload)
            print(
                f"[ICMP BURST] Evento {index + 1}/{total} enviado para "
                f"{asset['name']}: {self.describe_event_response(response)}"
            )
            time.sleep(0.05)

    def simulate_port_scan(self, target_asset: dict | None = None) -> None:
        assets = self.get_monitored_assets()

        if not assets:
            print("[WARN] Nenhum ativo monitorado encontrado.")
            return

        asset = target_asset or random.choice(assets)

        print(
            f"\n[INFO] Simulando port scan TCP no ativo "
            f"{asset['name']} ({asset['ip_address']})..."
        )

        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306]
        attacker_ip = EventFactory.suspicious_source_ip()

        for index, port in enumerate(ports, start=1):
            payload = EventFactory.tcp_event(
                asset_id=asset["id"],
                source_ip=attacker_ip,
                destination_ip=asset["ip_address"],
                destination_port=port,
            )
            response = self.api_client.send_event(payload)
            print(
                f"[PORT SCAN] Porta {port} ({index}/{len(ports)}) enviada para "
                f"{asset['name']}: {self.describe_event_response(response)}"
            )
            time.sleep(0.05)

    def simulate_dns_burst(
        self,
        total: int = 35,
        target_asset: dict | None = None,
    ) -> None:
        assets = self.get_monitored_assets()

        if not assets:
            print("[WARN] Nenhum ativo monitorado encontrado.")
            return

        asset = target_asset or random.choice(assets)

        print(
            f"\n[INFO] Simulando burst DNS com {total} eventos "
            f"no ativo {asset['name']} ({asset['ip_address']})..."
        )

        attacker_ip = EventFactory.suspicious_source_ip()

        for index in range(total):
            payload = EventFactory.dns_event(
                asset_id=asset["id"],
                source_ip=attacker_ip,
                destination_ip=asset["ip_address"],
            )
            response = self.api_client.send_event(payload)
            print(
                f"[DNS BURST] Evento {index + 1}/{total} enviado para "
                f"{asset['name']}: {self.describe_event_response(response)}"
            )
            time.sleep(0.05)

    def run_realtime_monitoring(self, interval: int = 5) -> None:
        print("\n[INFO] Iniciando monitoramento contínuo em tempo real...")

        while True:
            self.monitor_assets_once()

            if random.random() < 0.3:
                self.simulate_icmp_burst(total=25)

            if random.random() < 0.2:
                self.simulate_port_scan()

            if random.random() < 0.2:
                self.simulate_dns_burst(total=35)

            print(f"[INFO] Aguardando {interval} segundos para novo ciclo...")
            time.sleep(interval)
