"""
Mede acurácia do detector a partir das tags ``benchmark=<id>
truth=<ATTACK|NORMAL>`` gravadas em ``raw_summary`` pelos eventos
gerados por ``scenarios.py``.

Para cada cenário, calcula:
  * TP  — anomalia gerada quando o cenário é ATTACK.
  * FP  — anomalia gerada quando o cenário é NORMAL.
  * FN  — cenário ATTACK sem anomalia gerada.
  * TN  — cenário NORMAL sem anomalia gerada.
  * Precisão, Recall, F1.

Saída:
  * Tabela formatada no stdout.
  * Arquivo CSV ``metrics_summary.csv`` na pasta atual.

Uso:
    cd benchmark
    python measure.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.anomalies.models import Anomaly  # noqa: E402
from apps.events.models import NetworkEvent  # noqa: E402


SUMMARY_PATTERN = re.compile(
    r"benchmark=(?P<scenario>\S+)\s+truth=(?P<truth>ATTACK|NORMAL)"
)


def _parse_summary(raw_summary: str | None) -> tuple[str | None, str | None]:
    if not raw_summary:
        return None, None
    match = SUMMARY_PATTERN.search(raw_summary)
    if not match:
        return None, None
    return match.group("scenario"), match.group("truth")


def _scenario_prefix(scenario_id: str) -> str:
    # "A1_PORT_SCAN_007" -> "A1_PORT_SCAN"
    return "_".join(scenario_id.split("_")[:-1]) or scenario_id


def measure() -> list[dict]:
    """
    Conta, por prefixo de cenário, quantas iterações geraram (pelo
    menos uma) anomalia e quantas não geraram. Cada iteração é
    identificada pelo ``scenario_id`` único gravado no raw_summary.
    """
    # Mapeia scenario_id -> (truth, gerou_anomalia)
    iterations: dict[str, dict] = {}

    # 1) Lista todas as iterações vistas em eventos.
    for ev in NetworkEvent.objects.iterator():
        scenario_id, truth = _parse_summary(ev.raw_summary)
        if not scenario_id:
            continue
        iterations.setdefault(scenario_id,
                              {"truth": truth, "had_anomaly": False})

    # 2) Para cada anomalia gerada, marca a iteração correspondente.
    for an in Anomaly.objects.select_related("event").iterator():
        scenario_id, _ = _parse_summary(an.event.raw_summary if an.event else "")
        if scenario_id and scenario_id in iterations:
            iterations[scenario_id]["had_anomaly"] = True

    # 3) Agrega por prefixo de cenário.
    aggregated: dict[str, dict] = defaultdict(
        lambda: {"TP": 0, "FP": 0, "TN": 0, "FN": 0}
    )
    for sid, data in iterations.items():
        prefix = _scenario_prefix(sid)
        truth = data["truth"]
        had_anomaly = data["had_anomaly"]
        if truth == "ATTACK" and had_anomaly:
            aggregated[prefix]["TP"] += 1
        elif truth == "ATTACK" and not had_anomaly:
            aggregated[prefix]["FN"] += 1
        elif truth == "NORMAL" and had_anomaly:
            aggregated[prefix]["FP"] += 1
        elif truth == "NORMAL" and not had_anomaly:
            aggregated[prefix]["TN"] += 1

    # 4) Calcula métricas e prepara linhas.
    rows = []
    for name in sorted(aggregated.keys()):
        c = aggregated[name]
        tp, fp, tn, fn = c["TP"], c["FP"], c["TN"], c["FN"]
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        if precision and recall and (precision + recall) > 0:
            f1 = 2 * precision * recall / (precision + recall)
        else:
            f1 = float("nan")
        rows.append({
            "scenario": name,
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
    return rows


def _fmt(v) -> str:
    if isinstance(v, float):
        if v != v:  # NaN
            return "  -  "
        return f"{v:.3f}"
    return str(v)


def main() -> None:
    rows = measure()

    if not rows:
        print("[AVISO] Nenhuma iteração de benchmark encontrada no banco.")
        print("        Rode scenarios.py antes.")
        return

    headers = ["scenario", "TP", "FP", "TN", "FN",
               "precision", "recall", "f1"]
    widths = {h: max(len(h), max(len(_fmt(r[h])) for r in rows))
              for h in headers}

    line = " | ".join(h.ljust(widths[h]) for h in headers)
    print(line)
    print("-+-".join("-" * widths[h] for h in headers))
    for r in rows:
        print(" | ".join(_fmt(r[h]).ljust(widths[h]) for h in headers))

    out_path = Path(__file__).resolve().parent / "metrics_summary.csv"
    with out_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Métricas salvas em {out_path}")


if __name__ == "__main__":
    main()
