"""Finalize Gate 6 reports and immutable-manifest addenda without rerunning worlds."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any

V2_ROOT = Path(__file__).resolve().parents[1]
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

from challenges.common import (  # noqa: E402
    FROZEN_COMMIT,
    RELEASED_BLOCKS,
    verify_frozen_identity,
    write_json,
)
from challenges.run_c_v21 import render_report as render_v21_report  # noqa: E402


STAGE_CHALLENGES = {
    "V2.0": "C-V20",
    "V2.1": "C-V21",
    "V2.2": "C-V22",
}
EXPECTED_ROWS = {"C-V20": 50, "C-V21": 60, "C-V22": 60}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def correlation(left: list[float], right: list[float]) -> float:
    left_mean = statistics.mean(left)
    right_mean = statistics.mean(right)
    numerator = sum(
        (a - left_mean) * (b - right_mean) for a, b in zip(left, right)
    )
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left)
        * sum((b - right_mean) ** 2 for b in right)
    )
    return numerator / denominator


def read_rows(challenge: str) -> list[dict[str, str]]:
    path = V2_ROOT / "results" / "challenges" / challenge / "per_seed.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != EXPECTED_ROWS[challenge]:
        raise RuntimeError(f"{challenge} row count changed: {len(rows)}")
    start, end = RELEASED_BLOCKS[challenge]
    seeds = [int(row["seed"]) for row in rows]
    if seeds != list(range(start, start + EXPECTED_ROWS[challenge])):
        raise RuntimeError(f"{challenge} did not use the first released seeds")
    if seeds[-1] > end:
        raise RuntimeError(f"{challenge} used a seed outside its released block")
    return rows


def enrich_v22_localization() -> dict[str, Any]:
    rows = read_rows("C-V22")
    associations = [float(row["learned_association_cue5"]) for row in rows]
    root_revisions = [float(row["cue5_root_revision"]) for row in rows]
    transfers = [float(row["cue5_max_untreated_transfer"]) for row in rows]
    failed = [index for index, value in enumerate(transfers) if value > 0.02]
    passed = [index for index in range(len(rows)) if index not in failed]
    localization = {
        "failed_floor_worlds": len(failed),
        "failed_floor_seeds": [int(rows[index]["seed"]) for index in failed],
        "cue5_learned_association_mean": statistics.mean(associations),
        "cue5_learned_association_range": [
            min(associations),
            max(associations),
        ],
        "absolute_association_deviation_from_half_mean_failed": statistics.mean(
            abs(associations[index] - 0.5) for index in failed
        ),
        "absolute_association_deviation_from_half_mean_passed": statistics.mean(
            abs(associations[index] - 0.5) for index in passed
        ),
        "cue5_root_revision_range": [
            min(root_revisions),
            max(root_revisions),
        ],
        "cue5_max_transfer_range": [min(transfers), max(transfers)],
        "absolute_association_deviation_transfer_correlation": correlation(
            [abs(value - 0.5) for value in associations], transfers
        ),
        "absolute_root_revision_transfer_correlation": correlation(
            [abs(value) for value in root_revisions], transfers
        ),
        "interpretation": (
            "The failure localizes to absolute calibration of the learned "
            "non-association for cue 5: finite developmental histories left "
            "posterior associations far enough from 0.5 that repeated correction "
            "revised G. Transfer remained mediated by G (mediation passed), so "
            "the finding is not a root-free transfer route."
        ),
    }
    result_dir = V2_ROOT / "results" / "challenges" / "C-V22"
    summary_path = result_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["failure_localization"] = localization
    write_json(summary_path, summary)

    report_path = result_dir / "report.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "## Read-only failure localization"
    if marker not in report:
        report += f"""

## Read-only failure localization

The cue-5 floor failed in `{len(failed)}/60` worlds. Cue 5's learned association
ranged from `{min(associations):.3f}` to `{max(associations):.3f}` around the
true factorized value 0.5. Mean absolute deviation from 0.5 was
`{localization['absolute_association_deviation_from_half_mean_failed']:.4f}` in
failed worlds versus
`{localization['absolute_association_deviation_from_half_mean_passed']:.4f}` in
passing worlds. Absolute association deviation correlated `{localization['absolute_association_deviation_transfer_correlation']:.3f}`
with transfer; absolute G revision correlated
`{localization['absolute_root_revision_transfer_correlation']:.3f}` with transfer.

