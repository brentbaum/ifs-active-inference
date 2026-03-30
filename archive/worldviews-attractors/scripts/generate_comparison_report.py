#!/usr/bin/env python3
"""Generate comparison report from MC survey results."""

import json
from pathlib import Path

RESULTS_DIR = Path("runs/mc_comparison/results")

# Dimension metadata - extracted from actual MC survey files
DIMENSIONS = {
    # Worldview & Life (WL)
    "wl_ag": ("Agency", "Worldview & Life"),
    "wl_cm": ("Cosmos", "Worldview & Life"),
    "wl_df": ("Determining Factors", "Worldview & Life"),
    "wl_dt": ("Deity", "Worldview & Life"),
    "wl_ex": ("Explanation", "Worldview & Life"),
    "wl_hn": ("Humanity-Nature", "Worldview & Life"),
    "wl_ip": ("Intrapsychic", "Worldview & Life"),
    "wl_nc": ("Nature-Consciousness", "Worldview & Life"),
    "wl_on": ("Ontology", "Worldview & Life"),
    "wl_pl": ("Purpose of Life", "Worldview & Life"),
    "wl_un": ("Unity", "Worldview & Life"),
    "wl_wb": ("Well-Being", "Worldview & Life"),
    "wl_wj": ("World Justice", "Worldview & Life"),
    "wl_wr": ("Worth of Life", "Worldview & Life"),
    # Human Nature (HN)
    "hn_cx": ("Complexity", "Human Nature"),
    "hn_mo": ("Moral Orientation", "Human Nature"),
    "hn_mu": ("Mutability", "Human Nature"),
    # Cognition (CG)
    "cg_cs": ("Consciousness", "Cognition"),
    "cg_kn": ("Knowledge Sources", "Cognition"),
    # Behavior (BH)
    "bh_ad": ("Activity Direction", "Behavior"),
    "bh_ae": ("Action Efficacy", "Behavior"),
    "bh_as": ("Activity Satisfaction", "Behavior"),
    "bh_cd": ("Control Disposition", "Behavior"),
    "bh_cl": ("Control Location", "Behavior"),
    "bh_mr": ("Moral Relevance", "Behavior"),
    "bh_ms": ("Moral Source", "Behavior"),
    "bh_mt": ("Moral Standard", "Behavior"),
    "bh_to": ("Time Orientation", "Behavior"),
    # Interpersonal (IP)
    "ip_cn": ("Connection", "Interpersonal"),
    "ip_cr": ("Correction", "Interpersonal"),
    "ip_ij": ("Interpersonal Justice", "Interpersonal"),
    "ip_in": ("Interaction", "Interpersonal"),
    "ip_ot": ("Otherness", "Interpersonal"),
    "ip_ra": ("Relation to Authority", "Interpersonal"),
    "ip_rb": ("Relation to Biosphere", "Interpersonal"),
    "ip_rg": ("Relation to Group", "Interpersonal"),
    "ip_rh": ("Relation to Humanity", "Interpersonal"),
    "ip_sj": ("Sociopolitical Justice", "Interpersonal"),
    "ip_sx": ("Sexuality", "Interpersonal"),
    # Transcendent (TR)
    "tr_av": ("Availability", "Transcendent"),
    "tr_po": ("Possession", "Transcendent"),
    "tr_sc": ("Scope", "Transcendent"),
}

def parse_summary_entry(data):
    if data.get("dimension_mean") is not None:
        return {"kind": "numeric", "value": data["dimension_mean"]}

    if data.get("category_distribution") or data.get("category_mode"):
        distribution = data.get("category_distribution") or {}
        mode = data.get("category_mode")
        share = data.get("category_mode_share")

        if mode is None and distribution:
            mode = max(distribution.items(), key=lambda item: (item[1], item[0]))[0]
            share = distribution.get(mode)

        return {
            "kind": "categorical",
            "mode": mode,
            "share": share,
            "distribution": distribution,
        }

    return None


def format_entry(entry):
    if entry is None:
        return "—"
    if entry["kind"] == "numeric":
        return f"{entry['value']:.2f}"
    if entry["kind"] == "categorical":
        mode = entry.get("mode")
        share = entry.get("share")
        if mode is None:
            return "—"
        if isinstance(share, (int, float)):
            return f"{mode} ({share:.2f})"
        return str(mode)
    return "—"


def load_results():
    """Load all summary files."""
    results = {}

    for code in DIMENSIONS.keys():
        results[code] = {
            "kimi": None,
            "haiku": None
        }

        # Load Kimi results
        kimi_file = RESULTS_DIR / f"{code}_summary_moonshotai_kimi-k2.5.json"
        if kimi_file.exists():
            with open(kimi_file) as f:
                data = json.load(f)
                results[code]["kimi"] = parse_summary_entry(data)

        # Load Haiku results
        haiku_file = RESULTS_DIR / f"{code}_summary_anthropic_claude-3.5-haiku.json"
        if haiku_file.exists():
            with open(haiku_file) as f:
                data = json.load(f)
                results[code]["haiku"] = parse_summary_entry(data)

    return results

