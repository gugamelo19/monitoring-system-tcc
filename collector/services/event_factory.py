import random
from datetime import datetime, timezone

from config import ASSET_ID


class EventFactory:
    @staticmethod
    def base_event(protocol: str) -> dict:
        return {
            "asset": ASSET_ID,
            "source_ip": f"192.168.0.{random.randint(10, 200)}",
            "destination_ip": "192.168.0.10",
            "protocol": protocol,
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
            "collector_name": "simulator",
            "raw_summary": f"Simulated {protocol} event",
        }

    @staticmethod
    def icmp_event(source_ip: str | None = None) -> dict:
        payload = EventFactory.base_event("ICMP")
        payload.update(
            {
                "source_ip": source_ip or payload["source_ip"],
                "packet_size": random.randint(64, 128),
                "icmp_type": 8,
                "icmp_code": 0,
                "raw_summary": "ICMP Echo Request",
            }
        )
        return payload

    @staticmethod
    def tcp_event(
        source_ip: str | None = None,
        destination_port: int | None = None,
    ) -> dict:
        payload = EventFactory.base_event("TCP")
        payload.update(
            {
                "source_ip": source_ip or payload["source_ip"],
                "source_port": random.randint(20000, 65000),
                "destination_port": destination_port or random.choice([22, 80, 443, 3306, 8080]),
                "transport_layer": "L4",
                "packet_size": random.randint(60, 1500),
                "tcp_flags": "SYN",
                "raw_summary": "TCP SYN simulated event",
            }
        )
        return payload

    @staticmethod
    def dns_event(
        source_ip: str | None = None,
        dns_query: str | None = None,
    ) -> dict:
        payload = EventFactory.base_event("DNS")
        domains = [
            "example.com",
            "google.com",
            "openai.com",
            "github.com",
            "microsoft.com",
            "cloudflare.com",
        ]
        payload.update(
            {
                "source_ip": source_ip or payload["source_ip"],
                "destination_ip": "8.8.8.8",
                "source_port": random.randint(20000, 65000),
                "destination_port": 53,
                "packet_size": random.randint(70, 200),
                "dns_query": dns_query or random.choice(domains),
                "raw_summary": "DNS query simulated event",
            }
        )
        return payload
