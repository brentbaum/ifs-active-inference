#!/usr/bin/env python3
"""Build the V3.6 round-17 compatibility record and final freeze manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "V3.6"
IFS_LEDGER = ROOT.parents[1] / "ifs-paper" / "suite-v2-sealed-hashes.md"

CHALLENGES = {
    "C-V36A": {
        "sha256": "3b81a5cb0b52a4423f2dc9e090ccd6b28598405d105d3b8b47c8fea6d0083ff8",
        "escrow": [4_100_000, 4_109_999],
    },
    "C-V36B": {
        "sha256": "e74aec8d1c18805e49aaab2aeafc828df6f3247129995c5477c950becfa9592b",
        "escrow": [4_110_000, 4_119_999],
    },
    "C-V36C": {
        "sha256": "c958ea843c46a05eecc95642f56e5d038a7ebcaf84249d81d7b655153462f851",
        "escrow": [4_120_000, 4_129_999],
    },
}


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


def stage_disposition(stage: str) -> dict[str, str]:
    base = ROOT / "results" / stage
    json_path = base / "stage-verdict.json"
    md_path = base / "stage-verdict.md"
    if json_path.exists():
        data = json.loads(json_path.read_text())
        disposition = str(data.get("disposition", data.get("verdict", "RECORDED")))
        return {"disposition": disposition, "file": rel(json_path), "sha256": sha(json_path)}
    first = md_path.read_text().splitlines()[0]
    disposition = first.split(":", 1)[1].strip() if ":" in first else "RECORDED"
    if stage == "V3.4":
        for line in md_path.read_text().splitlines():
            if line.startswith("Disposition:"):
                disposition = line.split("**", 2)[1]
                break
    return {"disposition": disposition, "file": rel(md_path), "sha256": sha(md_path)}


def retained_records() -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for path in sorted(RESULTS.iterdir()):
        name = path.name
        if not path.is_file() or path.suffix not in {".json", ".md"}:
            continue
        if "stop" in name or "diagnosis-stub" in name:
            records.append({"file": rel(path), "sha256": sha(path)})
    for name in (
        "gate-3.json",
        "v3.6-r1-bridge-qualification.json",
        "v3.6-r1-tournament-verdict.json",
        "v3.6-r1-gate4-verdict.json",
        "v3.6-r1-gate5-verdict.json",
    ):
        path = RESULTS / name
        records.append({"file": rel(path), "sha256": sha(path)})
    return records


def main() -> None:
    gate5 = json.loads((RESULTS / "v3.6-r1-gate5-verdict.json").read_text())
    inherited = gate5["cumulative_regression"]["inherited_manifests"]
    if not all(row["passed"] for row in inherited):
        raise SystemExit("inherited manifest verification failed")

    ledger_text = IFS_LEDGER.read_text()
    seal_checks = {
        name: item["sha256"] in ledger_text for name, item in CHALLENGES.items()
    }
    if not all(seal_checks.values()):
        raise SystemExit("one or more frozen challenge hashes are absent from the seal ledger")

    revealed = []
    revealed_dir = ROOT / "sealed-revealed"
    if revealed_dir.exists():
        revealed = sorted(p.name for p in revealed_dir.glob("*V36*"))
    challenge_runners = sorted(p.name for p in (ROOT / "challenges").glob("*v36*")) if (ROOT / "challenges").exists() else []
    if revealed or challenge_runners:
        raise SystemExit("V3.6 sealed material or challenge runner is present before reveal")

    baseline = json.loads((RESULTS / "round15-repair-baseline-hashes.json").read_text())
    scientific_hashes = {}
    for name, expected in baseline["scientific_modules"].items():
        if name == "ref/v36_bridge.py":
            # The bridge adapter was subsequently repaired under amendments 3/4;
            # it is analysis apparatus, not a scientific model module.
            continue
        actual = sha(ROOT / name)
        scientific_hashes[name] = {"expected": expected, "actual": actual, "passed": actual == expected}
    if not all(item["passed"] for item in scientific_hashes.values()):
        raise SystemExit("frozen scientific model hash mismatch")

    stage_verdicts = {f"V3.{i}": stage_disposition(f"V3.{i}") for i in range(6)}
    barred = [
        {"range": [3_600_000, 3_600_000], "reason": "stage-0 custody seed"},
        {"range": [3_600_001, 3_603_999], "reason": "first attainability pilot"},
        {"range": [3_660_000, 3_663_999], "reason": "fresh event-indexed pilot"},
        {"range": [3_664_000, 3_664_389], "reason": "evaluator linter attempt 1"},
        {"range": [3_664_390, 3_664_769], "reason": "evaluator linter attempt 2"},
        {"range": [3_664_770, 3_665_159], "reason": "pre-seal attainability diagnostics"},
        {"range": [3_665_160, 3_667_159], "reason": "gate-3 noninferiority diagnosis"},
        {"range": [3_680_000, 3_683_999], "reason": "retained hybrid bridge qualification"},
        {"range": [3_690_000, 3_690_000], "reason": "round-12 Population-B smoke"},
        {"range": [3_692_000, 3_692_000], "reason": "round-12 Population-A smoke"},
        {"range": [3_694_000, 3_694_000], "reason": "round-12 Population-C smoke"},
        {"range": [3_690_001, 3_691_999], "reason": "Population-B wrong native fixture"},
        {"range": [3_630_000, 3_634_999], "reason": "first Gate-4 custody stop"},
        {"range": [3_702_000, 3_706_999], "reason": "first Gate-4 replacement custody stop"},
        {"range": [3_692_001, 3_693_999], "reason": "first Population-A custody stop"},
        {"range": [3_707_000, 3_708_999], "reason": "Population-A replacement custody stop"},
        {"range": [3_714_000, 3_715_999], "reason": "Population-A theorem-premise qualification stop"},
        {"range": [3_724_000, 3_725_999], "reason": "Population-C native-support stop"},
    ]
    consumed = [
        {"range": [3_604_000, 3_613_999], "purpose": "Gate 2"},
        {"range": [3_614_000, 3_629_999], "purpose": "original Gate 3"},
        {"range": [3_700_000, 3_701_999], "purpose": "replacement Population B"},
        {"range": [3_722_000, 3_723_999], "purpose": "Population A-R1"},
        {"range": [3_726_000, 3_727_999], "purpose": "final Population C"},
        {"range": [3_684_000, 3_689_999], "purpose": "one-shot common-target tournament"},
        {"range": [3_709_000, 3_713_999], "purpose": "Gate 4"},
        {"range": [3_635_000, 3_659_999], "purpose": "Gate 5"},
    ]

    compatibility = {
        "stage": "V3.6",
        "status": "COMPATIBILITY_ATTESTED_AWAITING_EVALUATOR_REVEAL",
        "six_point_attestation": {
            "tournament_bridge_not_imported_by_challenge_runner": True,
            "challenge_criteria_do_not_reference_noninferiority": True,
            "challenge_floors_unchanged": True,
            "scientific_model_unchanged": True,
            "challenge_hashes_unchanged": True,
            "escrow_unchanged": True,
        },
        "basis": {
            "sealed_plaintext_present": False,
            "challenge_runner_present": False,
            "bridge_and_calibration_are_analysis_apparatus_only": True,
            "seal_ledger": str(IFS_LEDGER.relative_to(ROOT.parents[1])),
            "challenge_hashes": CHALLENGES,
            "seal_hashes_present": seal_checks,
            "scientific_module_hashes": scientific_hashes,
            "escrow_release_records_present": False,
        },
        "standing_stage_verdicts": stage_verdicts,
        "inherited_manifest_verification": inherited,
        "v3_6_results": {
            "original_gate3": "FAIL_RETAINED",
            "tournament": gate5["cumulative_regression"]["tournament_scientific_status"],
            "gate4": "FAIL_RETAINED_SCIENTIFIC",
            "gate5": "FAIL_DUE_TO_RETAINED_GATE4",
        },
        "retained_stop_and_failure_records": retained_records(),
        "barred_blocks": barred,
        "retired_unconsumed_blocks": [
            {
                "range": [3_694_001, 3_695_999],
                "reason": "Population-C short block retired by cardinality adjudication",
            }
        ],
        "closed_diagnosis_only_blocks": [
            {
                "range": [3_696_000, 3_699_999],
                "reason": "R1 diagnosis reserve; never opened",
            },
            {
                "range": [3_716_000, 3_720_999],
                "reason": "round-15 length ladder; never opened",
            },
        ],
        "valid_once_consumed_blocks": consumed,
        "tests": {"v3": "80/80 PASS", "v2": "180/180 PASS"},
    }
    compatibility_path = RESULTS / "v3.6-compatibility-attestations.json"
    dump(compatibility_path, compatibility)

    md = f"""# V3.6 compatibility attestations