def generate_report(results):
    """Generate markdown report."""
    lines = [
        "# Worldview MC Survey Comparison Report",
        "",
        "Comparing Kimi K2.5 vs Claude 3.5 Haiku on 42 worldview dimensions using multiple choice format.",
        "",
        "## Summary Statistics",
        ""
    ]

    # Calculate stats
    valid_kimi_numeric = [
        v["kimi"]["value"]
        for v in results.values()
        if v["kimi"] is not None and v["kimi"]["kind"] == "numeric"
    ]
    valid_haiku_numeric = [
        v["haiku"]["value"]
        for v in results.values()
        if v["haiku"] is not None and v["haiku"]["kind"] == "numeric"
    ]
    valid_kimi_categorical = [
        v["kimi"]
        for v in results.values()
        if v["kimi"] is not None and v["kimi"]["kind"] == "categorical"
    ]
    valid_haiku_categorical = [
        v["haiku"]
        for v in results.values()
        if v["haiku"] is not None and v["haiku"]["kind"] == "categorical"
    ]

    divergences = []
    categorical_pairs = []
    for code, data in results.items():
        if (
            data["kimi"] is not None
            and data["haiku"] is not None
            and data["kimi"]["kind"] == "numeric"
            and data["haiku"]["kind"] == "numeric"
        ):
            diff = abs(data["kimi"]["value"] - data["haiku"]["value"])
            divergences.append((code, diff, data["kimi"]["value"], data["haiku"]["value"]))
        if (
            data["kimi"] is not None
            and data["haiku"] is not None
            and data["kimi"]["kind"] == "categorical"
            and data["haiku"]["kind"] == "categorical"
        ):
            categorical_pairs.append((code, data["kimi"], data["haiku"]))

    lines.extend([
        f"- **Kimi K2.5 (numeric)**: {len(valid_kimi_numeric)}/42 dimensions scored",
        f"- **Claude Haiku (numeric)**: {len(valid_haiku_numeric)}/42 dimensions scored",
        f"- **Comparable numeric dimensions**: {len(divergences)}",
        ""
    ])

    if divergences:
        avg_divergence = sum(d[1] for d in divergences) / len(divergences)
        lines.append(f"- **Average divergence**: {avg_divergence:.2f}")
        lines.append("")

    categorical_dim_count = len(
        [
            code
            for code, data in results.items()
            if (data["kimi"] and data["kimi"]["kind"] == "categorical")
            or (data["haiku"] and data["haiku"]["kind"] == "categorical")
        ]
    )
    if categorical_dim_count:
        lines.append(
            f"- **Categorical dimensions scored**: "
            f"Kimi {len(valid_kimi_categorical)}/{categorical_dim_count}, "
            f"Claude {len(valid_haiku_categorical)}/{categorical_dim_count}"
        )
        if categorical_pairs:
            matches = sum(1 for _, kimi, haiku in categorical_pairs if kimi.get("mode") == haiku.get("mode"))
            lines.append(f"- **Categorical mode agreement**: {matches}/{len(categorical_pairs)}")
        lines.append("")

    # Full results table
    lines.extend([
        "## Full Results by Group",
        ""
    ])

    # Group dimensions
    groups = {}
    for code, (name, group) in DIMENSIONS.items():
        if group not in groups:
            groups[group] = []
        groups[group].append((code, name))

    for group_name, dims in groups.items():
        lines.extend([
            f"### {group_name}",
            "",
            "| Dimension | Kimi K2.5 | Claude Haiku | Divergence |",
            "|-----------|-----------|--------------|------------|"
        ])

        for code, name in dims:
            data = results[code]
            kimi_val = format_entry(data["kimi"])
            haiku_val = format_entry(data["haiku"])

            if (
                data["kimi"] is not None
                and data["haiku"] is not None
                and data["kimi"]["kind"] == "numeric"
                and data["haiku"]["kind"] == "numeric"
            ):
                diff = abs(data["kimi"]["value"] - data["haiku"]["value"])
                diff_str = f"{diff:.2f}"
                if diff >= 1.0:
                    diff_str = f"**{diff_str}**"
            else:
                diff_str = "—"

            lines.append(f"| {name} | {kimi_val} | {haiku_val} | {diff_str} |")

        lines.append("")

    # Top divergences
    if divergences:
        lines.extend([
            "## Top Divergences (≥ 0.5)",
            "",
            "| Dimension | Kimi K2.5 | Claude Haiku | Divergence |",
            "|-----------|-----------|--------------|------------|"
        ])

        sorted_divs = sorted(divergences, key=lambda x: -x[1])
        for code, diff, kimi, haiku in sorted_divs:
            if diff >= 0.5:
                name = DIMENSIONS[code][0]
                lines.append(f"| {name} | {kimi:.2f} | {haiku:.2f} | **{diff:.2f}** |")

        lines.append("")

    # Interpretation notes
    lines.extend([
        "## Interpretation Guide",
        "",
        "- **Score range**: -2.0 (strong pole A) to +2.0 (strong pole B)",
        "- **0.0**: Balanced/neutral position",
        "- **Divergence ≥ 1.0**: Substantial disagreement between models",
        "- **Categorical entries**: `mode (share)` across items and runs",
        "- **—**: Missing data",
        ""
    ])

    return "\n".join(lines)

if __name__ == "__main__":
    results = load_results()
    report = generate_report(results)

    output_path = RESULTS_DIR / "comparison_report.md"
    with open(output_path, "w") as f:
        f.write(report)

    print(f"Report generated: {output_path}")
    print(report)
