#!/usr/bin/env python3
"""Score Moral Standard responses from JSONL runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional


ABSOLUTE = {"MS1", "MS3", "MS5", "MS7"}
RELATIVE = {"MS2", "MS4", "MS6", "MS8"}


def score_run(responses: Dict[str, Any]) -> Optional[Dict[str, float]]:
    if not responses:
        return None
    try:
        abs_vals = [float(responses[k]) for k in ABSOLUTE if k in responses]
        rel_vals = [float(responses[k]) for k in RELATIVE if k in responses]
    except (TypeError, ValueError):
        return None
    if not abs_vals or not rel_vals:
        return None
    abs_mean = mean(abs_vals)
    rel_mean = mean(rel_vals)
    return {
        "absolute_mean": abs_mean,
        "relative_mean": rel_mean,
        "net_score": abs_mean - rel_mean,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Moral Standard JSONL runs.")
    parser.add_argument("--runs", type=Path, default=Path("results/moral_standard_runs.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("results/moral_standard_summary.json"))
    args = parser.parse_args()

    rows: List[Dict[str, Any]] = []
    for line in args.runs.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))

    scored = []
    for row in rows:
        s = score_run(row.get("responses"))
        if s:
            scored.append({"run_id": row.get("run_id"), **s})

    if not scored:
        raise SystemExit("No scored runs found.")

    summary = {
        "runs": len(scored),
        "absolute_mean": mean([r["absolute_mean"] for r in scored]),
        "relative_mean": mean([r["relative_mean"] for r in scored]),
        "net_score": mean([r["net_score"] for r in scored]),
    }

    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
