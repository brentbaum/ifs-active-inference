#!/usr/bin/env python3
"""Analyze survey runs: per-item stats and subscale reliability."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    parser = argparse.ArgumentParser(description="Analyze survey JSONL runs.")
    parser.add_argument("--items", type=Path, required=True)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--out-json", type=Path, required=True)
    parser.add_argument("--out-md", type=Path, required=True)
    args = parser.parse_args()

    survey = load_json(args.items)
    items = survey.get("items", [])
    scoring = survey.get("scoring")
    if not scoring:
        raise SystemExit("Survey missing 'scoring' metadata")

    rows = [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]
    responses_list = [r.get("responses") for r in rows if r.get("responses")]
    if not responses_list:
        raise SystemExit("No responses found.")

    per_item = {}
    for item in items:
        item_id = item["id"]
        vals = [float(r[item_id]) for r in responses_list if item_id in r]
        per_item[item_id] = {
            "n": len(vals),
            "mean": mean(vals),
            "std": pstdev(vals) if len(vals) > 1 else 0.0,
        }

    subscales = scoring.get("subscales", {})
    alphas = {}
    for name, item_ids in subscales.items():
        matrix = [[float(r[i]) for i in item_ids if i in r] for r in responses_list]
        # ensure same length
        matrix = [row for row in matrix if len(row) == len(item_ids)]
        alphas[name] = cronbach_alpha(matrix)

    summary = {
        "runs": len(responses_list),
        "per_item": per_item,
        "cronbach_alpha": alphas,
    }

    args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        f"# {survey.get('dimension', 'Survey')} Analysis",
        "",
        f"Runs: {len(responses_list)}",
        "",
        "## Per-item stats",
        "",
    ]
    for item in items:
        item_id = item["id"]
        s = per_item[item_id]
        md_lines.append(f"- {item_id}: mean={s['mean']:.2f}, std={s['std']:.2f} (n={s['n']})")
    md_lines += [
        "",
        "## Reliability (Cronbach's alpha)",
        "",
    ]
    for name, alpha in alphas.items():
        md_lines.append(f"- {name}: {alpha:.3f}")
    md_lines.append("")

    args.out_md.write_text("\n".join(md_lines), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
