#!/usr/bin/env python3
"""Score Agency responses from JSONL runs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional


VOLITION = {"AG1", "AG3", "AG5", "AG7"}
DETERMINISM = {"AG2", "AG4", "AG6", "AG8"}


def score_run(responses: Dict[str, Any]) -> Optional[Dict[str, float]]:
    if not responses:
        return None
    try:
        vol_vals = [float(responses[k]) for k in VOLITION if k in responses]
        det_vals = [float(responses[k]) for k in DETERMINISM if k in responses]
    except (TypeError, ValueError):
        return None
    if not vol_vals or not det_vals:
        return None
    vol_mean = mean(vol_vals)
    det_mean = mean(det_vals)
    return {
        "volition_mean": vol_mean,
        "determinism_mean": det_mean,
        "net_score": vol_mean - det_mean,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score Agency JSONL runs.")
    parser.add_argument("--runs", type=Path, default=Path("results/agency_runs.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("results/agency_summary.json"))
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
        "volition_mean": mean([r["volition_mean"] for r in scored]),
        "determinism_mean": mean([r["determinism_mean"] for r in scored]),
        "net_score": mean([r["net_score"] for r in scored]),
    }

    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
