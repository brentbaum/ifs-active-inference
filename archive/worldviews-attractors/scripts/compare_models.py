#!/usr/bin/env python3
"""Compare two model summary JSONs for a dimension."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare two summary JSON files.")
    parser.add_argument("--a", type=Path, required=True, help="Summary A JSON")
    parser.add_argument("--b", type=Path, required=True, help="Summary B JSON")
    parser.add_argument("--label-a", type=str, default="A")
    parser.add_argument("--label-b", type=str, default="B")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    a = load(args.a)
    b = load(args.b)

    keys = [k for k in a.keys() if k != "runs" and k in b]

    lines = [
        f"# Model comparison: {args.label_a} vs {args.label_b}",
        "",
        f"A: {args.a}",
        f"B: {args.b}",
        "",
        "| Metric | A | B | B - A |",
        "|---|---:|---:|---:|",
    ]
    for k in keys:
        try:
            av = float(a[k])
            bv = float(b[k])
        except Exception:
            continue
        lines.append(f"| {k} | {av:.2f} | {bv:.2f} | {bv - av:+.2f} |")

    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", args.out)


if __name__ == "__main__":
    main()
