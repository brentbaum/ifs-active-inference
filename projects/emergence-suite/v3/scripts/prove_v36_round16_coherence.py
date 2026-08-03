#!/usr/bin/env python3
"""Persist the permanent V3.6 generator-coherence proof before verdict output."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ref.v36_coherence import prove_generator_coherence  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
JSON_PATH = RESULTS / "round16-generator-coherence-proof.json"
MD_PATH = RESULTS / "round16-generator-coherence-proof.md"


def main() -> int:
    if JSON_PATH.exists() or MD_PATH.exists():
        raise RuntimeError("custody refusal: round-16 proof outputs already exist")
    result = prove_generator_coherence()
    encoded = (
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    RESULTS.mkdir(parents=True, exist_ok=True)
    with JSON_PATH.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    digest = hashlib.sha256(encoded).hexdigest()
    report = "\n".join([
        "# Round-16 permanent generator-coherence proof",
        "",
        f"Verdict: **{result['verdict']}**.",
        "",
        "All four external strata were constructed directly through",
        "`_external_structure` and `_external_temporal`. Their structure/sign/",
        "partner-channel tuples occur in the frozen sign-enumerated V3 support",
        "with finite nonzero prior mass, and the resulting canonical document",
        "has finite nonzero prior-predictive mass under both adapters. The full",
        "Population-A native support was also enumerated and normalized.",
        "",
        f"JSON SHA-256: `{digest}`.",
        "",
    ]).encode("utf-8")
    with MD_PATH.open("xb") as handle:
        handle.write(report)
        handle.flush()
        os.fsync(handle.fileno())
    print(json.dumps({"verdict": result["verdict"], "sha256": digest}))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
