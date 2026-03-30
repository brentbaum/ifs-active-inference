#!/usr/bin/env python3
"""Render a single heatmap across all dimensions/subscales and models."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def base_from_runs_path(path: Path) -> str:
    stem = path.stem
    if "_runs_" in stem:
        return stem.split("_runs_")[0]
    return stem


def collect_runs(results_dir: Path) -> Dict[Tuple[str, str], Path]:
    latest: Dict[Tuple[str, str], Path] = {}
    for path in results_dir.glob("*_runs_*.jsonl"):
        try:
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        models = {row.get("model") for row in rows if row.get("model")}
        if len(models) != 1:
            continue
        model = list(models)[0]
        dimension_key = base_from_runs_path(path)
        key = (dimension_key, model)
        if key not in latest or path.stat().st_mtime > latest[key].stat().st_mtime:
            latest[key] = path
    return latest


def compute_subscale_means(survey: Dict[str, Any], runs_path: Path) -> Dict[str, float]:
    subscales = survey.get("scoring", {}).get("subscales", {})
    rows = [json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    per_sub: Dict[str, List[float]] = {k: [] for k in subscales.keys()}

    for row in rows:
        responses = row.get("responses")
        if not responses:
            continue
        for name, items in subscales.items():
            vals = []
            ok = True
            for item_id in items:
                if item_id not in responses:
                    ok = False
                    break
                try:
                    vals.append(float(responses[item_id]))
                except (TypeError, ValueError):
                    ok = False
                    break
            if ok and vals:
                per_sub[name].append(mean(vals))

    means = {}
    for name, vals in per_sub.items():
        if vals:
            means[name] = mean(vals)
    return means


def main() -> None:
    parser = argparse.ArgumentParser(description="Render summary heatmap across dimensions and models.")
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--survey-dir", type=Path, default=Path("survey"))
    parser.add_argument("--out", type=Path, default=Path("visuals/summary/heatmap.png"))
    args = parser.parse_args()

    latest = collect_runs(args.results_dir)
    if not latest:
        raise SystemExit("No runs found.")

    # Map (dimension_key, model) -> subscale means
    entries: Dict[Tuple[str, str], Dict[str, float]] = {}
    dim_name_map: Dict[str, str] = {}
    subscale_labels: Dict[str, List[str]] = {}

    for (dimension_key, model), path in latest.items():
        survey_path = args.survey_dir / f"{dimension_key}.json"
        if not survey_path.exists():
            continue
        survey = load_json(survey_path)
        dim_label = survey.get("dimension", dimension_key)
        dim_name_map[dimension_key] = dim_label
        subscales = list(survey.get("scoring", {}).get("subscales", {}).keys())
        subscale_labels[dimension_key] = subscales
        means = compute_subscale_means(survey, path)
        if means:
            entries[(dimension_key, model)] = means

    models = sorted({model for (_, model) in entries.keys()})
    dimensions = sorted(subscale_labels.keys())

    # Build row labels as Dimension::subscale
    rows: List[str] = []
    row_keys: List[Tuple[str, str]] = []
    for dim in dimensions:
        for sub in subscale_labels[dim]:
            rows.append(f"{dim_name_map.get(dim, dim)}::{sub}")
            row_keys.append((dim, sub))

    matrix = np.full((len(rows), len(models)), np.nan, dtype=float)
    for r_idx, (dim, sub) in enumerate(row_keys):
        for c_idx, model in enumerate(models):
            means = entries.get((dim, model))
            if means and sub in means:
                matrix[r_idx, c_idx] = means[sub]

    # Plot
    height = max(6, len(rows) * 0.22)
    width = max(8, len(models) * 1.2)
    plt.figure(figsize=(width, height), dpi=150)
    cmap = plt.cm.viridis
    cmap.set_bad(color="#dddddd")
    im = plt.imshow(matrix, aspect="auto", vmin=1, vmax=7, cmap=cmap)
    plt.colorbar(im, label="Mean score")
    plt.yticks(range(len(rows)), rows, fontsize=7)
    plt.xticks(range(len(models)), models, rotation=30, ha="right", fontsize=8)
    plt.title("Worldview subscale means by model (latest runs)")
    plt.tight_layout()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(args.out)
    plt.close()


if __name__ == "__main__":
    main()
