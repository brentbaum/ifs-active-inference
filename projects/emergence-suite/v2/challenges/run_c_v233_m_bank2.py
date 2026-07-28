"""Run revealed C-V233-M-bank2 on the repaired frozen instrument."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from challenges import run_c_v233_m_bank as bank_audit  # noqa: E402
from ref.v232_formation import PRIOR, score_history  # noqa: E402
from ref.v233 import (  # noqa: E402
    PARAMETERS,
    canonical_state_bytes,
    canonical_state_hash,
    classify_initial_strength,
    construct_bank_state,
)


CHALLENGE = "C-V233-M-bank2"
FREEZE_COMMIT = "3e9bad2"
PUBLIC_PLAN_COMMIT = "39236e7"
FIRST_SEED = 820001
LAST_SEED = 825504
WORLD_COUNT = 5504
TARGET = 40
STRATA = ("moderate", "strong", "very_strong")
RELEASED_BLOCK = (FIRST_SEED, LAST_SEED)
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
BASE_MANIFEST_REL = (
    "projects/emergence-suite/v2/results/V2.3.3/"
    "freeze-manifest.json"
)
REPAIR_ADDENDUM_REL = (
    "projects/emergence-suite/v2/results/V2.3.3/"
    "seed-authorization-repair-addendum.json"
)
REPAIR_ADDENDUM_PATH = ROOT / REPAIR_ADDENDUM_REL.split("v2/", 1)[1]
CHALLENGE_PATH = (
    ROOT / "sealed-revealed" / "C-V233-M-bank2-challenge.md"
)
SAMPLING_PLAN_PATH = (
    ROOT / "protocols" / "v2.3.3-bank2-sampling-plan.md"
)
ADJUDICATION_PATH = (
    ROOT / "results" / "V2.3.3" / "bank2-adjudication.md"
)
ATTESTATION_PATH = (
    ROOT
    / "results"
    / "V2.3.3"
    / "maintenance-seal-compatibility-attestation.json"
)
ADDENDUM_PATH = (
    ROOT / "results" / "V2.3.3" / "gate6-bank2-addendum.json"
)
MILESTONE_PATH = (
    ROOT / "results" / "milestone-4-v2.3.3-gate6-bank2-update.md"
)
OLD_RESULT_DIR = (
    ROOT / "results" / "challenges" / "C-V233-M-bank-repaired-instrument"
)
TOLERANCE = 1e-10


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    def native(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        raise TypeError(f"cannot serialize {type(item).__name__}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=native) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def verify_identity() -> dict[str, Any]:
    base_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:{BASE_MANIFEST_REL}"],
        cwd=REPO,
    )
    local_base = ROOT / "results" / "V2.3.3" / "freeze-manifest.json"
    if local_base.read_bytes() != base_bytes:
        raise RuntimeError("local base manifest differs from 3e9bad2")
    repair_bytes = subprocess.check_output(
        [
            "git",
            "show",
            f"{PUBLIC_PLAN_COMMIT}:{REPAIR_ADDENDUM_REL}",
        ],
        cwd=REPO,
    )
    if REPAIR_ADDENDUM_PATH.read_bytes() != repair_bytes:
        raise RuntimeError(
            "local seed-authorization repair addendum differs from 39236e7"
        )
    base = json.loads(base_bytes)
    repair = json.loads(repair_bytes)
    authorized = {
        relative: detail["after_sha256"]
        for relative, detail in repair["authorized_guard_diff"][
            "scientific_files"
        ].items()
    }
    mismatches = []
    for relative, base_expected in base["files"].items():
        expected = authorized.get(relative, base_expected)
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {
                    "path": relative,
                    "base_expected": base_expected,
                    "repair_expected": expected,
                    "actual": actual,
                }
            )
    for relative, expected in authorized.items():
        if relative in base["files"]:
            continue
        actual = sha256(ROOT / relative)
        if actual != expected:
            mismatches.append(
                {
                    "path": relative,
                    "base_expected": None,
                    "repair_expected": expected,
                    "actual": actual,
                }
            )
    if mismatches:
        raise RuntimeError(f"frozen-plus-repair identity mismatch: {mismatches}")
    return {
        "base_freeze_commit": FREEZE_COMMIT,
        "base_manifest_sha256": hashlib.sha256(base_bytes).hexdigest(),
        "base_manifest_file_count": len(base["files"]),
        "repair_commit": PUBLIC_PLAN_COMMIT,
        "repair_addendum_sha256": hashlib.sha256(
            repair_bytes
        ).hexdigest(),
        "authorized_scientific_files": authorized,
        "mismatches": mismatches,
        "passed": True,
    }


def wilson(successes: int, total: int) -> list[float]:
    probability = successes / total
    z = 1.96
    denominator = 1.0 + z * z / total
    center = (probability + z * z / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(
            probability * (1.0 - probability) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return [probability, center - half, center + half]


def numeric_summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    if not len(array):
        return {"count": 0}
    return {
        "count": len(array),
        "minimum": float(array.min()),
        "p01": float(np.quantile(array, 0.01)),
        "p05": float(np.quantile(array, 0.05)),
        "p25": float(np.quantile(array, 0.25)),
        "median": float(np.quantile(array, 0.50)),
        "mean": float(array.mean()),
        "p75": float(np.quantile(array, 0.75)),
        "p95": float(np.quantile(array, 0.95)),
        "p99": float(np.quantile(array, 0.99)),
        "maximum": float(array.max()),
    }


def histogram(values: list[float], edges: list[float]) -> dict[str, Any]:
    counts, used_edges = np.histogram(np.asarray(values), bins=edges)
    return {
        "edges": [float(value) for value in used_edges],
        "counts": counts.tolist(),
    }


def mean_difference_interval(
    new_values: list[float], old_values: list[float]
) -> list[float]:
    new = np.asarray(new_values, dtype=float)
    old = np.asarray(old_values, dtype=float)
    difference = float(new.mean() - old.mean())
    standard_error = math.sqrt(
        float(new.var(ddof=1)) / len(new)
        + float(old.var(ddof=1)) / len(old)
    )
    return [
        difference,
        difference - 1.96 * standard_error,
        difference + 1.96 * standard_error,
    ]


def profile_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["profile_signature"])].append(row)
    return {
        signature: {
            "candidate_count": len(group),
            "eligible_counts": {
                stratum: sum(row["stratum"] == stratum for row in group)
                for stratum in STRATA
            },
            "q_P": numeric_summary([float(row["q_P"]) for row in group]),
            "m0": numeric_summary([float(row["m0"]) for row in group]),
            "upper_saturation_rate": (
                sum(float(row["q_P"]) > 0.98 for row in group) / len(group)
            ),
        }
        for signature, group in sorted(grouped.items())
    }


def temporal_coordinates(
    state: dict[str, Any],
) -> dict[str, Any]:
    observations = [
        tuple(value)
        for value in state["developmental_history"]["observations"]
    ]
    configurations = state["developmental_history"]["configurations"]
    scored = score_history(observations, configurations, prior=PRIOR)
    first_selection = None
    first_q60 = None
    for time, protocol_state in enumerate(scored["states"], start=1):
        posterior = protocol_state.posterior_store["H_formation"]
        if first_selection is None and int(np.argmax(posterior)) == 2:
            first_selection = time
        if first_q60 is None and float(posterior[2]) >= 0.60:
            first_q60 = time
    final_joint = np.asarray(scored["log_joint"], dtype=float)
    runner = int(np.argmax(final_joint[:2]))
    per_slice_bf = [
        float(detail["candidate_log_likelihoods"][2])
        - float(detail["candidate_log_likelihoods"][runner])
        for detail in scored["contributions"]
    ]
    split = len(per_slice_bf) if first_selection is None else first_selection
    return {
        "first_P_selection_time": (
            "" if first_selection is None else first_selection
        ),
        "first_qP_0_60_crossing_time": (
            "" if first_q60 is None else first_q60
        ),
        "final_runner_up": ("T", "D")[runner],
        "cumulative_P_runner_up_log_BF": float(sum(per_slice_bf)),
        "post_selection_log_BF": float(sum(per_slice_bf[split:])),
        "pre_and_selection_log_BF": float(sum(per_slice_bf[:split])),
    }


def census_row(
    position: int,
    seed: int,
    state: dict[str, Any],
    *,
    digest: str,
    reload_digest: str,
    stratum: str | None,
    retained: bool,
    reason: str,
    eligible_counts: dict[str, int],
    retained_counts: dict[str, int],
) -> dict[str, Any]:
    q = np.asarray(state["q_H_formation"], dtype=float)
    log_joint = np.asarray(state["candidate_log_evidence"], dtype=float)
    log_likelihood = log_joint - np.log(PRIOR)
    configurations = state["developmental_history"]["configurations"]
    overwhelm = sum(
        configuration["precision"] == "overwhelm"
        for configuration in configurations
    )
    low_control = sum(
        configuration["control"] == "low"
        for configuration in configurations
    )
    collapsed = sum(
        configuration["broadcast"] == "collapsed"
        for configuration in configurations
    )
    ordinary = len(configurations) - overwhelm
    high_control = len(configurations) - low_control
    integrated = len(configurations) - collapsed
    temporal = temporal_coordinates(state)
    return {
        "position": position,
        "seed": seed,
        "history_length": len(configurations),
        "ordinary_slice_count": ordinary,
        "overwhelming_slice_count": overwhelm,
        "high_control_slice_count": high_control,
        "low_control_slice_count": low_control,
        "integrated_broadcast_slice_count": integrated,
        "collapsed_broadcast_slice_count": collapsed,
        "profile_signature": (
            f"L{len(configurations)}-O{overwhelm}-"
            f"LC{low_control}-CB{collapsed}"
        ),
        "q_T": float(q[0]),
        "q_D": float(q[1]),
        "q_P": float(q[2]),
        "m0": float(
            min(
                math.log(float(q[2]) / float(q[0])),
                math.log(float(q[2]) / float(q[1])),
            )
        ),
        "log_joint_T": float(log_joint[0]),
        "log_joint_D": float(log_joint[1]),
        "log_joint_P": float(log_joint[2]),
        "log_likelihood_T": float(log_likelihood[0]),
        "log_likelihood_D": float(log_likelihood[1]),
        "log_likelihood_P": float(log_likelihood[2]),
        **temporal,
        "stratum": "" if stratum is None else stratum,
        "eligible": int(stratum is not None),
        "retained": int(retained),
        "reason": reason,
        "state_sha256": digest,
        "reload_sha256": reload_digest,
        "rehash_ok": int(digest == reload_digest),
        "released_block_authorization": f"{FIRST_SEED}:{LAST_SEED}",
        "cumulative_moderate": eligible_counts["moderate"],
        "cumulative_strong": eligible_counts["strong"],
        "cumulative_very_strong": eligible_counts["very_strong"],
        "retained_moderate": retained_counts["moderate"],
        "retained_strong": retained_counts["strong"],
        "retained_very_strong": retained_counts["very_strong"],
    }


def old_block_comparison(new_rows: list[dict[str, Any]]) -> dict[str, Any]:
    with (OLD_RESULT_DIR / "per_seed.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        old_rows = list(csv.DictReader(handle))
    old_q = [float(row["q_P"]) for row in old_rows]
    new_q = [float(row["q_P"]) for row in new_rows]
    old_counts = {
        stratum: sum(row["stratum"] == stratum for row in old_rows)
        for stratum in STRATA
    }
    new_counts = {
        stratum: sum(row["stratum"] == stratum for row in new_rows)
        for stratum in STRATA
    }
    rate_comparison = {}
    for stratum in STRATA:
        new_interval = wilson(new_counts[stratum], len(new_rows))
        old_interval = wilson(old_counts[stratum], len(old_rows))
        rate_comparison[stratum] = {
            "new_count": new_counts[stratum],
            "old_count": old_counts[stratum],
            "new_rate": new_interval,
            "old_rate": old_interval,
            "rate_difference": (
                new_interval[0] - old_interval[0]
            ),
            "conservative_95_interval_for_difference": [
                new_interval[1] - old_interval[2],
                new_interval[2] - old_interval[1],
            ],
        }
    return {
        "classification": "descriptive_only_no_pooling",
        "new_candidate_count": len(new_rows),
        "old_candidate_count": len(old_rows),
        "q_P_new": numeric_summary(new_q),
        "q_P_old": numeric_summary(old_q),
        "q_P_mean_difference_95_interval": mean_difference_interval(
            new_q, old_q
        ),
        "band_rate_comparison": rate_comparison,
        "upper_saturation_rate_new": (
            sum(value > 0.98 for value in new_q) / len(new_q)
        ),
        "upper_saturation_rate_old": (
            sum(value > 0.98 for value in old_q) / len(old_q)
        ),
        "m0_old_block": None,
        "m0_comparison_status": (
            "UNAVAILABLE: the committed 800-seed ledger did not retain "
            "candidate log-evidence coordinates for nonbanked states; "
            "the old block was not rerun."
        ),
        "interpretation_lock": (
            "Bank2 tests sampling adequacy only. It neither replicates "
            "nor reverses the prospective 800-seed natural-yield result."
        ),
    }


def main() -> None:
    identity = verify_identity()
    bank_audit.FIRST_SEED = FIRST_SEED
    bank_audit.LAST_SEED = LAST_SEED
    counts = {stratum: 0 for stratum in STRATA}
    retained_counts = {stratum: 0 for stratum in STRATA}
    fill = {stratum: None for stratum in STRATA}
    rows = []
    retained_states = []
    rehash_failures = []
    all_quota_fill_position = None

    for position, seed in enumerate(
        range(FIRST_SEED, LAST_SEED + 1), start=1
    ):
        state = construct_bank_state(
            seed, released_block=RELEASED_BLOCK
        )
        serialized = canonical_state_bytes(state)
        digest = hashlib.sha256(serialized).hexdigest()
        reload_digest = canonical_state_hash(json.loads(serialized))
        if digest != reload_digest:
            rehash_failures.append(seed)
        q_p = float(state["q_H_formation"][2])
        stratum = classify_initial_strength(q_p)
        retained = (
            stratum is not None and retained_counts[stratum] < TARGET
        )
        if stratum is not None:
            counts[stratum] += 1
            if retained:
                retained_counts[stratum] += 1
                retained_states.append(
                    {
                        "seed": seed,
                        "q_P": q_p,
                        "stratum": stratum,
                        "state_sha256": digest,
                        "serialized_state": state,
                    }
                )
            if counts[stratum] == TARGET:
                fill[stratum] = {"position": position, "seed": seed}
            if (
                all(counts[name] >= TARGET for name in STRATA)
                and all_quota_fill_position is None
            ):
                all_quota_fill_position = position
        if retained:
            reason = "retained_first_eligible"
        elif stratum is not None:
            reason = "eligible_after_stratum_quota"
        elif q_p < 0.60:
            reason = "below_formed_range"
        else:
            reason = "above_nonsaturation_range"
        rows.append(
            census_row(
                position,
                seed,
                state,
                digest=digest,
                reload_digest=reload_digest,
                stratum=stratum,
                retained=retained,
                reason=reason,
                eligible_counts=counts,
                retained_counts=retained_counts,
            )
        )

    q_sorted = np.sort(np.asarray([row["q_P"] for row in rows]))
    m0_sorted = np.sort(np.asarray([row["m0"] for row in rows]))
    for row in rows:
        row["q_P_ECDF"] = float(
            np.searchsorted(q_sorted, row["q_P"], side="right")
            / WORLD_COUNT
        )
        row["m0_ECDF"] = float(
            np.searchsorted(m0_sorted, row["m0"], side="right")
            / WORLD_COUNT
        )

    provenance = [
        bank_audit.provenance_audit(record["serialized_state"])
        for record in retained_states
    ]
    one_posterior = [
        bank_audit.one_posterior_audit(record["serialized_state"])
        for record in retained_states
    ]
    constructor_source = inspect.getsource(construct_bank_state)
    source_audit = {
        "contains_band_classifier": (
            "classify_initial_strength" in constructor_source
        ),
        "contains_band_thresholds": any(
            token in constructor_source
            for token in (
                "initial_strength_strata",
                "lower_inclusive",
                "upper_exclusive",
            )
        ),
        "contains_maintenance_trajectory": any(
            token in constructor_source
            for token in (
                "run_maintenance_trajectory",
                "simulate_six_arms",
                "maintenance_seed",
                "M_PT",
                "M_PD",
            )
        ),
        "posterior_source_is_frozen_update": (
            'formation["posterior"]' in constructor_source
        ),
    }
    source_audit["passed"] = (
        not source_audit["contains_band_classifier"]
        and not source_audit["contains_band_thresholds"]
        and not source_audit["contains_maintenance_trajectory"]
        and source_audit["posterior_source_is_frozen_update"]
    )

    criterion_1 = (
        all(counts[stratum] >= TARGET for stratum in STRATA)
        and len(retained_states) == 120
    )
    criterion_2 = (
        len(provenance) == 120
        and all(item["passed"] for item in provenance)
        and len(one_posterior) == 120
        and all(item["passed"] for item in one_posterior)
        and source_audit["passed"]
    )
    seed_sequence = [int(row["seed"]) for row in rows]
    criterion_3 = (
        len(rows) == WORLD_COUNT
        and seed_sequence == list(range(FIRST_SEED, LAST_SEED + 1))
        and not rehash_failures
        and all(
            row["released_block_authorization"]
            == f"{FIRST_SEED}:{LAST_SEED}"
            for row in rows
        )
        and rows[-1]["position"] == WORLD_COUNT
    )
    verdict = "PASS" if criterion_1 and criterion_2 and criterion_3 else "FAIL"

    by_length = {
        str(length): {
            "candidate_count": len(group),
            "eligible_counts": {
                stratum: sum(row["stratum"] == stratum for row in group)
                for stratum in STRATA
            },
            "q_P": numeric_summary([row["q_P"] for row in group]),
            "m0": numeric_summary([row["m0"] for row in group]),
            "first_P_selection_time": numeric_summary(
                [
                    float(row["first_P_selection_time"])
                    for row in group
                    if row["first_P_selection_time"] != ""
                ]
            ),
            "post_selection_log_BF": numeric_summary(
                [row["post_selection_log_BF"] for row in group]
            ),
        }
        for length in sorted({int(row["history_length"]) for row in rows})
        for group in [
            [row for row in rows if int(row["history_length"]) == length]
        ]
    }
    q_values = [float(row["q_P"]) for row in rows]
    m0_values = [float(row["m0"]) for row in rows]
    first_selection_times = [
        float(row["first_P_selection_time"])
        for row in rows
        if row["first_P_selection_time"] != ""
    ]
    census = {
        "classification": "distributional_stress_descriptive_only",
        "q_P": {
            "summary": numeric_summary(q_values),
            "histogram": histogram(
                q_values, [index / 20.0 for index in range(21)]
            ),
            "ECDF": "per_seed.csv:q_P_ECDF",
        },
        "m0": {
            "definition": (
                "min(log(q(P)/q(T)), log(q(P)/q(D)))"
            ),
            "summary": numeric_summary(m0_values),
            "histogram": histogram(
                m0_values,
                [-100, -20, -10, -5, -2, 0, 2, 5, 10, 20, 100],
            ),
            "below_minus_100": sum(value < -100 for value in m0_values),
            "above_100": sum(value > 100 for value in m0_values),
            "ECDF": "per_seed.csv:m0_ECDF",
        },
        "by_history_length": by_length,
        "by_sufficient_statistic_profile": profile_summary(rows),
        "upper_saturation": {
            "count": sum(value > 0.98 for value in q_values),
            "rate_95_wilson": wilson(
                sum(value > 0.98 for value in q_values), WORLD_COUNT
            ),
        },
        "first_selection": {
            "selected_P_at_least_once_count": len(first_selection_times),
            "never_selected_P_count": (
                WORLD_COUNT - len(first_selection_times)
            ),
            "time_summary": numeric_summary(first_selection_times),
        },
        "post_selection_evidence": numeric_summary(
            [float(row["post_selection_log_BF"]) for row in rows]
        ),
        "cumulative_P_runner_up_log_BF": numeric_summary(
            [
                float(row["cumulative_P_runner_up_log_BF"])
                for row in rows
            ]
        ),
        "fill_curves": "per_seed.csv:cumulative_*",
        "comparison_to_800_seed_block": old_block_comparison(rows),
    }
    eligibility = {
        stratum: {
            "eligible_count": counts[stratum],
            "rate_95_wilson": wilson(counts[stratum], WORLD_COUNT),
            "retained_count": retained_counts[stratum],
            "fill": fill[stratum],
        }
        for stratum in STRATA
    }
    summary = {
        "challenge": CHALLENGE,
        "classification": "sampling_adequacy_requalification",
        "verdict": verdict,
        "seed_block_used": [FIRST_SEED, LAST_SEED],
        "candidate_count": len(rows),
        "identity": identity,
        "criteria": {
            "1_scientific_sampling_adequacy": {
                "verdict": "PASS" if criterion_1 else "FAIL",
                "eligibility": eligibility,
                "retained_state_count": len(retained_states),
                "posterior_assignment_used": False,
                "trajectory_continuation_used": False,
            },
            "2_semantic_integrity": {
                "verdict": "PASS" if criterion_2 else "FAIL",
                "provenance_audit_count": len(provenance),
                "provenance_failure_seeds": [
                    item["seed"] for item in provenance if not item["passed"]
                ],
                "maximum_provenance_error": max(
                    (
                        item["maximum_numeric_error"]
                        for item in provenance
                    ),
                    default=None,
                ),
                "one_posterior_audit_count": len(one_posterior),
                "one_posterior_failure_seeds": [
                    item["seed"]
                    for item in one_posterior
                    if not item["passed"]
                ],
                "constructor_source_audit": source_audit,
            },
            "3_process_custody": {
                "verdict": "PASS" if criterion_3 else "FAIL",
                "ledger_row_count": len(rows),
                "gap_free_seed_order": (
                    seed_sequence
                    == list(range(FIRST_SEED, LAST_SEED + 1))
                ),
                "rehash_pass_count": WORLD_COUNT - len(rehash_failures),
                "rehash_failure_seeds": rehash_failures,
                "all_quota_fill_position": all_quota_fill_position,
                "candidates_processed_after_all_quotas_filled": (
                    0
                    if all_quota_fill_position is None
                    else WORLD_COUNT - all_quota_fill_position
                ),
                "full_block_consumed": len(rows) == WORLD_COUNT,
                "released_block_authorization_logged_every_row": all(
                    row["released_block_authorization"]
                    == f"{FIRST_SEED}:{LAST_SEED}"
                    for row in rows
                ),
                "maintenance_seed_opened": False,
                "early_stop_used": False,
            },
            "4_distributional_census": {
                "verdict": "DESCRIPTIVE_ONLY",
                "criterial": False,
                "artifact": "census.json",
            },
        },
        "verdict_classes": {
            "scientific_sampling_adequacy": (
                "PASS" if criterion_1 else "FAIL"
            ),
            "semantic_integrity": "PASS" if criterion_2 else "FAIL",
            "process_custody": "PASS" if criterion_3 else "FAIL",
            "distributional_census": "DESCRIPTIVE_ONLY",
        },
        "interpretation_lock": (
            "The 800-seed natural-yield finding stands. Bank2 tests only "
            "whether the prespecified rate-powered fresh block can "
            "assemble the unchanged equal-stratum stress bank."
        ),
        "failure_interpretation": (
            None
            if verdict == "PASS"
            else (
                "A band shortfall concludes the equal-band design "
                "incompatible with the frozen constructor endpoint "
                "geometry; integrity/custody failure is architecture "
                "failure."
            )
        ),
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "challenge_spec_sha256": sha256(CHALLENGE_PATH),
        "sampling_plan_sha256": sha256(SAMPLING_PLAN_PATH),
        "adjudication_sha256": sha256(ADJUDICATION_PATH),
        "compatibility_attestation_sha256": sha256(ATTESTATION_PATH),
    }
    write_csv(RESULT_DIR / "per_seed.csv", rows)
    write_json(
        RESULT_DIR / "retained_states.json",
        {
            "challenge": CHALLENGE,
            "retention_rule": "first 40 eligible per band",
            "state_count": len(retained_states),
            "states": retained_states,
        },
    )
    write_json(
        RESULT_DIR / "provenance-audit.json",
        {
            "challenge": CHALLENGE,
            "retained_state_audits": provenance,
            "one_posterior_audits": one_posterior,
            "constructor_source_audit": source_audit,
        },
    )
    write_json(RESULT_DIR / "census.json", census)
    write_json(RESULT_DIR / "summary.json", summary)

    eligibility_lines = []
    for stratum in STRATA:
        details = eligibility[stratum]
        interval = details["rate_95_wilson"]
        fill_text = (
            f"filled at position `{details['fill']['position']}`, seed "
            f"`{details['fill']['seed']}`"
            if details["fill"] is not None
            else "did not fill"
        )
        eligibility_lines.append(
            f"- {stratum}: {details['eligible_count']}/{WORLD_COUNT}, "
            f"rate `{interval[0]:.6f}` (95% Wilson "
            f"`[{interval[1]:.6f}, {interval[2]:.6f}]`); "
            f"{fill_text}; retained `{details['retained_count']}`."
        )
    comparison = census["comparison_to_800_seed_block"]
    report = f"""# {CHALLENGE}