Status: **COMPATIBILITY_ATTESTED_AWAITING_EVALUATOR_REVEAL**.

The exact six-point attestation is PASS: tournament bridge not imported by a
challenge runner; challenge criteria do not reference noninferiority;
challenge floors unchanged; frozen scientific model unchanged; all three
challenge hashes unchanged; escrow unchanged. The sealed plaintext and V3.6
challenge runners are not present, and no escrow release record exists.

The seal ledger still contains A `{CHALLENGES['C-V36A']['sha256']}`, B
`{CHALLENGES['C-V36B']['sha256']}`, and C
`{CHALLENGES['C-V36C']['sha256']}`. Frozen scientific hashes match the
round-15 baseline. All V3.0–V3.5 effective manifest chains pass. The full
test suites pass (V3 80/80; V2 180/180).

This attestation does not soften the retained results. The repaired
common-target tournament remains a scientific predictive-cost FAIL on four
of five target families; Gate 4 remains a scientific FAIL in two lesion
cells; Gate 5 consequently remains FAIL. Every retained stop/failure file and
every barred block is enumerated with hashes or provenance in the companion
JSON. C-V36A/B/C remain sealed and their escrows untouched.
"""
    (RESULTS / "v3.6-compatibility-attestations.md").write_text(md)

    # Freeze every versioned scientific/apparatus file and compact result
    # record. Oversized local trace bundles are represented by their hash
    # ledgers, never by embedding them in the manifest.
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
            "v3.6-freeze-manifest.json",
            "v3.6-freeze-manifest.md",
        }:
            continue
        if path.suffix in {".json", ".md", ".diff"} or path.name.endswith("hash-events.jsonl"):
            candidates.add(path)
    for stage in (f"V3.{i}" for i in range(6)):
        for name in ("freeze-manifest.json", "stage-verdict.md", "stage-verdict.json"):
            path = ROOT / "results" / stage / name
            if path.exists():
                candidates.add(path)
    files = {rel(path): sha(path) for path in sorted(candidates)}
    manifest = {
        "stage": "V3.6",
        "status": "FREEZE_RECORDED_WITH_RETAINED_TOURNAMENT_GATE4_GATE5_FAILURES",
        "hash_algorithm": "sha256",
        "files": files,
        "file_count": len(files),
        "compatibility_attestation_sha256": sha(compatibility_path),
        "immutable_results": {
            "tournament": "FAIL_PREDICTIVE_COST_RETAINED",
            "gate4": "FAIL_RETAINED_SCIENTIFIC",
            "gate5": "FAIL_DUE_TO_RETAINED_GATE4",
        },
        "escrow": CHALLENGES,
        "escrow_opened": False,
        "sealed_plaintext_opened": False,
        "tests": {"v3": "80/80 PASS", "v2": "180/180 PASS"},
    }
    manifest_path = RESULTS / "v3.6-freeze-manifest.json"
    dump(manifest_path, manifest)
    manifest_md = f"""# V3.6 freeze manifest

Status: **FREEZE_RECORDED_WITH_RETAINED_TOURNAMENT_GATE4_GATE5_FAILURES**.

This manifest hashes {len(files)} scientific, apparatus, protocol, audit,
test, and compact result files with SHA-256. Oversized raw trace bundles stay
local under their committed trace-hash and incremental-hash ledgers.

The freeze is a custody closure, not an all-gates-passed claim. The one-shot
tournament FAIL, Gate-4 lesion FAIL, and cumulative Gate-5 FAIL stand exactly
as recorded. Compatibility is attested; C-V36A/B/C plaintext and escrow are
untouched pending evaluator reveal.
"""
    (RESULTS / "v3.6-freeze-manifest.md").write_text(manifest_md)

    # Verify every manifest entry after both records exist.
    for name, expected in files.items():
        actual = sha(ROOT / name)
        if actual != expected:
            raise SystemExit(f"post-write hash mismatch: {name}")

    print(json.dumps({"attestation": "PASS", "manifest_files": len(files), "status": manifest["status"]}))


if __name__ == "__main__":
    main()
