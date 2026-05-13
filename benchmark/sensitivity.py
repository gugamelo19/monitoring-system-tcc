"""
Análise de sensibilidade dos limiares do detector.

Em vez de reexecutar o ``scenarios.py`` para cada combinação de
limiares, este script reaplica as três regras do detector
**offline**, lendo os eventos já persistidos no banco e simulando
diferentes valores de limiar. Para cada valor produz contagens de
TP/FP/FN/TN e métricas (precisão, recall, F1) cruzadas com o
``raw_summary`` que carrega ``truth=ATTACK|NORMAL``.

Resultado: três arquivos CSV (um por regra) que alimentam as tabelas
de sensibilidade do capítulo de Resultados.

Uso:
    cd benchmark
    python sensitivity.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.events.models import NetworkEvent  # noqa: E402


SUMMARY_PATTERN = re.compile(
    r"benchmark=(?P<scenario>\S+)\s+truth=(?P<truth>ATTACK|NORMAL)"
)


def _parse(raw_summary: str | None) -> tuple[str | None, str | None]:
    if not raw_summary:
        return None, None
    match = SUMMARY_PATTERN.search(raw_summary)
    if not match:
        return None, None
    return match.group("scenario"), match.group("truth")


def _load_events(protocol: str) -> list[NetworkEvent]:
    return list(
        NetworkEvent.objects
        .filter(protocol=protocol)
        .order_by("event_timestamp")
    )


def _aggregate(per_iteration: dict[str, dict]) -> dict[str, int]:
    """Aplica TP/FP/TN/FN a partir do dicionário {scenario_id: {truth, fired}}."""
    counters = {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    for data in per_iteration.values():
        truth = data["truth"]
        fired = data["fired"]
        if truth == "ATTACK" and fired:
            counters["TP"] += 1
        elif truth == "ATTACK" and not fired:
            counters["FN"] += 1
        elif truth == "NORMAL" and fired:
            counters["FP"] += 1
        elif truth == "NORMAL" and not fired:
            counters["TN"] += 1
    return counters


def _metrics(c: dict[str, int]) -> dict[str, float]:
    tp, fp, fn = c["TP"], c["FP"], c["FN"]
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    if precision and recall and (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    else:
        f1 = float("nan")
    return {"precision": precision, "recall": recall, "f1": f1}


# ----- ICMP: contagem por janela ---------------------------------------------

def simulate_icmp(threshold: int, window_seconds: int = 30) -> dict:
    events = _load_events("ICMP")
    per_iteration: dict[str, dict] = {}

    # Indexa eventos por scenario_id para identificar iterações.
    for ev in events:
        sid, truth = _parse(ev.raw_summary)
        if not sid:
            continue
        per_iteration.setdefault(sid, {"truth": truth, "fired": False})

    # Para cada evento ICMP, conta no window-back e marca fired se
    # ultrapassa limiar.
    for ev in events:
        sid, _ = _parse(ev.raw_summary)
        if not sid or per_iteration[sid]["fired"]:
            continue
        window_start = ev.event_timestamp - timedelta(seconds=window_seconds)
        count = sum(
            1 for e in events
            if e.source_ip == ev.source_ip
            and window_start <= e.event_timestamp <= ev.event_timestamp
        )
        if count > threshold:
            per_iteration[sid]["fired"] = True

    counters = _aggregate(per_iteration)
    return {"threshold": threshold, **counters, **_metrics(counters)}


# ----- TCP: portas distintas por janela --------------------------------------

def simulate_port_scan(threshold: int, window_seconds: int = 60) -> dict:
    events = _load_events("TCP")
    per_iteration: dict[str, dict] = {}

    for ev in events:
        sid, truth = _parse(ev.raw_summary)
        if not sid:
            continue
        per_iteration.setdefault(sid, {"truth": truth, "fired": False})

    for ev in events:
        sid, _ = _parse(ev.raw_summary)
        if not sid or per_iteration[sid]["fired"]:
            continue
        if ev.destination_port is None:
            continue
        window_start = ev.event_timestamp - timedelta(seconds=window_seconds)
        ports = {
            e.destination_port for e in events
            if e.source_ip == ev.source_ip
            and e.destination_port is not None
            and window_start <= e.event_timestamp <= ev.event_timestamp
        }
        if len(ports) > threshold:
            per_iteration[sid]["fired"] = True

    counters = _aggregate(per_iteration)
    return {"threshold": threshold, **counters, **_metrics(counters)}


# ----- DNS: contagem por janela ----------------------------------------------

def simulate_dns(threshold: int, window_seconds: int = 60) -> dict:
    events = _load_events("DNS")
    per_iteration: dict[str, dict] = {}

    for ev in events:
        sid, truth = _parse(ev.raw_summary)
        if not sid:
            continue
        per_iteration.setdefault(sid, {"truth": truth, "fired": False})

    for ev in events:
        sid, _ = _parse(ev.raw_summary)
        if not sid or per_iteration[sid]["fired"]:
            continue
        window_start = ev.event_timestamp - timedelta(seconds=window_seconds)
        count = sum(
            1 for e in events
            if e.source_ip == ev.source_ip
            and window_start <= e.event_timestamp <= ev.event_timestamp
        )
        if count > threshold:
            per_iteration[sid]["fired"] = True

    counters = _aggregate(per_iteration)
    return {"threshold": threshold, **counters, **_metrics(counters)}


# ----- orquestrador ----------------------------------------------------------

def _write_csv(rows: list[dict], filename: str) -> None:
    out = Path(__file__).resolve().parent / filename
    with out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[OK] {out}")


def main() -> None:
    print("\n--- HIGH_ICMP_RATE ---")
    icmp_rows = [simulate_icmp(t) for t in (5, 10, 15, 20, 25, 30, 35, 40)]
    for r in icmp_rows:
        print(r)
    _write_csv(icmp_rows, "sensitivity_icmp.csv")

    print("\n--- PORT_SCAN_SUSPECT ---")
    tcp_rows = [simulate_port_scan(t) for t in (5, 8, 10, 11, 12, 13, 15, 20)]
    for r in tcp_rows:
        print(r)
    _write_csv(tcp_rows, "sensitivity_port_scan.csv")

    print("\n--- DNS_QUERY_BURST ---")
    dns_rows = [simulate_dns(t) for t in (10, 20, 30, 35, 40, 50, 60)]
    for r in dns_rows:
        print(r)
    _write_csv(dns_rows, "sensitivity_dns.csv")


if __name__ == "__main__":
    main()
