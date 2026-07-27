"""Invalidate-and-repeat C-V23b with the authorized V2.3.1r instrument."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from challenges import run_c_v23b as original  # noqa: E402


RESULT_DIR = ROOT / "results" / "challenges" / "C-V23b-repaired-instrument"
FREEZE_COMMIT = "7d5650c"
AUTHORIZED_REPAIR = "ref/v231.py"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repaired_identity() -> dict[str, object]:
    manifest_relative = (
        "projects/emergence-suite/v2/results/V2.3.1/freeze-manifest.json"
    )
    committed_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:{manifest_relative}"], cwd=REPO
    )
    committed = json.loads(committed_bytes)
    local_manifest = json.loads(
        (ROOT / "results" / "V2.3.1" / "freeze-manifest.json").read_text()
    )
    if local_manifest != committed:
        raise RuntimeError("the frozen V2.3.1 manifest itself changed")

    mismatches = []
    for path, expected in committed["files"].items():
        actual = sha256_bytes((ROOT / path).read_bytes())
        if actual != expected:
            mismatches.append(
                {"path": path, "expected": expected, "actual": actual}
            )
    if [item["path"] for item in mismatches] != [AUTHORIZED_REPAIR]:
        raise RuntimeError(f"unexpected frozen-file mismatches: {mismatches}")

    parameter_path = "protocols/v2.3.1-parameters.json"
    if sha256_bytes((ROOT / parameter_path).read_bytes()) != committed["files"][
        parameter_path
    ]:
        raise RuntimeError("V2.3.1 parameter block changed")
    bound = float(committed["step_injection_bound"]["value"])
    return {
        "commit": FREEZE_COMMIT,
        "manifest_path": manifest_relative,
        "manifest_sha256": sha256_bytes(committed_bytes),
        "verified_file_count": len(committed["files"]),
        "authorized_repair_mismatch": mismatches[0],
        "parameters_unchanged": True,
        "frozen_p99_exact": bound,
        "frozen_p99_reported": original.P99_BOUND_REPORTED,
        "instrument": "V2.3.1r",
        "status": "PASS",
    }


def write_repaired_metadata(exit_code: int) -> None:
    summary_path = RESULT_DIR / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["challenge_label"] = "C-V23b (repaired instrument)"
    summary["instrument"] = "V2.3.1r"
    summary["invalidate_and_repeat"] = True
    summary["original_defective_result"] = "results/challenges/C-V23b/"
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )

    report_path = RESULT_DIR / "report.md"
    report = report_path.read_text()
    report = report.replace(
        "# C-V23b formation challenge report",
        "# C-V23b (repaired instrument) formation challenge report",
        1,
    )
    report += (
        "\n## Invalidate-and-repeat status\n\n"
        "This is the authorized V2.3.1r instrument repeat. The original "
        "defective-instrument C-V23b verdict remains at "
        "`results/challenges/C-V23b/` and is not overwritten. The repair "
        "changes only candidate evidence normalization; the frozen "
        "parameters, protocol, seeds, stream family, thresholds, and p99 "
        "reference are unchanged.\n"
    )
    report_path.write_text(report)

    files = [
        ROOT / "challenges" / "run_c_v23b_repaired.py",
        RESULT_DIR / "per_seed.csv",
        summary_path,
        report_path,
    ]
    addendum = {
        "challenge": "C-V23b (repaired instrument)",
        "instrument": "V2.3.1r",
        "invalidate_and_repeat": True,
        "runner_exit_code": exit_code,
        "verdict": summary["verdict"],
        "identity": summary["identity"],
        "original_defective_result": "results/challenges/C-V23b/",
        "files": {
            str(path.relative_to(ROOT)): sha256_bytes(path.read_bytes())
            for path in files
        },
    }
    addendum_path = ROOT / "results" / "V2.3.1r" / "c-v23b-addendum.json"
    addendum_path.write_text(
        json.dumps(addendum, indent=2, sort_keys=True) + "\n"
    )


def main() -> int:
    original.RESULT_DIR = RESULT_DIR
    original.verify_freeze_identity = repaired_identity
    original.write_addendum = lambda summary: None
    original.write_milestone_update = lambda summary: None
    exit_code = original.main()
    write_repaired_metadata(exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
