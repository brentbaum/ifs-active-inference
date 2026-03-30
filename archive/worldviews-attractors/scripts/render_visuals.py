#!/usr/bin/env python3
"""Render per-run comparison visuals for survey runs."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List

import matplotlib.pyplot as plt


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def base_from_runs_path(path: Path) -> str:
    stem = path.stem
    if "_runs_" in stem:
        return stem.split("_runs_")[0]
    return stem


def compute_subscales(survey: Dict[str, Any], responses: Dict[str, Any]) -> Dict[str, float]:
    subscales = survey.get("scoring", {}).get("subscales", {})
    scores = {}
    for name, items in subscales.items():
        vals = []
        for item_id in items:
            if item_id in responses:
                vals.append(float(responses[item_id]))
        if vals:
            scores[name] = mean(vals)
    return scores


def plot_bars(title: str, scores: Dict[str, float], out_path: Path) -> None:
    labels = list(scores.keys())
    values = [scores[k] for k in labels]

    plt.figure(figsize=(8, 4.5), dpi=150)
    plt.bar(labels, values, color="#2b6cb0")
    plt.ylim(1, 7)
    plt.ylabel("Mean score")
    plt.title(title)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render visuals for survey runs.")
    parser.add_argument("--runs", type=Path, required=True, help="JSONL runs file")
    parser.add_argument("--out-dir", type=Path, default=Path("visuals"))
    parser.add_argument("--survey-dir", type=Path, default=Path("survey"))
    args = parser.parse_args()

    base = base_from_runs_path(args.runs)
    survey_path = args.survey_dir / f"{base}.json"
    if not survey_path.exists():
        raise SystemExit(f"Survey not found for {base}: {survey_path}")

    survey = load_json(survey_path)
    rows = [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]

    for row in rows:
        responses = row.get("responses")
        if not responses:
            continue
        model = safe_name(row.get("model", "unknown"))
        run_index = row.get("run_index", 0)
        scores = compute_subscales(survey, responses)
        title = f"{survey.get('dimension', base)} | {row.get('model')} | run {run_index}"
        out_path = args.out_dir / base / model / f"run_{run_index}.png"
        plot_bars(title, scores, out_path)


if __name__ == "__main__":
    main()