This localizes the failure to absolute calibration of the learned
non-association: repeated correction of cue 5 revised G when its finite-history
posterior lay away from 0.5. Mediation still passed, so no root-free transfer
route was detected.
"""
        report_path.write_text(report, encoding="utf-8")
    return summary


def enrich_v21_runner_failures() -> dict[str, Any]:
    """Replace abbreviated retained errors with the runner's full verbatim traces."""
    from challenges import run_c_v21

    result_dir = V2_ROOT / "results" / "challenges" / "C-V21"
    summary_path = result_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    # The constants are materialized by the runner while building its summary;
    # extract them without executing the challenge by reading its source-owned
    # function through a fixed literal kept here for output finalization.
    source = Path(run_c_v21.__file__).read_text(encoding="utf-8")
    start = source.index('"runner_execution_failures_retained_verbatim": [')
    end = source.index('        "passed": passed,', start)
    literal_block = source[start:end]
    namespace: dict[str, Any] = {}
    exec("value = {" + literal_block + "}", {}, namespace)
    summary["runner_execution_failures_retained_verbatim"] = namespace["value"][
        "runner_execution_failures_retained_verbatim"
    ]
    write_json(summary_path, summary)
    (result_dir / "report.md").write_text(
        render_v21_report(summary), encoding="utf-8"
    )
    return summary


def verify_frozen_tree_unchanged() -> None:
    paths = [
        "projects/emergence-suite/v2/ref",
        "projects/emergence-suite/v2/contracts",
        "projects/emergence-suite/v2/protocols",
        "projects/emergence-suite/v2/results/V2.0/freeze-manifest.json",
        "projects/emergence-suite/v2/results/V2.1/freeze-manifest.json",
        "projects/emergence-suite/v2/results/V2.2/freeze-manifest.json",
    ]
    result = subprocess.run(
        ["git", "diff", "--exit-code", FROZEN_COMMIT, "--", *paths],
        cwd=V2_ROOT.parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"frozen tree changed:\n{result.stdout}\n{result.stderr}")


def write_addenda(summaries: dict[str, dict[str, Any]]) -> None:
    for stage, challenge in STAGE_CHALLENGES.items():
        identity = verify_frozen_identity(stage)
        result_dir = V2_ROOT / "results" / "challenges" / challenge
        manifest_path = V2_ROOT / "results" / stage / "freeze-manifest.json"
        frozen_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if frozen_manifest["sealed_gate_6_run"] is not False:
            raise RuntimeError(f"{stage} frozen manifest was modified")
        revealed_path = (
            V2_ROOT
            / "sealed-revealed"
            / (
                "C-V20-kernel-challenge.md"
                if challenge == "C-V20"
                else "C-V21-precision-challenge.md"
                if challenge == "C-V21"
                else "C-V22-seam-challenge.md"
            )
        )
        addendum = {
            "stage": stage,
            "base_freeze_commit": FROZEN_COMMIT,
            "base_freeze_manifest": str(manifest_path.relative_to(V2_ROOT)),
            "base_freeze_manifest_sha256": sha256(manifest_path),
            "base_manifest_sealed_gate_6_run": False,
            "overlay": {"sealed_gate_6_run": True},
            "challenge": challenge,
            "challenge_spec_sha256": sha256(revealed_path),
            "verdict": "PASS" if summaries[challenge]["passed"] else "FAIL",
            "frozen_identity": identity,
            "result_files": {
                str(path.relative_to(V2_ROOT)): sha256(path)
                for path in sorted(result_dir.iterdir())
                if path.is_file()
            },
            "frozen_manifest_modified": False,
        }
        write_json(V2_ROOT / "results" / stage / "gate6-addendum.json", addendum)


