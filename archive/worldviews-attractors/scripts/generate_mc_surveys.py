#!/usr/bin/env python3
"""Generate MC survey JSON files from worldview_survey_mc.md and scoring key."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def parse_mc_markdown(md_path: Path) -> Dict[str, Dict[str, Any]]:
    """Parse the MC markdown survey into structured data.

    Returns dict keyed by dimension code (e.g., "HN-MO") with:
        - name: dimension name
        - group: group name
        - questions: list of {id, text, options}
    """
    content = md_path.read_text(encoding="utf-8")
    dimensions: Dict[str, Dict[str, Any]] = {}

    current_group = None
    current_dim_code = None
    current_dim_name = None

    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Match group headers: "# GROUP 1: HUMAN NATURE"
        group_match = re.match(r"^# GROUP \d+: (.+)$", line)
        if group_match:
            current_group = group_match.group(1).strip()
            i += 1
            continue

        # Match dimension headers: "## 1.1 Moral Orientation (HN-MO)"
        dim_match = re.match(r"^## \d+\.\d+ (.+?) \(([A-Z]{2}-[A-Z]{2})\)$", line)
        if dim_match:
            current_dim_name = dim_match.group(1).strip()
            current_dim_code = dim_match.group(2).strip()
            dimensions[current_dim_code] = {
                "name": current_dim_name,
                "group": current_group,
                "questions": [],
            }
            i += 1
            continue

        # Match question headers: "**HN-MO-1**: Question text..."
        q_match = re.match(r"^\*\*([A-Z]{2}-[A-Z]{2}-\d+)\*\*: (.+)$", line)
        if q_match and current_dim_code:
            q_id = q_match.group(1)
            q_text = q_match.group(2).strip()
            options: Dict[str, str] = {}

            # Parse options on following lines
            i += 1
            while i < len(lines):
                opt_line = lines[i]
                opt_match = re.match(r"^- \(([A-E])\) (.+)$", opt_line)
                if opt_match:
                    letter = opt_match.group(1)
                    opt_text = opt_match.group(2).strip()
                    options[letter] = opt_text
                    i += 1
                elif opt_line.strip() == "" or opt_line.startswith("**") or opt_line.startswith("#") or opt_line.startswith("---"):
                    break
                else:
                    i += 1

            dimensions[current_dim_code]["questions"].append({
                "id": q_id,
                "text": q_text,
                "options": options,
            })
            continue

        i += 1

    return dimensions


def load_scoring_key(key_path: Path) -> Dict[str, Any]:
    """Load the scoring key JSON."""
    return json.loads(key_path.read_text(encoding="utf-8"))


def generate_survey_json(
    dim_code: str,
    dim_data: Dict[str, Any],
    scoring_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate a survey JSON for a single dimension."""
    scoring_dim = scoring_data["dimensions"].get(dim_code, {})

    # Build scoring section
    questions_scoring = scoring_dim.get("questions", {})

    # Determine scoring type
    scoring_type = "bipolar"
    if scoring_dim.get("categorical"):
        scoring_type = "categorical"

    survey = {
        "dimension": dim_data["name"],
        "code": dim_code,
        "group": dim_data["group"],
        "format": "mc",
        "poles": scoring_dim.get("poles", []),
        "non_mutually_exclusive": scoring_dim.get("non_mutually_exclusive", False),
        "items": dim_data["questions"],
        "scoring": {
            "mode": "choice",
            "type": scoring_type,
            "questions": questions_scoring,
        },
    }

    # Add interpretation if available
    if "interpretation" in scoring_dim:
        survey["interpretation"] = scoring_dim["interpretation"]

    return survey


def main() -> None:
    base_dir = Path(__file__).parent.parent
    md_path = base_dir / "survey" / "worldview_survey_mc.md"
    key_path = base_dir / "survey" / "worldview_scoring_key.json"
    out_dir = base_dir / "survey" / "mc"

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {md_path}...")
    dimensions = parse_mc_markdown(md_path)
    print(f"Found {len(dimensions)} dimensions")

    print(f"Loading {key_path}...")
    scoring_data = load_scoring_key(key_path)

    for dim_code, dim_data in dimensions.items():
        survey = generate_survey_json(dim_code, dim_data, scoring_data)
        out_file = out_dir / f"{dim_code.lower().replace('-', '_')}.json"
        out_file.write_text(json.dumps(survey, indent=2) + "\n", encoding="utf-8")
        print(f"  Generated {out_file.name}: {len(dim_data['questions'])} questions")

    print(f"\nGenerated {len(dimensions)} MC survey files in {out_dir}")


if __name__ == "__main__":
    main()