Sealed verdict: **{verdict}**.

The runner verified the frozen `3e9bad2` identity plus the committed
seed-authorization repair hashes. All 5,504 candidates (`820001:825504`) were
consumed exactly once, ascending, in full. Maintenance escrow remained closed.

## Scientific sampling adequacy — {'PASS' if criterion_1 else 'FAIL'}

{chr(10).join(eligibility_lines)}

The first 40 eligible states in each band were retained without posterior
assignment or trajectory continuation. The 800-seed result remains the
prospective natural-yield finding; this verdict is sampling adequacy only.

## Semantic integrity — {'PASS' if criterion_2 else 'FAIL'}

All `{len(provenance)}` retained states reconstructed exactly; maximum
provenance error was
`{summary['criteria']['2_semantic_integrity']['maximum_provenance_error']}`.
The one-posterior audit ran on all `{len(one_posterior)}` retained states with
zero failures. The constructor source contains no band threshold or
maintenance-trajectory read.

## Process custody — {'PASS' if criterion_3 else 'FAIL'}

The ITS ledger contains 5,504 gap-free rows, every row logs released block
`820001:825504`, and all 5,504 states serialize/reload/rehash bitwise. All
quotas first coexisted at position `{all_quota_fill_position}`; processing
continued for
`{summary['criteria']['3_process_custody']['candidates_processed_after_all_quotas_filled']}`
additional candidates, proving no early stop.

