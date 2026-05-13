"""
Gerador de cenários para o capítulo de Resultados do TCC.

Executa, em ordem e com repetições configuráveis, três cenários de
ataque (A1, A2, A3) e três cenários de "ruído legítimo" (N1, N2, N3),
enviando os eventos correspondentes ao backend via API REST.

Cada evento é anotado no campo ``raw_summary`` com a tag
``benchmark=<id> truth=ATTACK|NORMAL``, o que permite ao script
``measure.py`` reclassificar TP/FP automaticamente lendo o banco.

Pré-requisitos:
  * Backend rodando em http://127.0.0.1:8000.
  * Pelo menos um ativo cadastrado com is_monitored=True.
  * Coletor não rodando em paralelo (evita poluir o experimento).
  * Banco preferencialmente vazio (rode ``flush`` antes para um run
    limpo).

Uso:
    cd benchmark
    python scenarios.py --repetitions 30

Argumentos:
    --repetitions N   Número de repetições por cenário (default: 30).
    --gap SECONDS     Pausa entre iterações; deve ser maior que a
                      janela de detecção (default: 70).
    --base-url URL    URL do backend (default: http://127.0.0.1:8000).
    --username USER   Usuário (default: admin).
    --password PASS   Senha (default: admin).
"""
from __future__ import annotations

import argparse
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Permite importar o EventFactory e o APIClient sem instalar o coletor.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "collector"))

from services.api_client import APIClient  # noqa: E402
from services.event_factory import EventFactory  # noqa: E402


def _send(api: APIClient, payload: dict, scenario_id: str,
          truth: str) -> None:
    payload = dict(payload)
    payload["raw_summary"] = (
        f"benchmark={scenario_id} truth={truth} | "
        f"{payload.get('raw_summary', '')}"
    )
    api.send_event(payload)


# ------- Cenários de ataque --------------------------------------------------

def run_a1_port_scan(api: APIClient, asset: dict,
                     scenario_id: str) -> None:
    """A1: port scan TCP em 13 portas distintas."""
    attacker_ip = EventFactory.suspicious_source_ip()
    ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 3306]
    for port in ports:
        payload = EventFactory.tcp_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
            destination_port=port,
        )
        _send(api, payload, scenario_id, "ATTACK")
        time.sleep(0.05)


def run_a2_icmp_burst(api: APIClient, asset: dict,
                      scenario_id: str, count: int = 30) -> None:
    """A2: burst ICMP — volume suficiente para superar o limiar."""
    attacker_ip = EventFactory.suspicious_source_ip()
    for _ in range(count):
        payload = EventFactory.icmp_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
        )
        _send(api, payload, scenario_id, "ATTACK")
        time.sleep(0.02)


def run_a3_dns_burst(api: APIClient, asset: dict,
                     scenario_id: str, count: int = 50) -> None:
    """A3: burst DNS — volume suficiente para superar o limiar."""
    attacker_ip = EventFactory.suspicious_source_ip()
    for _ in range(count):
        payload = EventFactory.dns_event(
            asset_id=asset["id"],
            source_ip=attacker_ip,
            destination_ip=asset["ip_address"],
        )
        _send(api, payload, scenario_id, "ATTACK")
        time.sleep(0.02)


# ------- Cenários de ruído legítimo -----------------------------------------

def run_n1_zabbix(api: APIClient, assets: list[dict],
                  scenario_id: str, count: int = 50) -> None:
    """N1: servidor de monitoramento (Zabbix/Nagios) pingando vários
    hosts da rede. Mesmo source_ip emite >20 ICMPs em curto intervalo."""
    monitor_ip = "10.0.0.50"
    for _ in range(count):
        target = random.choice(assets)
        payload = EventFactory.icmp_event(
            asset_id=target["id"],
            source_ip=monitor_ip,
            destination_ip=target["ip_address"],
        )
        _send(api, payload, scenario_id, "NORMAL")
        time.sleep(0.05)


def run_n2_inventory(api: APIClient, asset: dict,
                     scenario_id: str) -> None:
    """N2: scanner de inventário/CMDB tocando em 12 portas distintas
    (logo abaixo do limiar padrão). Em allowlist, deve ser ignorado;
    sem allowlist, gera FP do tipo PORT_SCAN_SUSPECT."""
    scanner_ip = "10.0.0.60"
    ports = [21, 22, 80, 443, 3306, 5432, 6379, 8080, 8443, 9200, 27017, 5672]
    for port in ports:
        payload = EventFactory.tcp_event(
            asset_id=asset["id"],
            source_ip=scanner_ip,
            destination_ip=asset["ip_address"],
            destination_port=port,
        )
        _send(api, payload, scenario_id, "NORMAL")
        time.sleep(0.05)


def run_n3_browsing(api: APIClient, asset: dict,
                    scenario_id: str, count: int = 40) -> None:
    """N3: navegação web ordinária — 40 resoluções DNS em curto
    intervalo. Sem mitigação, gera FP do tipo DNS_QUERY_BURST."""
    client_ip = f"10.0.0.{random.randint(100, 200)}"
    for _ in range(count):
        payload = EventFactory.dns_event(
            asset_id=asset["id"],
            source_ip=client_ip,
            destination_ip=asset["ip_address"],
        )
        _send(api, payload, scenario_id, "NORMAL")
        time.sleep(0.05)


# ------- Orquestrador -------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--gap", type=int, default=70,
                        help="Segundos entre iterações (default: 70).")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default=os.getenv("API_USERNAME", "admin"))
    parser.add_argument("--password", default=os.getenv("API_PASSWORD", "admin"))
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    print(f"[INFO] Autenticando em {args.base_url}...")
    api = APIClient(args.base_url, args.username, args.password)
    api.authenticate()

    assets = api.get_assets()
    monitored = [a for a in assets if a.get("is_monitored")]
    if not monitored:
        print("[ERRO] Cadastre ao menos um ativo monitorado antes de rodar.")
        sys.exit(1)

    print(f"[INFO] {len(monitored)} ativos monitorados encontrados.")
    print(f"[INFO] Início: {datetime.now(timezone.utc).isoformat()}")

    scenarios = [
        ("A1_PORT_SCAN", lambda i: run_a1_port_scan(
            api, random.choice(monitored), f"A1_{i:03d}")),
        ("A2_ICMP_BURST", lambda i: run_a2_icmp_burst(
            api, random.choice(monitored), f"A2_{i:03d}")),
        ("A3_DNS_BURST",  lambda i: run_a3_dns_burst(
            api, random.choice(monitored), f"A3_{i:03d}")),
        ("N1_ZABBIX",     lambda i: run_n1_zabbix(
            api, monitored, f"N1_{i:03d}")),
        ("N2_INVENTORY",  lambda i: run_n2_inventory(
            api, random.choice(monitored), f"N2_{i:03d}")),
        ("N3_BROWSING",   lambda i: run_n3_browsing(
            api, random.choice(monitored), f"N3_{i:03d}")),
    ]

    for name, fn in scenarios:
        print(f"\n=== {name} ({args.repetitions} repetições) ===")
        for i in range(args.repetitions):
            print(f"  [{name}] iteração {i + 1}/{args.repetitions}")
            try:
                fn(i)
            except Exception as error:  # noqa: BLE001
                print(f"  [ERRO] {error}")
            if i < args.repetitions - 1:
                time.sleep(args.gap)

    print(f"\n[INFO] Fim: {datetime.now(timezone.utc).isoformat()}")
    print("[INFO] Execute agora `python measure.py` para tabular as métricas.")


if __name__ == "__main__":
    main()
