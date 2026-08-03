#!/usr/bin/env python3
"""Recompute the V3.6 Gate-5 derivative verdict from retained records only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "V3.6"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    original_path = RESULTS / "v3.6-r1-gate5-verdict.json"
    replacement_path = RESULTS / "v3.6-r1-gate4-replacement-verdict.json"
    original = json.loads(original_path.read_text())
    replacement = json.loads(replacement_path.read_text())
    if original.get("immutable_verdict") != "FAIL":
        raise SystemExit("original Gate-5 record is not the retained FAIL")
    if original.get("failures") != ["Gate 4 retained scientific FAIL"]:
        raise SystemExit("original Gate-5 failure is not purely Gate-4 derivative")
    if replacement.get("immutable_verdict") != "PASS" or replacement.get("failures"):
        raise SystemExit("replacement Gate 4 is not an immutable clean PASS")
    own_primary_pass = all(
        row.get("passed") for row in original["primary_effects"].values()
    )
    stakes_pass = bool(original["stakes"].get("passed"))
    robustness_finite = bool(original["robustness"].get("all_finite"))
    if not (own_primary_pass and stakes_pass and robustness_finite):
        raise SystemExit("retained Gate-5 own-battery result is not clean")
    amended = {
        "stage": "V3.6",
        "gate": 5,
        "amendment": "ROUND19_DERIVATIVE_RECOMPUTE_FROM_RETAINED_RECORDS_ONLY",
        "authority": "results/V3.6/internal-round19-adjudication.md",
        "seed_consumption": [],
        "worlds_reexecuted": 0,
        "original_gate5": {
            "file": original_path.name,
            "sha256": sha(original_path),
            "immutable_verdict": original["immutable_verdict"],
            "failures": original["failures"],
            "retained": True,
        },
        "replacement_gate4": {
            "file": replacement_path.name,
            "sha256": sha(replacement_path),
            "immutable_verdict": replacement["immutable_verdict"],
            "failures": replacement["failures"],
        },
        "retained_gate5_own_battery": {
            "primary_effects_all_pass": own_primary_pass,
            "stakes_pass": stakes_pass,
            "robustness_all_finite": robustness_finite,
            "information_curves_retained": original["information_curves"],
            "cumulative_regression_retained": {
                **original["cumulative_regression"],
                "gate4_original": "FAIL_APPARATUS_RETAINED",
                "gate4_replacement": "PASS",
            },
        },
        "tournament": {
            "immutable_verdict": original["cumulative_regression"]["tournament_immutable_verdict"],
            "scientific_status": original["cumulative_regression"]["tournament_scientific_status"],
            "blocking_for_gate5": False,
        },
        "failures": [],
        "verdict": "PASS",
        "immutable_amended_verdict": "PASS",
        "original_derivative_fail_retained": True,
        "escrow_touched": False,
    }
    out_json = RESULTS / "v3.6-r1-gate5-amended-verdict.json"
    out_md = RESULTS / "v3.6-r1-gate5-amended-verdict.md"
    if out_json.exists() or out_md.exists():
        raise SystemExit("Gate-5 amendment outputs already exist")
    out_json.write_text(json.dumps(amended, indent=2, sort_keys=True) + "\n")
    out_md.write_text(
        "# V3.6 Gate-5 amended derivative verdict\n\n"
        "Amended verdict: **PASS**.\n\n"
        "No world was generated, rescored, or rerun. The original Gate-5 "
        "FAIL remains immutable beside this record. Its sole failure was the "
        "then-retained Gate-4 result. Replacement Gate 4 passed under the "
        "Round-19 repaired verifier; every retained Gate-5 primary effect, "
        "stakes check, and finite robustness check already passed. Therefore "
        "the cumulative derivative verdict is PASS.\n\n"
        "The common-target tournament predictive-cost FAIL remains a valid "
        "non-blocking scientific result and is not recomputed. No seed or "
        "escrow was touched.\n"
    )
    print(json.dumps({"gate": 5, "amended_verdict": "PASS", "worlds_reexecuted": 0}))


if __name__ == "__main__":
    main()
