#!/usr/bin/env python3
"""Declare the Round-19 V3.6 freeze and hash the repaired verifier set."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "V3.6"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def retained_stop_records() -> list[dict[str, str]]:
    selected: set[Path] = set()
    for path in RESULTS.iterdir():
        if path.is_file() and path.suffix in {".json", ".md"}:
            if "stop" in path.name or "diagnosis-stub" in path.name:
                selected.add(path)
    for name in (
        "gate-3.json",
        "v3.6-r1-bridge-qualification.json",
        "v3.6-r1-round12-v2-native-qualification.json",
        "v3.6-r1-round14-v3-native-replacement-2-qualification.json",
        "v3.6-r1-tournament-verdict.json",
        "v3.6-r1-gate4-verdict.json",
        "v3.6-r1-gate5-verdict.json",
        "round18-gate4-diagnosis.json",
    ):
        path = RESULTS / name
        if path.exists():
            selected.add(path)
    return [
        {"file": rel(path), "sha256": sha(path)} for path in sorted(selected)
    ]


def main() -> None:
    audit_path = RESULTS / "round19-verifier-repair-audit.json"
    gate4_path = RESULTS / "v3.6-r1-gate4-replacement-verdict.json"
    gate5_path = RESULTS / "v3.6-r1-gate5-amended-verdict.json"
    compatibility_path = RESULTS / "v3.6-compatibility-attestations.json"
    audit = json.loads(audit_path.read_text())
    gate4 = json.loads(gate4_path.read_text())
    gate5 = json.loads(gate5_path.read_text())
    compatibility = json.loads(compatibility_path.read_text())
    if audit.get("verdict") != "PASS":
        raise SystemExit("Round-19 verifier audit did not pass")
    if gate4.get("immutable_verdict") != "PASS":
        raise SystemExit("replacement Gate 4 did not pass")
    if gate5.get("immutable_amended_verdict") != "PASS":
        raise SystemExit("amended Gate 5 did not pass")
    if not all(compatibility["six_point_attestation"].values()):
        raise SystemExit("challenge compatibility attestation is not 6/6")

    original_gate4 = RESULTS / "v3.6-r1-gate4-verdict.json"
    original_gate5 = RESULTS / "v3.6-r1-gate5-verdict.json"
    tournament = RESULTS / "v3.6-r1-tournament-verdict.json"
    declaration = {
        "stage": "V3.6",
        "status": "FROZEN_ROUND19_WITH_RETAINED_COMPRESSION_PREDICTIVE_COST",
        "authority": "results/V3.6/internal-round19-adjudication.md",
        "freeze_declared": True,
        "scientific_disposition": {
            "common_target_tournament": "FAIL_PREDICTIVE_COST_RETAINED",
            "replacement_gate4": "PASS",
            "amended_gate5": "PASS",
        },
        "apparatus_history": {
            "original_gate4": {
                "status": "FAIL_APPARATUS_RETAINED",
                "file": rel(original_gate4),
                "sha256": sha(original_gate4),
            },
            "original_gate5": {
                "status": "FAIL_DERIVATIVE_RETAINED",
                "file": rel(original_gate5),
                "sha256": sha(original_gate5),
            },
            "round18_classification": "D1_ORACLE_CONSTRUCT__D2_SUPPORT_ACCOUNTING_APPARATUS",
            "round19_verifier_repair": "PASS",
        },
        "replacement_records": {
            "gate4": {"file": rel(gate4_path), "sha256": sha(gate4_path)},
            "gate5": {"file": rel(gate5_path), "sha256": sha(gate5_path)},
            "verifier_audit": {"file": rel(audit_path), "sha256": sha(audit_path)},
        },
        "retained_stops": retained_stop_records(),
        "retained_stop_count": len(retained_stop_records()),
        "barred_blocks": compatibility["barred_blocks"],
        "retired_unconsumed_blocks": compatibility["retired_unconsumed_blocks"],
        "closed_diagnosis_only_blocks": compatibility["closed_diagnosis_only_blocks"],
        "valid_once_consumed_blocks": compatibility["valid_once_consumed_blocks"]
        + [{"range": [3_728_000, 3_732_999], "purpose": "replacement Gate 4"}],
        "compatibility": {
            "six_of_six": True,
            "file": rel(compatibility_path),
            "sha256": sha(compatibility_path),
        },
        "tests": {"v3": "82/82 PASS"},
        "escrow_opened": False,
        "sealed_plaintext_opened": False,
    }
    declaration_json = RESULTS / "v3.6-freeze-declaration.json"
    declaration_md = RESULTS / "v3.6-freeze-declaration.md"
    manifest_json = RESULTS / "v3.6-freeze-manifest-final.json"
    manifest_md = RESULTS / "v3.6-freeze-manifest-final.md"
    for path in (declaration_json, declaration_md, manifest_json, manifest_md):
        if path.exists():
            raise SystemExit(f"final freeze output already exists: {path.name}")
    dump(declaration_json, declaration)
    declaration_md.write_text(
        "# V3.6 Round-19 freeze declaration\n\n"
        "Status: **FROZEN_ROUND19_WITH_RETAINED_COMPRESSION_PREDICTIVE_COST**.\n\n"
        "Replacement Gate 4 passed all five lesion cells under the repaired "
        "verifier. Gate 5 is PASS by retained-record derivative recomputation; "
        "no Gate-5 world was rerun. The original Gate-4 apparatus FAIL and "
        "original Gate-5 derivative FAIL remain immutable in the ledger. The "
        "one-shot common-target tournament predictive-cost FAIL also remains "
        "a scientific result.\n\n"
        f"All {declaration['retained_stop_count']} retained stop/failure records "
        "are named and hashed in the JSON declaration. Compatibility remains "
        "6/6. C-V36A/B/C plaintext and escrow remain untouched.\n"
    )

    candidates: set[Path] = set()
    for folder in ("ref", "contracts", "protocols", "audits", "scripts", "tests"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                candidates.add(path)
    for path in RESULTS.iterdir():
        if not path.is_file():
            continue
        if path.name in {
            "ready-to-commit.md",
            manifest_json.name,
            manifest_md.name,
        }:
            continue
        if path.suffix in {".json", ".md", ".diff"} or path.name.endswith(
            "hash-events.jsonl"
        ):
            candidates.add(path)
    for stage in (f"V3.{index}" for index in range(6)):
        for name in ("freeze-manifest.json", "stage-verdict.md", "stage-verdict.json"):
            path = ROOT / "results" / stage / name
            if path.exists():
                candidates.add(path)
    files = {rel(path): sha(path) for path in sorted(candidates)}
    manifest = {
        "stage": "V3.6",
        "status": declaration["status"],
        "freeze_declared": True,
        "hash_algorithm": "sha256",
        "file_count": len(files),
        "files": files,
        "freeze_declaration": {
            "file": rel(declaration_json),
            "sha256": sha(declaration_json),
        },
        "verifier_repair_audit": {
            "file": rel(audit_path),
            "sha256": sha(audit_path),
        },
        "replacement_gate4": "PASS",
        "amended_gate5": "PASS",
        "tournament": "FAIL_PREDICTIVE_COST_RETAINED",
        "escrow_opened": False,
        "sealed_plaintext_opened": False,
        "tests": {"v3": "82/82 PASS"},
    }
    dump(manifest_json, manifest)
    manifest_md.write_text(
        "# V3.6 final freeze manifest\n\n"
        f"Status: **{manifest['status']}**.\n\n"
        f"The final manifest hashes {len(files)} scientific, verifier, "
        "protocol, audit, test, and compact result files. Raw world traces "
        "remain under their hash ledgers. Independent rehashing is required "
        "before evaluator reveal.\n\n"
        "This freeze preserves the tournament predictive-cost FAIL, original "
        "Gate-4 apparatus FAIL, and original Gate-5 derivative FAIL alongside "
        "the replacement Gate-4 PASS and amended Gate-5 PASS.\n"
    )

    for name, expected in files.items():
        if sha(ROOT / name) != expected:
            raise SystemExit(f"post-write hash mismatch: {name}")
    print(json.dumps({"freeze": "DECLARED", "files": len(files), "status": manifest["status"]}))


if __name__ == "__main__":
    main()
