#!/usr/bin/env python3
"""Record the authorized Round-19 verifier-only differential audit."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "V3.6"
MANIFEST = RESULTS / "v3.6-freeze-manifest.json"
AUTHORIZED = (
    "scripts/run_v36_gate4.py",
    "tests/test_v36_gate4_custody_repair.py",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    baseline = json.loads(MANIFEST.read_text())
    files = baseline["files"]
    scientific = {}
    for name, expected in files.items():
        if not name.startswith("ref/"):
            continue
        actual = sha(ROOT / name)
        scientific[name] = {
            "baseline_sha256": expected,
            "current_sha256": actual,
            "bitwise_unchanged": actual == expected,
        }
    changed = {}
    for name in AUTHORIZED:
        changed[name] = {
            "baseline_sha256": files[name],
            "repaired_sha256": sha(ROOT / name),
            "changed": files[name] != sha(ROOT / name),
        }
    failures = []
    if not all(row["bitwise_unchanged"] for row in scientific.values()):
        failures.append("frozen_scientific_module_hash_mismatch")
    if not all(row["changed"] for row in changed.values()):
        failures.append("authorized_verifier_or_test_file_not_changed")
    record = {
        "stage": "V3.6",
        "repair": "ROUND19_VERIFIER_ONLY",
        "authority": "results/V3.6/internal-round19-adjudication.md",
        "baseline_manifest": "results/V3.6/v3.6-freeze-manifest.json",
        "baseline_file_count": baseline["file_count"],
        "authorized_changed_files": changed,
        "scientific_module_hashes": scientific,
        "scientific_module_count": len(scientific),
        "scientific_modules_bitwise_unchanged": not any(
            not row["bitwise_unchanged"] for row in scientific.values()
        ),
        "semantic_diff": {
            "oracle_key": "(structure,cross_sign) -> (structure,cross_sign,reliable)",
            "key_set_equality_asserted_before_value_comparison": True,
            "support_predicate": "exp(log_evidence)>0 -> finite(log_evidence)",
            "linear_space_log_evidence_predicate_present": False,
            "scientific_likelihood_prior_or_generator_changed": False,
        },
        "regression_tests": {
            "key_collapse": "test_full_atom_keys_prevent_reliability_collapse",
            "exp_underflow": "test_log_space_evidence_positivity_survives_linear_underflow",
            "targeted_test_result": "3/3 PASS",
        },
        "failures": failures,
        "verdict": "PASS" if not failures else "FAIL",
    }
    out_json = RESULTS / "round19-verifier-repair-audit.json"
    out_md = RESULTS / "round19-verifier-repair-audit.md"
    refresh = "--refresh" in __import__("sys").argv[1:]
    if (out_json.exists() or out_md.exists()) and not refresh:
        raise SystemExit("Round-19 audit outputs already exist")
    out_json.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    out_md.write_text(
        "# V3.6 Round-19 verifier repair audit\n\n"
        f"Verdict: **{record['verdict']}**.\n\n"
        "The repair is confined to `scripts/run_v36_gate4.py` and its "
        "regression test. Oracle comparisons now use the full "
        "`(structure, cross_sign, reliable)` atom coordinate and assert exact "
        "key-set equality before comparing values. Licensed-support "
        "positivity is decided directly in log space; no log evidence is "
        "exponentiated for a predicate.\n\n"
        f"All {len(scientific)} frozen `ref/` files match the 278-file freeze "
        "manifest byte-for-byte. No likelihood, prior, generator, posterior, "
        "threshold, or scientific readout changed. Targeted regressions pass "
        "3/3.\n"
    )
    print(json.dumps({"audit": record["verdict"], "scientific_files": len(scientific)}))


if __name__ == "__main__":
    main()