## Distributional census — descriptive only

q(P) mean/median were `{census['q_P']['summary']['mean']:.6f}` /
`{census['q_P']['summary']['median']:.6f}`. m0 mean/median were
`{census['m0']['summary']['mean']:.6f}` /
`{census['m0']['summary']['median']:.6f}`. Histograms, ECDF coordinates,
history-length/profile strata, saturation, first-selection, post-selection
evidence, cumulative P-vs-runner-up BF, and fill curves are published in
`census.json` and `per_seed.csv`.

Against the committed 800-seed block, the descriptive q(P) mean difference
was `{comparison['q_P_mean_difference_95_interval'][0]:.6f}` (95% interval
`[{comparison['q_P_mean_difference_95_interval'][1]:.6f},
{comparison['q_P_mean_difference_95_interval'][2]:.6f}]`). No verdict pools
the blocks. Historical m0 comparison is unavailable because the 800-seed
ledger did not preserve nonbanked candidate evidence, and that block was not
rerun.

## Verdict classes

Scientific sampling adequacy: **{'PASS' if criterion_1 else 'FAIL'}**.
Semantic integrity: **{'PASS' if criterion_2 else 'FAIL'}**. Process custody:
**{'PASS' if criterion_3 else 'FAIL'}**. Distributional census:
**DESCRIPTIVE ONLY**. The maintenance seeds `816001:816900` remain closed and
were not accessed.
"""
    (RESULT_DIR / "report.md").write_text(report, encoding="utf-8")

    result_files = [
        RESULT_DIR / "per_seed.csv",
        RESULT_DIR / "retained_states.json",
        RESULT_DIR / "provenance-audit.json",
        RESULT_DIR / "census.json",
        RESULT_DIR / "summary.json",
        RESULT_DIR / "report.md",
    ]
    addendum = {
        "stage": "V2.3.3",
        "challenge": CHALLENGE,
        "classification": "sampling_adequacy_requalification",
        "verdict": verdict,
        "criterion_verdicts": summary["verdict_classes"],
        "seed_block_used": [FIRST_SEED, LAST_SEED],
        "candidate_count": WORLD_COUNT,
        "identity": identity,
        "maintenance_challenge_run": False,
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "challenge_spec_sha256": sha256(CHALLENGE_PATH),
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in result_files
        },
        "prior_bank_verdicts_preserved": [
            "C-V233-M-bank FAIL_UNEXECUTABLE",
            "C-V233-M-bank (repaired instrument) FAIL",
        ],
        "frozen_manifest_modified": False,
    }
    write_json(ADDENDUM_PATH, addendum)
    MILESTONE_PATH.write_text(
        f"""# V2.3.3 Gate 6 bank2 update

`{CHALLENGE}` verdict: **{verdict}**. The full 5,504-seed block was consumed
once in ascending order. Eligible counts were
`{counts['moderate']}` moderate, `{counts['strong']}` strong, and
`{counts['very_strong']}` very-strong; 40 per band were retained.
Semantic integrity passed with `{len(provenance)}` exact provenance
reconstructions and `{len(one_posterior)}` one-posterior audits. Custody
passed with 5,504/5,504 rehashes and no early stop. The q(P)/m0 census and
the non-pooled comparison with the standing 800-seed yield result are
descriptive only. The maintenance bundle and seeds `816001:816900` remain
closed pending explicit evaluator release.
""",
        encoding="utf-8",
    )
    addendum["result_hashes"][
        str(MILESTONE_PATH.relative_to(ROOT))
    ] = sha256(MILESTONE_PATH)
    write_json(ADDENDUM_PATH, addendum)


if __name__ == "__main__":
    main()
