#!/usr/bin/env python3

"""Build or verify the exact Experiment 51 public-contract content manifest."""

from __future__ import annotations

import argparse
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "contract" / "public-contract-manifest.sha256"


def public_files() -> list[pathlib.Path]:
    files = [ROOT / "CONTRACT.md"]
    files.extend((ROOT / "schemas").glob("*.json"))
    files.extend(
        path
        for path in (ROOT / "contract").iterdir()
        if path.is_file() and path != MANIFEST
    )
    files.extend(
        path
        for path in (ROOT / "scripts" / "contract").iterdir()
        if path.is_file() and path.suffix in {".jl", ".py", ".sh"}
    )
    files.extend(
        path
        for path in (ROOT / "protocols" / "public-dummies" / "51-P-00").iterdir()
        if path.is_file()
    )
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix())


def render() -> str:
    lines = []
    for path in public_files():
        payload = path.read_bytes()
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"{hashlib.sha256(payload).hexdigest()} {len(payload)} {relative}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    rendered = render()
    if arguments.check:
        if not MANIFEST.exists() or MANIFEST.read_text(encoding="utf-8") != rendered:
            raise SystemExit("public contract manifest mismatch")
        print("public contract manifest verified")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
