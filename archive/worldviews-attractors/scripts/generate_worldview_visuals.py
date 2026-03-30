#!/usr/bin/env python3
"""Generate interactive HTML visuals for worldview model comparisons."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


GROUP_LABELS = {
    "WORLD AND LIFE": "Worldview & Life",
    "HUMAN NATURE": "Human Nature",
    "COGNITION": "Cognition",
    "BEHAVIOR": "Behavior",
    "INTERPERSONAL": "Interpersonal",
    "TRANSCENDENT": "Transcendent",
}

GROUP_ORDER = [
    "WORLD AND LIFE",
    "HUMAN NATURE",
    "COGNITION",
    "BEHAVIOR",
    "INTERPERSONAL",
    "TRANSCENDENT",
]


@dataclass
class DimensionMeta:
    key: str
    label: str
    group: str


@dataclass
class SummaryEntry:
    kind: str  # "numeric" | "categorical"
    value: Optional[float] = None
    mode: Optional[str] = None
    share: Optional[float] = None
    distribution: Optional[Dict[str, float]] = None


def safe_name(text: str) -> str:
    out = []
    for ch in text:
        if ch.isalnum() or ch in {".", "_", "-"}:
            out.append(ch)
        else:
            out.append("_")
    return "".join(out)


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_summary(path: Path) -> Optional[SummaryEntry]:
    if not path.exists():
        return None
    data = load_json(path)
    if data.get("dimension_mean") is not None:
        return SummaryEntry(kind="numeric", value=float(data["dimension_mean"]))
    if data.get("category_distribution") or data.get("category_mode"):
        distribution = data.get("category_distribution") or {}
        mode = data.get("category_mode")
        share = data.get("category_mode_share")
        if mode is None and distribution:
            mode = max(distribution.items(), key=lambda item: (item[1], item[0]))[0]
            share = distribution.get(mode)
        return SummaryEntry(
            kind="categorical",
            mode=mode,
            share=float(share) if isinstance(share, (int, float)) else None,
            distribution=distribution,
        )
    return None


def load_dimensions(survey_dir: Path, manifest_path: Optional[Path]) -> List[DimensionMeta]:
    dimensions: List[DimensionMeta] = []
    survey_files: List[Path] = []

    if manifest_path and manifest_path.exists():
        manifest = load_json(manifest_path)
        survey_files = [survey_dir / name for name in manifest.get("surveys", [])]
    else:
        survey_files = sorted(survey_dir.glob("*.json"))

    for path in survey_files:
        if not path.exists():
            continue
        data = load_json(path)
        key = path.stem
        dimensions.append(
            DimensionMeta(
                key=key,
                label=data.get("dimension", key),
                group=data.get("group", "Unknown"),
            )
        )

    return dimensions


def group_dimensions(dimensions: List[DimensionMeta]) -> Dict[str, List[DimensionMeta]]:
    grouped: Dict[str, List[DimensionMeta]] = {g: [] for g in GROUP_ORDER}
    for dim in dimensions:
        group = dim.group
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(dim)

    for group, dims in grouped.items():
        grouped[group] = sorted(dims, key=lambda d: d.label)
    return grouped


def score_to_color(value: float) -> str:
    # Map -2..2 to hue 210 (blue) .. 15 (red)
    clamped = max(-2.0, min(2.0, value))
    t = (clamped + 2.0) / 4.0
    hue = 210 - (195 * t)
    return f"hsl({hue:.0f}, 70%, 55%)"


def bar_style(value: float) -> str:
    # AIDEV-NOTE: Numeric bars anchor at center; width scales to abs(score) within [-2, 2].
    clamped = max(-2.0, min(2.0, value))
    width = abs(clamped) / 2.0 * 50.0
    if clamped >= 0:
        left = 50
    else:
        left = 50 - width
    color = score_to_color(clamped)
    return f"left:{left:.1f}%; width:{width:.1f}%; background:{color};"


def share_style(share: Optional[float]) -> str:
    pct = 0.0 if share is None else max(0.0, min(1.0, share)) * 100.0
    return f"width:{pct:.1f}%;"


def build_model_cards(
    models: List[str],
    grouped: Dict[str, List[DimensionMeta]],
    summaries: Dict[Tuple[str, str], Optional[SummaryEntry]],
) -> str:
    cards = []
    for model in models:
        rows = []
        for group in GROUP_ORDER:
            dims = grouped.get(group, [])
            if not dims:
                continue
            rows.append(f"<div class=\"group-title\">{GROUP_LABELS.get(group, group)}</div>")
            for dim in dims:
                summary = summaries.get((dim.key, model))
                if summary is None:
                    rows.append(
                        f"<div class=\"dim-row\"><div class=\"dim-label\">{dim.label}</div>"
                        f"<div class=\"dim-missing\">—</div></div>"
                    )
                    continue
                if summary.kind == "numeric" and summary.value is not None:
                    rows.append(
                        f"<div class=\"dim-row\">"
                        f"<div class=\"dim-label\">{dim.label}</div>"
                        f"<div class=\"dim-bar\">"
                        f"<span class=\"dim-center\"></span>"
                        f"<span class=\"dim-fill\" style=\"{bar_style(summary.value)}\"></span>"
                        f"</div>"
                        f"<div class=\"dim-value\">{summary.value:.2f}</div>"
                        f"</div>"
                    )
                elif summary.kind == "categorical":
                    mode = summary.mode or "—"
                    share = summary.share
                    share_text = f"{share:.0%}" if isinstance(share, float) else ""
                    rows.append(
                        f"<div class=\"dim-row\">"
                        f"<div class=\"dim-label\">{dim.label}</div>"
                        f"<div class=\"cat-pill\">{mode}</div>"
                        f"<div class=\"cat-bar\"><span style=\"{share_style(share)}\"></span></div>"
                        f"<div class=\"dim-value\">{share_text}</div>"
                        f"</div>"
                    )
        cards.append(
            "<section class=\"model-card\">"
            f"<h2>{model}</h2>"
            "<div class=\"card-body\">"
            + "\n".join(rows)
            + "</div></section>"
        )
    return "\n".join(cards)


def build_matrix(
    models: List[str],
    grouped: Dict[str, List[DimensionMeta]],
    summaries: Dict[Tuple[str, str], Optional[SummaryEntry]],
) -> str:
    rows = [
        "<table class=\"matrix\">",
        "<thead><tr><th>Dimension</th>" + "".join(f"<th>{m}</th>" for m in models) + "</tr></thead>",
        "<tbody>",
    ]

    for group in GROUP_ORDER:
        dims = grouped.get(group, [])
        if not dims:
            continue
        rows.append(
            f"<tr class=\"group-row\"><td colspan=\"{len(models) + 1}\">{GROUP_LABELS.get(group, group)}</td></tr>"
        )
        for dim in dims:
            row_cells = [f"<td class=\"dim-cell\">{dim.label}</td>"]
            for model in models:
                summary = summaries.get((dim.key, model))
                if summary is None:
                    row_cells.append("<td class=\"cell missing\">—</td>")
                    continue
                if summary.kind == "numeric" and summary.value is not None:
                    color = score_to_color(summary.value)
                    row_cells.append(
                        f"<td class=\"cell numeric\" style=\"background:{color};\">{summary.value:.2f}</td>"
                    )
                elif summary.kind == "categorical":
                    mode = summary.mode or "—"
                    share = summary.share
                    share_text = f" {share:.0%}" if isinstance(share, float) else ""
                    opacity = 0.15 + (share or 0.0) * 0.6
                    row_cells.append(
                        f"<td class=\"cell categorical\" style=\"background:rgba(48,84,150,{opacity:.2f});\">{mode}{share_text}</td>"
                    )
                else:
                    row_cells.append("<td class=\"cell missing\">—</td>")
            rows.append("<tr>" + "".join(row_cells) + "</tr>")

    rows.append("</tbody></table>")
    return "\n".join(rows)


def build_html(cards_html: str, matrix_html: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Worldview model comparison</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card: #111827;
      --text: #e5e7eb;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --pill: #1f2937;
      --border: #1f2937;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Inter", system-ui, -apple-system, sans-serif;
      background: radial-gradient(circle at top, #1e293b 0%, #0b1120 55%, #05070f 100%);
      color: var(--text);
      padding: 32px 24px 48px;
    }}
    h1 {{ font-size: 28px; margin: 0 0 12px; }}
    h2 {{ font-size: 20px; margin: 0 0 12px; }}
    .subtitle {{ color: var(--muted); margin-bottom: 24px; }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
      margin-bottom: 36px;
    }}
    .model-card {{
      background: rgba(17, 24, 39, 0.88);
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.25);
      backdrop-filter: blur(10px);
    }}
    .card-body {{ display: grid; gap: 8px; }}
    .group-title {{
      margin-top: 10px;
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--accent);
    }}
    .dim-row {{
      display: grid;
      grid-template-columns: 1.2fr 1.2fr 0.6fr;
      gap: 10px;
      align-items: center;
      font-size: 13px;
      padding: 6px 0;
      border-bottom: 1px dashed rgba(148,163,184,0.15);
    }}
    .dim-row:last-child {{ border-bottom: none; }}
    .dim-label {{ color: var(--text); }}
    .dim-bar {{
      position: relative;
      height: 10px;
      background: rgba(148,163,184,0.15);
      border-radius: 999px;
      overflow: hidden;
    }}
    .dim-center {{
      position: absolute;
      left: 50%;
      top: 0;
      bottom: 0;
      width: 1px;
      background: rgba(255,255,255,0.35);
    }}
    .dim-fill {{ position: absolute; top: 0; bottom: 0; border-radius: 999px; }}
    .dim-value {{ text-align: right; color: var(--muted); }}
    .dim-missing {{ color: var(--muted); text-align: right; }}
    .cat-pill {{
      background: var(--pill);
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 12px;
      text-align: center;
      color: var(--text);
    }}
    .cat-bar {{
      height: 8px;
      background: rgba(148,163,184,0.2);
      border-radius: 999px;
      overflow: hidden;
      position: relative;
    }}
    .cat-bar span {{
      display: block;
      height: 100%;
      background: #38bdf8;
    }}
    .matrix-wrap {{
      background: rgba(15, 23, 42, 0.92);
      border-radius: 18px;
      padding: 18px;
      border: 1px solid rgba(148,163,184,0.2);
      overflow-x: auto;
    }}
    table.matrix {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }}
    table.matrix th,
    table.matrix td {{
      padding: 8px 10px;
      border-bottom: 1px solid rgba(148,163,184,0.2);
      text-align: left;
    }}
    table.matrix th {{ color: var(--muted); font-weight: 600; }}
    .cell {{ text-align: center; border-radius: 6px; font-weight: 600; color: #0b1120; }}
    .cell.categorical {{ color: #e2e8f0; font-weight: 500; }}
    .cell.missing {{ color: var(--muted); text-align: center; }}
    .group-row td {{
      padding: 10px;
      background: rgba(56, 189, 248, 0.12);
      color: #e0f2fe;
      font-weight: 600;
      border-bottom: none;
    }}
    .legend {{
      margin-top: 16px;
      color: var(--muted);
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <h1>Worldview fingerprints</h1>
  <div class=\"subtitle\">Numeric dimensions use a -2 → +2 scale; categorical show mode + share.</div>
  <div class=\"cards\">
    {cards_html}
  </div>
  <section class=\"matrix-wrap\">
    <h2>Comparison matrix</h2>
    {matrix_html}
    <div class=\"legend\">Numeric cells are color-mapped; categorical cells show mode and share.</div>
  </section>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate worldview HTML visuals.")
    parser.add_argument("--results-dir", type=Path, default=Path("runs/mc_comparison/results"))
    parser.add_argument("--survey-dir", type=Path, default=Path("survey/mc"))
    parser.add_argument("--manifest", type=Path, default=Path("runs/mc_comparison/run_manifest.json"))
    parser.add_argument("--out", type=Path, default=Path("runs/mc_comparison/visuals/worldview_cards.html"))
    args = parser.parse_args()

    manifest = load_json(args.manifest) if args.manifest.exists() else {}
    models = manifest.get("models", [])
    models = [m for m in models if isinstance(m, str)]

    dimensions = load_dimensions(args.survey_dir, args.manifest if args.manifest.exists() else None)
    grouped = group_dimensions(dimensions)

    summaries: Dict[Tuple[str, str], Optional[SummaryEntry]] = {}
    for dim in dimensions:
        for model in models:
            summary_path = args.results_dir / f"{dim.key}_summary_{safe_name(model)}.json"
            summaries[(dim.key, model)] = parse_summary(summary_path)

    cards_html = build_model_cards(models, grouped, summaries)
    matrix_html = build_matrix(models, grouped, summaries)
    html = build_html(cards_html, matrix_html)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
