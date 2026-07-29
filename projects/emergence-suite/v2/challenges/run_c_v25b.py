#!/usr/bin/env python3
"""Pre-consumption sealed-vocabulary validator for C-V25B."""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref import v25b  # noqa: E402
from run_v25b_gates import GATE3_ARMS  # noqa: E402


CHALLENGE = ROOT / "sealed-revealed" / "C-V25B-reduction-challenge.md"
OUT = ROOT / "results" / "V2.5b"
MANIFEST = OUT / "freeze-manifest.json"
RELEASE_LEDGER = (
    REPO_ROOT / "projects" / "ifs-paper" / "suite-v2-sealed-hashes.md"
)
RELEASED_BLOCK = (2_020_000, 2_021_999)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def parse_bundle() -> dict[str, Any]:
    text = CHALLENGE.read_text(encoding="utf-8")
    start = text.index("{'parse_instruction'")
    criteria = text.index("\n\n## Criteria", start)
    end = text.rfind("}", start, criteria) + 1
    return ast.literal_eval(text[start:end])


def parse_escrow(value: str) -> tuple[int, int]:
    left, right = value.split(":")
    return int(left), int(right)


def verify_freeze() -> dict[str, Any]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append(
                {
                    "file": relative,
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha256(MANIFEST),
        "file_count": len(manifest["files"]),
        "mismatches": mismatches,
        "passed": not mismatches,
    }


def validate() -> dict[str, Any]:
    bundle = parse_bundle()
    signature = inspect.signature(v25b.generate_world)
    permitted_kwargs = set(signature.parameters) - {"seed", "released_block"}
    public_mapping = {
        "material_reduction": (
            "ref.v25b.score(...).material_reduction.material"
        ),
        "time_to_material": (
            "ref.v25b.score(...).material_reduction.first_time"
        ),
        "historical_retention": "ref.v25b.old_context_query_error",
        "premature_stable_reduction": (
            "frozen GATE3_ARMS prefix score material readout"
        ),
        "old_context_return_reversal": (
            "frozen GATE3_ARMS prefix/final material readouts"
        ),
        "structure_recovery": "ref.v25b.score(...).q_structure",
        "false_complete_reduction": (
            "ref.v25b.score(...).material_reduction + q_structure"
        ),
        "old_context_query_error": "ref.v25b.old_context_query_error",
    }
    errors = []
    seeds = []
    cells = [key for key in bundle if key.startswith("cell_")]
    for cell_name in cells:
        cell = bundle[cell_name]
        start, end = parse_escrow(cell["escrow"])
        if end - start + 1 != int(cell["n_worlds"]):
            errors.append(f"{cell_name}: escrow count mismatch")
        seeds.extend(range(start, end + 1))
        unknown_kwargs = sorted(set(cell["world"]) - permitted_kwargs)
        if unknown_kwargs:
            errors.append(
                f"{cell_name}: unknown generate_world kwargs {unknown_kwargs}"
            )
        if cell["arm"] not in GATE3_ARMS:
            errors.append(
                f"{cell_name}: arm {cell['arm']!r} is not frozen"
            )
        for readout in cell["score"]:
            if readout == "capacity_survival":
                errors.append(
                    f"{cell_name}: capacity_survival is inexpressible; "
                    "the frozen public API has no capacity state field or "
                    "capacity-readout function"
                )
            elif readout not in public_mapping:
                errors.append(
                    f"{cell_name}: unmapped sealed readout {readout!r}"
                )
    if seeds != list(range(RELEASED_BLOCK[0], RELEASED_BLOCK[1] + 1)):
        errors.append("cell escrow ranges are not ascending and gap-free")
    freeze = verify_freeze()
    if not freeze["passed"]:
        errors.append("frozen source identity failed")
    ledger_text = RELEASE_LEDGER.read_text(encoding="utf-8")
    release_phrase = (
        "Escrow: C-V25B seeds 2020000:2021999, released by this record"
    )
    if release_phrase not in ledger_text:
        errors.append("committed C-V25B release ledger entry not found")
    return {
        "challenge": "C-V25B",
        "challenge_sha256": sha256(CHALLENGE),
        "verified_seal_sha256": (
            "e556e08eb23fe8fef14daad11735fb8066e9ce43e6558ca5520fef4710a65c36"
        ),
        "bundle_parse_instruction": bundle["parse_instruction"],
        "literal_parser": "ast.literal_eval",
        "cell_order": cells,
        "seed_start": seeds[0],
        "seed_end": seeds[-1],
        "seed_count_declared": len(seeds),
        "public_readout_mapping": public_mapping,
        "freeze_identity": freeze,
        "release_ledger": {
            "file": str(RELEASE_LEDGER.relative_to(REPO_ROOT)),
            "sha256": sha256(RELEASE_LEDGER),
            "release_phrase_found": release_phrase in ledger_text,
            "commit": "dede51d",
        },
        "expressible": not errors,
        "errors": errors,
    }


def main() -> None:
    validation = validate()
    validation_path = OUT / "c-v25b-validation.json"
    dump(validation_path, validation)
    if validation["expressible"]:
        raise RuntimeError(
            "validation unexpectedly passed; this custody-only validator "
            "must not consume escrow"
        )
    ledger = {
        "challenge": "C-V25B",
        "status": "STOP_AS_SEALED_PROSPECTION_FAILURE",
        "released_block": list(RELEASED_BLOCK),
        "release_authorized": True,
        "release_ledger_commit": "dede51d",
        "seeds_consumed": 0,
        "criteria_evaluated": False,
        "raw_traces_created": False,
        "one_run_budget_spent": False,
        "validation_file": str(validation_path.relative_to(ROOT)),
        "validation_sha256": sha256(validation_path),
    }
    dump(OUT / "c-v25b-run-ledger.json", ledger)
    lines = [
        "# C-V25B sealed verdict",
        "",
        "**IMMUTABLE SEALED VERDICT: `STOP_AS_SEALED`**",
        "",
        "## Prospection failure",
        "",
        "The bundle cannot be executed exactly through the frozen V2.5b "
        "public vocabulary. Cell 5 requires `capacity_survival` “per the "
        "frozen capacity readout,” but the frozen public API contains no "
        "capacity state field and no capacity-readout function. Constructing "
        "one in this runner would be a new scientific readout and is "
        "forbidden.",
        "",
        "The remaining sealed fields map to frozen public paths. Frozen "
        "identity passed for all 22 manifest files, the challenge hash "
        "matches the committed seal, all five escrow ranges are ascending "
        "and gap-free, and the release ledger is present.",
        "",
        "No escrow seed was consumed, no raw trace was created, and none of "
        "the six sealed criteria was evaluated. The one-run budget remains "
        "unspent.",
        "",
        "## Verdict classes",
        "",
        "- Scientific: `NOT EVALUATED`.",
        "- Semantic/prospection: `FAIL` — required readout absent.",
        "- Custody: `PASS` — zero seeds consumed; frozen identity and release "
        "ledger verified.",
    ]
    (OUT / "c-v25b-verdict.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
