import random
from datetime import datetime


class EventFactory:
    @staticmethod
    def suspicious_source_ip() -> str:
        return ".".join(
            str(part) for part in [
                random.randint(11, 223),
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(1, 254),
            ]
        )

    @staticmethod
    def icmp_event(
        asset_id: str | None = None,
        source_ip: str | None = None,
        destination_ip: str = "8.8.8.8",
    ) -> dict:
        return {
            "asset": asset_id,
            "protocol": "ICMP",
            "source_ip": source_ip or EventFactory.suspicious_source_ip(),
            "destination_ip": destination_ip,
            "source_port": None,
            "destination_port": None,
            "packet_size": random.randint(64, 128),
            "tcp_flags": "",
            "dns_query": "",
            "icmp_type": 8,
            "icmp_code": 0,
            "event_timestamp": datetime.utcnow().isoformat(),
            "raw_summary": "ICMP echo request detected",
            "collector_name": "simulator",
        }

    @staticmethod
    def tcp_event(
        asset_id: str | None = None,
        source_ip: str | None = None,
        destination_ip: str = "192.168.0.10",
        destination_port: int = 80,
    ) -> dict:
        return {
            "asset": asset_id,
            "protocol": "TCP",
            "source_ip": source_ip or EventFactory.suspicious_source_ip(),
            "destination_ip": destination_ip,
            "source_port": random.randint(1024, 65535),
            "destination_port": destination_port,
            "packet_size": random.randint(64, 1500),
            "tcp_flags": "SYN",
            "dns_query": "",
            "icmp_type": None,
            "icmp_code": None,
            "event_timestamp": datetime.utcnow().isoformat(),
            "raw_summary": f"TCP connection attempt to port {destination_port}",
            "collector_name": "simulator",
        }

    @staticmethod
    def dns_event(
        asset_id: str | None = None,
        source_ip: str | None = None,
        destination_ip: str = "8.8.8.8",
    ) -> dict:
        dns_queries = [
            "google.com",
            "openai.com",
            "github.com",
            "microsoft.com",
            "cloudflare.com",
        ]

        return {
            "asset": asset_id,
            "protocol": "DNS",
            "source_ip": source_ip or EventFactory.suspicious_source_ip(),
            "destination_ip": destination_ip,
            "source_port": random.randint(1024, 65535),
            "destination_port": 53,
            "packet_size": random.randint(64, 512),
            "tcp_flags": "",
            "dns_query": random.choice(dns_queries),
            "icmp_type": None,
            "icmp_code": None,
            "event_timestamp": datetime.utcnow().isoformat(),
            "raw_summary": "DNS query request detected",
            "collector_name": "simulator",
        }
