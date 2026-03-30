#!/usr/bin/env python3
"""Score a survey JSONL file using the survey's scoring metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def mean_for_items(responses: Dict[str, Any], items: List[str]) -> Optional[float]:
    """Compute mean for Likert items (numeric responses)."""
    vals = []
    for k in items:
        if k in responses:
            try:
                vals.append(float(responses[k]))
            except (TypeError, ValueError):
                return None
    if not vals:
        return None
    return mean(vals)


def score_mc_responses(
    responses: Dict[str, Any],
    questions: Dict[str, Dict[str, Any]],
    item_ids: List[str],
) -> Optional[float]:
    """Score MC responses by mapping letters to numeric scores and averaging.

    Args:
        responses: {"HN-MO-1": "A", "HN-MO-2": "C", ...}
        questions: {"HN-MO-1": {"A": 2, "B": 1, ...}, ...}
        item_ids: List of item IDs to score

    Returns:
        Mean of mapped scores, or None if any response is missing/invalid.
    """
    vals = []
    for item_id in item_ids:
        if item_id not in responses:
            return None
        letter = responses[item_id]
        if item_id not in questions:
            return None
        mapping = questions[item_id]
        if letter not in mapping:
            return None
        score = mapping[letter]
        # Handle numeric scores
        if isinstance(score, (int, float)):
            vals.append(float(score))
        # Skip categorical (string) scores for mean calculation
        elif isinstance(score, str):
            continue
    if not vals:
        return None
    return mean(vals)


def get_mc_categories(
    responses: Dict[str, Any],
    questions: Dict[str, Dict[str, Any]],
    item_ids: List[str],
) -> Optional[List[str]]:
    """Get categorical MC responses (for non-numeric dimensions).

    Returns list of category labels for each item.
    """
    categories = []
    for item_id in item_ids:
        if item_id not in responses:
            return None
        letter = responses[item_id]
        if item_id not in questions:
            return None
        mapping = questions[item_id]
        if letter not in mapping:
            return None
        categories.append(mapping[letter])
    return categories


def summarize_categories(categories_per_run: List[List[str]]) -> Dict[str, Any]:
    # AIDEV-NOTE: Categorical MC dimensions are summarized as distributions, not forced numeric means.
    counts: Dict[str, int] = {}
    for categories in categories_per_run:
        for category in categories:
            if not isinstance(category, str):
                continue
            counts[category] = counts.get(category, 0) + 1

    total = sum(counts.values())
    if total == 0:
        return {
            "category_counts": {},
            "category_total": 0,
            "category_distribution": {},
            "category_mode": None,
            "category_mode_share": None,
        }

    sorted_counts = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    distribution = {k: v / total for k, v in sorted_counts.items()}
    mode = next(iter(sorted_counts))
    mode_share = distribution[mode]

    return {
        "category_counts": sorted_counts,
        "category_total": total,
        "category_distribution": distribution,
        "category_mode": mode,
        "category_mode_share": mode_share,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Score survey JSONL runs.")
    parser.add_argument("--items", type=Path, required=True, help="Survey JSON file")
    parser.add_argument("--runs", type=Path, required=True, help="JSONL runs file")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    survey = load_json(args.items)
    scoring = survey.get("scoring")
    if not scoring:
        raise SystemExit("Survey missing 'scoring' metadata")

    rows = [json.loads(line) for line in args.runs.read_text(encoding="utf-8").splitlines() if line.strip()]
    responses_list = [r.get("responses") for r in rows if r.get("responses")]
    if not responses_list:
        raise SystemExit("No responses found.")

    # Detect format: MC has "mode": "choice" and "questions" mapping
    is_mc = scoring.get("mode") == "choice"
    is_categorical = is_mc and scoring.get("type") == "categorical"
    questions_mapping = scoring.get("questions", {})

    subscales = scoring.get("subscales", {})
    per_run = []
    categories_per_run: List[List[str]] = []

    for responses in responses_list:
        run_scores = {}

        if is_categorical:
            all_items = list(questions_mapping.keys())
            categories = get_mc_categories(responses, questions_mapping, all_items)
            if categories is not None:
                categories_per_run.append(categories)
            continue

        if is_mc:
            # MC format: map letter responses to scores
            # For MC, subscales may not exist; use all questions
            if subscales:
                for name, item_ids in subscales.items():
                    m = score_mc_responses(responses, questions_mapping, item_ids)
                    if m is None:
                        break
                    run_scores[name] = m
                else:
                    per_run.append(run_scores)
            else:
                # No subscales: score all questions as one dimension
                all_items = list(questions_mapping.keys())
                m = score_mc_responses(responses, questions_mapping, all_items)
                if m is not None:
                    run_scores["dimension"] = m
                    per_run.append(run_scores)
        else:
            # Likert format: average numeric responses
            for name, items in subscales.items():
                m = mean_for_items(responses, items)
                if m is None:
                    break
                run_scores[name] = m
            else:
                per_run.append(run_scores)

    if is_categorical and not categories_per_run:
        raise SystemExit("No scored runs found.")
    if not is_categorical and not per_run:
        raise SystemExit("No scored runs found.")

    summary = {
        "runs": len(categories_per_run) if is_categorical else len(per_run),
        "format": "mc" if is_mc else "likert",
    }

    if is_categorical:
        summary.update(summarize_categories(categories_per_run))
    elif is_mc and not subscales:
        # Single dimension MC
        summary["dimension_mean"] = mean([r["dimension"] for r in per_run])
    else:
        for name in subscales.keys():
            summary[f"{name}_mean"] = mean([r[name] for r in per_run])

    if scoring.get("type") == "bipolar":
        pos = scoring.get("positive")
        neg = scoring.get("negative")
        if pos in subscales and neg in subscales:
            summary["net_score"] = summary[f"{pos}_mean"] - summary[f"{neg}_mean"]

    args.out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
