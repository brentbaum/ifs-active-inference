#!/usr/bin/env python3
"""Analyze Agency runs: per-item stats and reliability."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List


ITEMS = ["AG1", "AG2", "AG3", "AG4", "AG5", "AG6", "AG7", "AG8"]
VOLITION = {"AG1", "AG3", "AG5", "AG7"}
DETERMINISM = {"AG2", "AG4", "AG6", "AG8"}


def cronbach_alpha(matrix: List[List[float]]) -> float:
    if len(matrix) < 2:
        return float("nan")
    k = len(matrix[0])
    if k < 2:
        return float("nan")
    item_vars = []
    for j in range(k):
        col = [row[j] for row in matrix]
        item_vars.append(pstdev(col) ** 2)
    total_scores = [sum(row) for row in matrix]
    total_var = pstdev(total_scores) ** 2
    if total_var == 0:
        return float("nan")
    return (k / (k - 1)) * (1 - (sum(item_vars) / total_var))


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze Agency JSONL runs.")
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, default=Path("results/agency_analysis.json"))
    parser.add_argument("--out-md", type=Path, default=Path("results/agency_report.md"))
    args = parser.parse_args()

    rows = []
    for line in args.runs.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))

    responses: List[Dict[str, Any]] = [r.get("responses") for r in rows if r.get("responses")]
    if not responses:
        raise SystemExit("No responses found.")

    per_item = {}
    for item in ITEMS:
        vals = [float(r[item]) for r in responses if item in r]
        per_item[item] = {
            "n": len(vals),
            "mean": mean(vals),
            "std": pstdev(vals) if len(vals) > 1 else 0.0,
        }

    vol_matrix = [[float(r[i]) for i in ITEMS if i in VOLITION] for r in responses]
    det_matrix = [[float(r[i]) for i in ITEMS if i in DETERMINISM] for r in responses]

    summary = {
        "runs": len(responses),
        "per_item": per_item,
        "cronbach_alpha": {
            "volition": cronbach_alpha(vol_matrix),
            "determinism": cronbach_alpha(det_matrix),
        },
    }

    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Agency Analysis",
        "",
        f"Runs: {len(responses)}",
        "",
        "## Per-item stats",
        "",
    ]
    for item in ITEMS:
        s = per_item[item]
        md_lines.append(f"- {item}: mean={s['mean']:.2f}, std={s['std']:.2f} (n={s['n']})")
    md_lines += [
        "",
        "## Reliability (Cronbach's alpha)",
        "",
        f"- Volition subscale: {summary['cronbach_alpha']['volition']:.3f}",
        f"- Determinism subscale: {summary['cronbach_alpha']['determinism']:.3f}",
        "",
    ]

    args.out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
