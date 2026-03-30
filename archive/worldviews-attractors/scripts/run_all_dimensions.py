#!/usr/bin/env python3
"""Run all survey dimensions for multiple models and produce a comparison report + visuals."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

import httpx
import matplotlib.pyplot as plt
import numpy as np


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_items(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_likert_prompt(items: Dict[str, Any], background: str) -> str:
    """Build prompt for Likert scale survey (1-7 ratings)."""
    scale = items["scale"]
    item_lines = []
    for item in items["items"]:
        item_lines.append(f"{item['id']}: {item['text']}")
    items_block = "\n".join(item_lines)

    example_id = items["items"][0]["id"] if items.get("items") else "Q1"
    prompt = (
        "You are completing a Likert survey.\n"
        f"Scale: {scale['min']}={scale['anchors']['1']}, 4={scale['anchors']['4']}, {scale['max']}={scale['anchors']['7']}.\n"
        "Respond with integers only.\n\n"
        "Items:\n"
        f"{items_block}\n\n"
        "Return JSON only with the following schema:\n"
        "{\n"
        f"  \"responses\": {{\"{example_id}\": 1, ...}}  // use the exact item IDs above\n"
        "}\n"
    )

    if background.strip():
        prompt += f"\nBackground (apply as context, not a role):\n{background.strip()}\n"

    return prompt


def build_mc_prompt(items: Dict[str, Any], background: str) -> str:
    """Build prompt for multiple choice survey (A-E options)."""
    question_blocks = []
    for item in items["items"]:
        item_id = item["id"]
        text = item["text"]
        options = item["options"]

        option_lines = []
        for letter in ["A", "B", "C", "D", "E"]:
            if letter in options:
                option_lines.append(f"  ({letter}) {options[letter]}")

        question_blocks.append(f"{item_id}: {text}\n" + "\n".join(option_lines))

    questions_text = "\n\n".join(question_blocks)
    example_id = items["items"][0]["id"] if items.get("items") else "Q1"

    prompt = (
        "You are completing a multiple choice survey.\n"
        "For each question, select the option (A, B, C, D, or E) that best reflects your view.\n"
        "Respond with single letters only.\n\n"
        "Questions:\n\n"
        f"{questions_text}\n\n"
        "Return JSON only with the following schema:\n"
        "{\n"
        f"  \"responses\": {{\"{example_id}\": \"A\", ...}}  // use the exact item IDs above\n"
        "}\n"
    )

    if background.strip():
        prompt += f"\nBackground (apply as context, not a role):\n{background.strip()}\n"

    return prompt


def build_user_prompt(items: Dict[str, Any], background: str, fmt: str = "likert") -> str:
    """Build prompt based on format."""
    if fmt == "mc":
        return build_mc_prompt(items, background)
    return build_likert_prompt(items, background)


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def call_openrouter(
    client: httpx.Client,
    model: str,
    messages: List[Dict[str, str]],
    temperature: float,
    top_p: float,
    max_tokens: int,
) -> Tuple[str, Dict[str, Any]]:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "reasoning": {"effort": "none", "exclude": True},
        "plugins": [{"id": "response-healing"}],
    }

    resp = client.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    message = data["choices"][0]["message"]
    content = message.get("content") or ""
    return content, data


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)


def list_surveys(survey_dir: Path) -> List[Path]:
    surveys = sorted(survey_dir.glob("*.json"))
    out = []
    for path in surveys:
        if path.name in {"moral_standard.json", "moral_standard_v3.json"}:
            continue
        out.append(path)
    return out


def timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def get_mc_categories(
    responses: Dict[str, Any],
    questions: Dict[str, Dict[str, Any]],
    item_ids: List[str],
) -> Optional[List[str]]:
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
    # AIDEV-NOTE: Categorical MC dimensions are summarized as distributions to preserve label fidelity.
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


def compute_summary(survey: Dict[str, Any], runs_path: Path) -> Dict[str, Any]:
    scoring = survey.get("scoring")
    if not scoring:
        raise ValueError("Survey missing scoring metadata")

    rows = [json.loads(line) for line in runs_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    responses_list = [r.get("responses") for r in rows if r.get("responses")]

    # Detect MC format
    is_mc = scoring.get("mode") == "choice"
    is_categorical = is_mc and scoring.get("type") == "categorical"
    questions_mapping = scoring.get("questions", {})
    subscales = scoring.get("subscales", {})

    if is_categorical:
        categories_per_run: List[List[str]] = []
        all_items = list(questions_mapping.keys())
        for responses in responses_list:
            if not isinstance(responses, dict):
                continue
            categories = get_mc_categories(responses, questions_mapping, all_items)
            if categories is not None:
                categories_per_run.append(categories)

        summary = {"runs": len(categories_per_run), "format": "mc"}
        summary.update(summarize_categories(categories_per_run))
        return summary

    per_run = []
    for responses in responses_list:
        if not isinstance(responses, dict):
            continue
        run_scores = {}
        ok = True

        if is_mc:
            # MC format: map letter responses to scores
            if subscales:
                for name, item_ids in subscales.items():
                    vals = []
                    for item_id in item_ids:
                        if item_id not in responses:
                            ok = False
                            break
                        letter = responses[item_id]
                        if item_id not in questions_mapping or letter not in questions_mapping[item_id]:
                            ok = False
                            break
                        score = questions_mapping[item_id][letter]
                        if isinstance(score, (int, float)):
                            vals.append(float(score))
                    if not ok or not vals:
                        break
                    run_scores[name] = mean(vals)
            else:
                # No subscales: score all questions as one dimension
                vals = []
                for item_id, mapping in questions_mapping.items():
                    if item_id not in responses:
                        ok = False
                        break
                    letter = responses[item_id]
                    if letter not in mapping:
                        ok = False
                        break
                    score = mapping[letter]
                    if isinstance(score, (int, float)):
                        vals.append(float(score))
                if ok and vals:
                    run_scores["dimension"] = mean(vals)
        else:
            # Likert format
            for name, items in subscales.items():
                vals = []
                for item_id in items:
                    if item_id not in responses:
                        ok = False
                        break
                    try:
                        vals.append(float(responses[item_id]))
                    except (TypeError, ValueError):
                        ok = False
                        break
                if not ok or not vals:
                    break
                run_scores[name] = mean(vals)

        if ok and run_scores:
            per_run.append(run_scores)

    summary = {"runs": len(per_run), "format": "mc" if is_mc else "likert"}

    if is_mc and not subscales:
        summary["dimension_mean"] = mean([r["dimension"] for r in per_run]) if per_run else None
    else:
        for name in subscales.keys():
            summary[f"{name}_mean"] = mean([r[name] for r in per_run]) if per_run else None

    if scoring.get("type") == "bipolar":
        pos = scoring.get("positive")
        neg = scoring.get("negative")
        if pos in subscales and neg in subscales and per_run:
            summary["net_score"] = summary[f"{pos}_mean"] - summary[f"{neg}_mean"]

    return summary


def run_task(
    survey_path: Path,
    model: str,
    runs: int,
    out_path: Path,
    temperature: float,
    top_p: float,
    max_tokens: int,
    background: str,
    fmt: str = "likert",
) -> Path:
    items = load_items(survey_path)
    user_prompt = build_user_prompt(items, background, fmt)

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost",
        "X-Title": "worldviews-batch",
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(headers=headers) as client, out_path.open("w", encoding="utf-8") as f:
        for run_idx in range(runs):
            messages = [{"role": "user", "content": user_prompt}]
            content, raw = call_openrouter(
                client,
                model,
                messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            parsed = extract_json(content)
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "run_index": run_idx + 1,
                "format": fmt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "background": background,
                "prompt_id": "no_system_prompt",
                "responses": parsed.get("responses") if parsed else None,
                "raw_content": content,
                "raw_response": raw,
            }
            f.write(json.dumps(record) + "\n")
            f.flush()
            time.sleep(0.2)
    return out_path


def render_dimension_comparisons(
    summaries: Dict[Tuple[str, str], Dict[str, Any]],
    survey_dir: Path,
    out_dir: Path,
) -> None:
    models = sorted({model for (_, model) in summaries.keys()})
    dimensions = sorted({dim for (dim, _) in summaries.keys()})

    for dim in dimensions:
        survey_path = survey_dir / f"{dim}.json"
        if not survey_path.exists():
            continue
        survey = load_items(survey_path)
        subscales = list(survey.get("scoring", {}).get("subscales", {}).keys())
        if not subscales:
            continue

        data = []
        for sub in subscales:
            row = []
            for model in models:
                summary = summaries.get((dim, model), {})
                val = summary.get(f"{sub}_mean")
                row.append(val if isinstance(val, (int, float)) else np.nan)
            data.append(row)

        arr = np.array(data, dtype=float)
        x = np.arange(len(subscales))
        width = 0.8 / max(1, len(models))

        plt.figure(figsize=(10, 4.8), dpi=150)
        for i, model in enumerate(models):
            plt.bar(x + i * width, arr[:, i], width=width, label=model)
        plt.ylim(1, 7)
        plt.ylabel("Mean score")
        plt.title(f"{survey.get('dimension', dim)} | model comparison")
        plt.xticks(x + width * (len(models) - 1) / 2, subscales, rotation=30, ha="right")
        plt.legend(fontsize=7)
        plt.tight_layout()

        out_path = out_dir / "comparisons" / f"{dim}_models.png"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path)
        plt.close()


def render_summary_heatmap(
    summaries: Dict[Tuple[str, str], Dict[str, Any]],
    survey_dir: Path,
    out_path: Path,
) -> None:
    models = sorted({model for (_, model) in summaries.keys()})
    dimensions = sorted({dim for (dim, _) in summaries.keys()})

    dim_label_map: Dict[str, str] = {}
    subscale_labels: Dict[str, List[str]] = {}
    for dim in dimensions:
        survey_path = survey_dir / f"{dim}.json"
        if not survey_path.exists():
            continue
        survey = load_items(survey_path)
        dim_label_map[dim] = survey.get("dimension", dim)
        subscale_labels[dim] = list(survey.get("scoring", {}).get("subscales", {}).keys())

    rows_labels: List[str] = []
    row_keys: List[Tuple[str, str]] = []
    for dim in dimensions:
        for sub in subscale_labels.get(dim, []):
            rows_labels.append(f"{dim_label_map.get(dim, dim)}::{sub}")
            row_keys.append((dim, sub))

    matrix = np.full((len(rows_labels), len(models)), np.nan, dtype=float)
    for r_idx, (dim, sub) in enumerate(row_keys):
        for c_idx, model in enumerate(models):
            summary = summaries.get((dim, model), {})
            val = summary.get(f"{sub}_mean")
            if isinstance(val, (int, float)):
                matrix[r_idx, c_idx] = val

    height = max(6, len(rows_labels) * 0.22)
    width = max(8, len(models) * 1.2)
    plt.figure(figsize=(width, height), dpi=150)
    cmap = plt.cm.viridis
    cmap.set_bad(color="#dddddd")
    im = plt.imshow(matrix, aspect="auto", vmin=1, vmax=7, cmap=cmap)
    plt.colorbar(im, label="Mean score")
    plt.yticks(range(len(rows_labels)), rows_labels, fontsize=7)
    plt.xticks(range(len(models)), models, rotation=30, ha="right", fontsize=8)
    plt.title("Worldview subscale means by model (averaged)")
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path)
    plt.close()


def write_comparison_report(
    summaries: Dict[Tuple[str, str], Dict[str, Any]],
    survey_dir: Path,
    out_path: Path,
) -> None:
    models = sorted({model for (_, model) in summaries.keys()})
    dimensions = sorted({dim for (dim, _) in summaries.keys()})

    lines = ["# Worldview comparison report", ""]

    for dim in dimensions:
        survey_path = survey_dir / f"{dim}.json"
        if not survey_path.exists():
            continue
        survey = load_items(survey_path)
        subscales = list(survey.get("scoring", {}).get("subscales", {}).keys())
        dim_label = survey.get("dimension", dim)

        lines.append(f"## {dim_label}")
        lines.append("")
        lines.append("| Subscale | " + " | ".join(models) + " |")
        lines.append("|---|" + "|".join(["---:"] * len(models)) + "|")
        for sub in subscales:
            row = [sub]
            for model in models:
                summary = summaries.get((dim, model), {})
                val = summary.get(f"{sub}_mean")
                row.append(f"{val:.2f}" if isinstance(val, (int, float)) else "")
            lines.append("| " + " | ".join(row) + " |")

        # net score if available
        if any("net_score" in summaries.get((dim, m), {}) for m in models):
            row = ["net_score"]
            for model in models:
                val = summaries.get((dim, model), {}).get("net_score")
                row.append(f"{val:.2f}" if isinstance(val, (int, float)) else "")
            lines.append("| " + " | ".join(row) + " |")

        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def run_claude_analysis(run_dir: Path, report_path: Path) -> None:
    prompt = (
        "Analyze the worldview benchmark results in the run directory. "
        "Use the comparison report and any summaries to characterize each model. "
        "Highlight the most distinctive dimensions, any contradictions or anomalies, "
        "and note confidence limits given the small number of runs. "
        "Return a concise markdown report with sections per model and a short "
        "cross-model comparison."
    )
    out_path = run_dir / "run-analysis.md"
    try:
        result = subprocess.run(
            [
                "claude",
                "--print",
                "--dangerously-skip-permissions",
                "--add-dir",
                str(run_dir),
            ],
            input=prompt,
            check=True,
            capture_output=True,
            text=True,
        )
        out_path.write_text(result.stdout.strip() + "\n", encoding="utf-8")
    except Exception as exc:
        out_path.write_text(
            f"# Run analysis failed\n\nClaude analysis failed: {exc}\n",
            encoding="utf-8",
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run all worldview dimensions and generate report + visuals.")
    parser.add_argument("--models", type=str, required=True, help="Comma-separated model ids")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--parallel", type=int, default=4)
    parser.add_argument("--survey-dir", type=Path, default=Path("survey"))
    parser.add_argument("--run-dir", type=Path, default=Path(""))
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--max-tokens", type=int, default=180)
    parser.add_argument("--background", type=str, default="")
    parser.add_argument("--format", choices=["likert", "mc"], default="likert",
                        help="Survey format: likert (1-7 scale) or mc (multiple choice A-E)")
    args = parser.parse_args()

    load_dotenv(Path(".env"))
    if not os.getenv("OPENROUTER_API_KEY"):
        raise SystemExit("Missing OPENROUTER_API_KEY (set in .env)")

    run_dir = args.run_dir
    if not run_dir or str(run_dir) in {"", ".", "./"}:
        run_dir = Path("runs") / timestamp_slug()
    results_dir = run_dir / "results"
    visuals_dir = run_dir / "visuals"
    report_path = results_dir / "comparison_report.md"
    run_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    visuals_dir.mkdir(parents=True, exist_ok=True)

    models = [m.strip() for m in args.models.split(",") if m.strip()]

    # Use mc subdirectory for MC format
    survey_dir = args.survey_dir
    if args.format == "mc":
        survey_dir = args.survey_dir / "mc"
    surveys = list_surveys(survey_dir)

    tasks = []
    for survey_path in surveys:
        dim_key = survey_path.stem
        for model in models:
            model_safe = safe_name(model)
            out_path = results_dir / f"{dim_key}_runs_{model_safe}.jsonl"
            tasks.append((survey_path, model, out_path))

    summaries: Dict[Tuple[str, str], Dict[str, Any]] = {}

    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        future_map = {
            executor.submit(
                run_task,
                survey_path,
                model,
                args.runs,
                out_path,
                args.temperature,
                args.top_p,
                args.max_tokens,
                args.background,
                args.format,
            ): (survey_path, model, out_path)
            for (survey_path, model, out_path) in tasks
        }

        for fut in as_completed(future_map):
            survey_path, model, out_path = future_map[fut]
            try:
                fut.result()
            except Exception as e:
                print(f"failed {survey_path.name} {model}: {e}")
                continue

            survey = load_items(survey_path)
            summary = compute_summary(survey, out_path)
            summary_path = results_dir / f"{survey_path.stem}_summary_{safe_name(model)}.json"
            summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            summaries[(survey_path.stem, model)] = summary

    # visuals: averaged comparisons only
    render_dimension_comparisons(summaries, args.survey_dir, visuals_dir)
    render_summary_heatmap(summaries, args.survey_dir, visuals_dir / "summary" / "heatmap.png")

    write_comparison_report(summaries, args.survey_dir, report_path)

    # run analysis via Claude Code
    run_claude_analysis(run_dir, report_path)

    run_manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": models,
        "runs_per_model": args.runs,
        "surveys": [p.name for p in surveys],
        "results_dir": str(results_dir),
        "visuals_dir": str(visuals_dir),
        "report": str(report_path),
        "analysis": str(run_dir / "run-analysis.md"),
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