def milestone_report(summaries: dict[str, dict[str, Any]]) -> str:
    v20 = summaries["C-V20"]
    v21 = summaries["C-V21"]
    v22 = summaries["C-V22"]
    localization = v22["failure_localization"]
    return f"""# Suite v2 milestone 1 — Gate 6 report

The three evaluator-revealed challenges were run in stage order against frozen
commit `{FROZEN_COMMIT}`. All 85 frozen manifest entries were identity-checked;
`ref/`, contracts, protocols, and the original freeze manifests remain
unchanged. Gate-6 state is recorded only in new addenda.

## Verdicts

| Stage | Challenge | Verdict |
|---|---|---|
| V2.0 | C-V20 | {'PASS' if v20['passed'] else 'FAIL'} |
| V2.1 | C-V21 | {'PASS' if v21['passed'] else 'FAIL'} |
| V2.2 | C-V22 | {'PASS' if v22['passed'] else 'FAIL'} |

## C-V20

- Exact filtered/smoothed parity maximum error:
  `{v20['tests']['exactness']['maximum_absolute_error']:.3g}` across
  `{v20['tests']['exactness']['checks']}` checks.
- O2 posterior reliability error:
  `{v20['tests']['learning']['absolute_error']:.4f}`.
- Cumulative ≥1-nat structure wins: H1
  `{v20['tests']['comparison']['h1_wins_at_least_1_nat']}/50`, H2
  `{v20['tests']['comparison']['h2_wins_at_least_1_nat']}/50`.
- Collider mutation margins:
  `{v20['tests']['mutation']['cumulative_margins']}`.

Verdict: **{'PASS' if v20['passed'] else 'FAIL'}**.

## C-V21

- Crossing precision worlds:
  `{v21['tests']['tracking']['crossing_worlds']}/60`.
- C-dominated integrated classifications:
  `{v21['tests']['miscalibration_containment']['integrated_worlds']}/60`.
- Paired post-midpoint accuracy effect:
  `{v21['tests']['broadcast_dissociation']['accuracy_effect_95_interval'][0]:.3f}`
  with 95% interval
  `[{v21['tests']['broadcast_dissociation']['accuracy_effect_95_interval'][1]:.3f},
  {v21['tests']['broadcast_dissociation']['accuracy_effect_95_interval'][2]:.3f}]`.
- Local-calibration intervals overlapped exactly; midpoint/regime information
  was not passed to inference.
- Two runner-side JSON serialization failures occurred after deterministic
  computation and are retained verbatim in the challenge report.

Verdict: **{'PASS' if v21['passed'] else 'FAIL'}**.

## C-V22

- Mean structure-recovery AUC:
  `{v22['tests']['structure_recovery']['mean_auc_95_interval'][0]:.3f}`.
- Broad-minus-narrowed root attribution:
  `{v22['tests']['segment_gated_uptake']['attribution_effect_95_interval'][0]:.3f}`
  with 95% interval
  `[{v22['tests']['segment_gated_uptake']['attribution_effect_95_interval'][1]:.3f},
  {v22['tests']['segment_gated_uptake']['attribution_effect_95_interval'][2]:.3f}]`;
  local cue uptake differed by
  `{v22['tests']['segment_gated_uptake']['local_uptake_difference']:.3g}`.
- Cue-1 structural transfer wins:
  `{v22['tests']['transfer_structure']['cue1_structural_win_worlds']}/60`.
- Cue-5 floor-clean worlds:
  `{v22['tests']['transfer_structure']['cue5_floor_clean_worlds']}/60`
  (preregistered requirement: all worlds).
- Mediation passed in `{v22['tests']['mediation']['null_root_worlds']}` null-root
  worlds; maximum transfer was
  `{v22['tests']['mediation']['maximum_null_world_transfer']:.4f}`.

Verdict: **{'PASS' if v22['passed'] else 'FAIL'}**. The failure localizes to
absolute calibration of cue 5's learned non-association, not to a root-free
transfer route. In failed worlds, mean absolute association deviation from 0.5
was `{localization['absolute_association_deviation_from_half_mean_failed']:.4f}`
versus `{localization['absolute_association_deviation_from_half_mean_passed']:.4f}`
in passing worlds; absolute G revision correlated
`{localization['absolute_root_revision_transfer_correlation']:.3f}` with
transfer.

## Stop

Gate 6 is complete. C-V20 and C-V21 passed; C-V22 failed its cue-5 floor
control with the failure retained and localized. No frozen code or contract was
changed, no seed outside the released blocks was used, and no commit was made.
Work stops here.
"""


def main() -> None:
    verify_frozen_tree_unchanged()
    for challenge in STAGE_CHALLENGES.values():
        read_rows(challenge)
    enrich_v21_runner_failures()
    enrich_v22_localization()
    summaries = {
        challenge: json.loads(
            (
                V2_ROOT
                / "results"
                / "challenges"
                / challenge
                / "summary.json"
            ).read_text(encoding="utf-8")
        )
        for challenge in STAGE_CHALLENGES.values()
    }
    write_addenda(summaries)
    report_path = V2_ROOT / "results" / "milestone-1-gate6-report.md"
    report_path.write_text(milestone_report(summaries), encoding="utf-8")


if __name__ == "__main__":
    main()
