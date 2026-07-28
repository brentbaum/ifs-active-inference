"""Run revealed C-V233-M-bank against frozen V2.3.3."""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import math
import random
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
sys.path.insert(0, str(ROOT))

from ref.audit import ProtocolState, audit_one_posterior  # noqa: E402
from ref.rng import component_rng  # noqa: E402
from ref.v221 import (  # noqa: E402
    ASSOCIATION_HIGH,
    learn_association,
    model_averaged_association,
)
from ref.v232_formation import (  # noqa: E402
    PRIOR,
    SUPPORT,
    score_history,
    slice_distribution,
)
from ref.v233 import (  # noqa: E402
    PARAMETERS,
    canonical_state_bytes,
    canonical_state_hash,
    classify_initial_strength,
    construct_bank_state,
)


CHALLENGE = "C-V233-M-bank"
FREEZE_COMMIT = "3e9bad2"
FIRST_SEED = 815001
LAST_SEED = 815800
TARGET_PER_STRATUM = 40
STRATA = ("moderate", "strong", "very_strong")
RESULT_DIR = ROOT / "results" / "challenges" / CHALLENGE
MANIFEST_REL = (
    "projects/emergence-suite/v2/results/V2.3.3/"
    "freeze-manifest.json"
)
CHALLENGE_PATH = (
    ROOT / "sealed-revealed" / "C-V233-M-bank-challenge.md"
)
ADDENDUM_PATH = ROOT / "results" / "V2.3.3" / "gate6-addendum.json"
MILESTONE_PATH = (
    ROOT / "results" / "milestone-4-v2.3.3-gate6-bank-update.md"
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


def verify_frozen_identity() -> dict[str, Any]:
    committed_bytes = subprocess.check_output(
        ["git", "show", f"{FREEZE_COMMIT}:{MANIFEST_REL}"], cwd=REPO
    )
    local_path = ROOT / "results" / "V2.3.3" / "freeze-manifest.json"
    if local_path.read_bytes() != committed_bytes:
        raise RuntimeError("local V2.3.3 manifest differs from 3e9bad2")
    manifest = json.loads(committed_bytes)
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = ROOT / relative
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {"path": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"frozen identity mismatch: {mismatches}")
    return {
        "commit": FREEZE_COMMIT,
        "manifest_sha256": hashlib.sha256(committed_bytes).hexdigest(),
        "verified_file_count": len(manifest["files"]),
        "mismatches": mismatches,
    }


def wilson_interval(successes: int, total: int) -> list[float]:
    rate = successes / total
    z = 1.96
    denominator = 1.0 + z * z / total
    center = (rate + z * z / (2.0 * total)) / denominator
    half = (
        z
        * math.sqrt(
            rate * (1.0 - rate) / total
            + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return [rate, center - half, center + half]


def distribution_summary(values: list[float]) -> dict[str, Any]:
    array = np.asarray(values, dtype=float)
    return {
        "count": len(values),
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


def independent_root_update(
    prior: np.ndarray,
    observation: tuple[int, int, int],
    association: float,
) -> np.ndarray:
    self_value = observation[0]
    likelihood = np.asarray(
        [
            association if self_value == 0 else 1.0 - association,
            association if self_value == 1 else 1.0 - association,
        ],
        dtype=float,
    )
    result = prior * likelihood
    return result / result.sum()


def independent_cue_prediction(
    root: np.ndarray, association: float
) -> np.ndarray:
    probability_one = (
        float(root[0]) * (1.0 - association)
        + float(root[1]) * association
    )
    return np.asarray([1.0 - probability_one, probability_one])


def maximum_error(left: Any, right: Any) -> float:
    return float(
        np.max(
            np.abs(
                np.asarray(left, dtype=float)
                - np.asarray(right, dtype=float)
            )
        )
    )


def provenance_audit(state: dict[str, Any]) -> dict[str, Any]:
    seed = int(state["seed"])
    observations = [
        tuple(value)
        for value in state["developmental_history"]["observations"]
    ]
    configurations = state["developmental_history"]["configurations"]
    bank = PARAMETERS["formed_world_bank"]
    profiles = bank["history_profile_cycle"]
    expected_configurations = [
        {
            "event": True,
            **profiles[(seed + time) % len(profiles)],
        }
        for time in range(len(configurations))
    ]
    generated_observations = []
    for time, configuration in enumerate(expected_configurations):
        row = slice_distribution("P", **configuration)
        index = int(
            component_rng(seed, f"v233-bank-development-{time}").choice(
                len(row), p=row
            )
        )
        generated_observations.append(SUPPORT[index])

    formation = score_history(observations, configurations, prior=PRIOR)
    matches = max(1, sum(observation[0] == 1 for observation in observations))
    mismatches = max(0, len(observations) - matches)
    treated_state = learn_association(matches, mismatches)
    treated_association = model_averaged_association(treated_state)
    untreated_rng = component_rng(
        seed, "v233-bank-untreated-association"
    )
    untreated_matches = int(
        untreated_rng.binomial(
            max(4, len(observations)), ASSOCIATION_HIGH
        )
    )
    untreated_state = learn_association(
        untreated_matches,
        max(4, len(observations)) - untreated_matches,
    )
    untreated_association = model_averaged_association(untreated_state)

    root = np.asarray([0.5, 0.5])
    for observation in observations:
        root = independent_root_update(
            root, observation, treated_association
        )
    treated_cue = independent_cue_prediction(root, treated_association)
    untreated_cue = independent_cue_prediction(root, untreated_association)

    ordinary = sum(
        configuration["precision"] == "ordinary"
        for configuration in configurations
    )
    acute = len(configurations) - ordinary
    high = sum(
        configuration["control"] == "high"
        for configuration in configurations
    )
    low = len(configurations) - high
    outcome_ones = sum(observation[1] for observation in observations)
    safe = len(observations) - outcome_ones
    availability_prior = np.asarray(
        PARAMETERS["maintenance"]["policy"]["availability_beta_prior"],
        dtype=float,
    )
    errors = {
        "developmental_configuration_error": float(
            configurations != expected_configurations
        ),
        "developmental_observation_error": float(
            observations != generated_observations
        ),
        "formation_posterior_error": maximum_error(
            state["q_H_formation"], formation["posterior"]
        ),
        "candidate_log_evidence_error": maximum_error(
            state["candidate_log_evidence"], formation["log_joint"]
        ),
        "treated_association_structure_error": maximum_error(
            state["cue_root_structural_posteriors"]["treated"],
            treated_state.posterior_store["Z_association"],
        ),
        "untreated_association_structure_error": maximum_error(
            state["cue_root_structural_posteriors"]["untreated"],
            untreated_state.posterior_store["Z_association"],
        ),
        "treated_association_readout_error": abs(
            float(state["cue_root_associations"]["treated"])
            - treated_association
        ),
        "untreated_association_readout_error": abs(
            float(state["cue_root_associations"]["untreated"])
            - untreated_association
        ),
        "root_posterior_error": maximum_error(
            state["root_posterior"], root
        ),
        "treated_cue_posterior_error": maximum_error(
            state["cue_posteriors"]["treated"], treated_cue
        ),
        "untreated_cue_posterior_error": maximum_error(
            state["cue_posteriors"]["untreated"], untreated_cue
        ),
        "treated_precision_posterior_error": maximum_error(
            state["precision_posteriors"]["treated"],
            [1.0 + ordinary, 1.0 + acute],
        ),
        "untreated_precision_posterior_error": maximum_error(
            state["precision_posteriors"]["untreated"],
            [1.0 + high, 1.0 + low],
        ),
        "engage_availability_posterior_error": maximum_error(
            state["action_outcome_posteriors"]["engage_available"],
            availability_prior + [safe, outcome_ones],
        ),
        "avoid_availability_posterior_error": maximum_error(
            state["action_outcome_posteriors"]["avoid_available"],
            availability_prior + [high, low],
        ),
    }
    provenance_hash_errors = {
        "formation_engine": (
            state["provenance"]["engine_sha256"]
            != sha256(ROOT / "ref" / "v232_formation.py")
        ),
        "formation_parameters": (
            state["provenance"]["parameter_sha256"]
            != sha256(
                ROOT
                / "protocols"
                / "v2.3.2-formation-parameters.json"
            )
        ),
        "maintenance_parameters": (
            state["provenance"]["v233_parameter_sha256"]
            != sha256(ROOT / "protocols" / "v2.3.3-parameters.json")
        ),
    }
    maximum_numeric_error = max(errors.values())
    return {
        "seed": seed,
        "errors": errors,
        "maximum_numeric_error": maximum_numeric_error,
        "provenance_hash_errors": provenance_hash_errors,
        "passed": (
            maximum_numeric_error <= TOLERANCE
            and not any(provenance_hash_errors.values())
            and state["source_stage"] == "V2.3.2-formation"
        ),
    }


def one_posterior_audit(state: dict[str, Any]) -> dict[str, Any]:
    log_evidence = np.asarray(
        state["candidate_log_evidence"], dtype=float
    )
    evidence = np.exp(log_evidence - log_evidence.max())
    protocol_state = ProtocolState(
        posterior_store={
            "H_formation": np.asarray(state["q_H_formation"], dtype=float),
            "G": np.asarray(state["root_posterior"], dtype=float),
            "cue_treated": np.asarray(
                state["cue_posteriors"]["treated"], dtype=float
            ),
            "cue_untreated": np.asarray(
                state["cue_posteriors"]["untreated"], dtype=float
            ),
        },
        parameter_posterior_store={
            "association_treated": np.asarray(
                state["cue_root_structural_posteriors"]["treated"],
                dtype=float,
            ),
            "association_untreated": np.asarray(
                state["cue_root_structural_posteriors"]["untreated"],
                dtype=float,
            ),
            "precision_treated": np.asarray(
                state["precision_posteriors"]["treated"], dtype=float
            ),
            "precision_untreated": np.asarray(
                state["precision_posteriors"]["untreated"], dtype=float
            ),
            "availability_engage": np.asarray(
                state["action_outcome_posteriors"]["engage_available"],
                dtype=float,
            ),
            "availability_avoid": np.asarray(
                state["action_outcome_posteriors"]["avoid_available"],
                dtype=float,
            ),
        },
        evidence_store={
            f"candidate_{index}": float(value)
            for index, value in enumerate(evidence)
        },
        metadata=MappingProxyType(
            {"seed": int(state["seed"]), "stage": "V2.3.3-bank"}
        ),
    )
    audit_one_posterior(protocol_state)
    return {"seed": int(state["seed"]), "passed": True}


def run_bank() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
]:
    counts = {stratum: 0 for stratum in STRATA}
    retained_counts = {stratum: 0 for stratum in STRATA}
    fill = {stratum: None for stratum in STRATA}
    ledger = []
    retained = []
    rehash_failures = []
    for position, seed in enumerate(
        range(FIRST_SEED, LAST_SEED + 1), start=1
    ):
        state = construct_bank_state(seed)
        serialized = canonical_state_bytes(state)
        digest = hashlib.sha256(serialized).hexdigest()
        reload_digest = canonical_state_hash(json.loads(serialized))
        rehash_ok = digest == reload_digest
        if not rehash_ok:
            rehash_failures.append(seed)
        q_p = float(state["q_H_formation"][2])
        stratum = classify_initial_strength(q_p)
        retained_now = (
            stratum is not None
            and retained_counts[stratum] < TARGET_PER_STRATUM
        )
        if stratum is not None:
            counts[stratum] += 1
            if counts[stratum] == TARGET_PER_STRATUM:
                fill[stratum] = {"position": position, "seed": seed}
            if retained_now:
                retained_counts[stratum] += 1
        if retained_now:
            reason = "retained_first_eligible"
            retained.append(
                {
                    "seed": seed,
                    "q_P": q_p,
                    "stratum": stratum,
                    "state_sha256": digest,
                    "serialized_state": state,
                }
            )
        elif stratum is not None:
            reason = "eligible_after_stratum_quota"
        elif q_p < 0.60:
            reason = "below_formed_range"
        else:
            reason = "above_nonsaturation_range"
        ledger.append(
            {
                "position": position,
                "seed": seed,
                "q_P": q_p,
                "stratum": "" if stratum is None else stratum,
                "eligible": int(stratum is not None),
                "retained": int(retained_now),
                "reason": reason,
                "state_sha256": digest,
                "reload_sha256": reload_digest,
                "rehash_ok": int(rehash_ok),
                "cumulative_moderate": counts["moderate"],
                "cumulative_strong": counts["strong"],
                "cumulative_very_strong": counts["very_strong"],
                "retained_moderate": retained_counts["moderate"],
                "retained_strong": retained_counts["strong"],
                "retained_very_strong": retained_counts["very_strong"],
            }
        )
    return ledger, retained, {
        "eligible_counts": counts,
        "retained_counts": retained_counts,
        "fill": fill,
        "rehash_failures": rehash_failures,
    }


def main() -> None:
    identity = verify_frozen_identity()
    ledger, retained, bank = run_bank()
    challenge_sha = sha256(CHALLENGE_PATH)

    provenance = [
        provenance_audit(record["serialized_state"])
        for record in retained
    ]
    sampling_rng = random.Random(int(challenge_sha[:16], 16))
    audit_records = sampling_rng.sample(retained, 10)
    one_posterior = [
        one_posterior_audit(record["serialized_state"])
        for record in audit_records
    ]

    constructor_source = inspect.getsource(construct_bank_state)
    constructor_source_audit = {
        "contains_stratum_classifier": (
            "classify_initial_strength" in constructor_source
        ),
        "contains_eligibility_thresholds": any(
            token in constructor_source
            for token in (
                "initial_strength_strata",
                "lower_inclusive",
                "upper_exclusive",
            )
        ),
        "contains_formed_assignment": "formed =" in constructor_source,
        "posterior_source_expression_present": (
            'formation["posterior"]' in constructor_source
        ),
        "passed": (
            "classify_initial_strength" not in constructor_source
            and "initial_strength_strata" not in constructor_source
            and "formed =" not in constructor_source
            and 'formation["posterior"]' in constructor_source
        ),
    }

    seed_sequence = [row["seed"] for row in ledger]
    ledger_complete = (
        seed_sequence == list(range(FIRST_SEED, LAST_SEED + 1))
        and [row["position"] for row in ledger] == list(range(1, 801))
    )
    criterion_1 = all(
        bank["eligible_counts"][stratum] >= TARGET_PER_STRATUM
        for stratum in STRATA
    )
    criterion_2 = (
        all(item["passed"] for item in provenance)
        and all(item["passed"] for item in one_posterior)
        and constructor_source_audit["passed"]
    )
    criterion_3 = (
        not bank["rehash_failures"]
        and ledger_complete
        and len(ledger) == 800
        and len(retained) == 120
    )
    verdict = "PASS" if criterion_1 and criterion_2 and criterion_3 else "FAIL"
    eligibility = {
        stratum: {
            "eligible_count": bank["eligible_counts"][stratum],
            "rate_95_wilson": wilson_interval(
                bank["eligible_counts"][stratum], 800
            ),
            "fill": bank["fill"][stratum],
        }
        for stratum in STRATA
    }
    q_values = [float(row["q_P"]) for row in ledger]
    summary = {
        "challenge": CHALLENGE,
        "verdict": verdict,
        "seed_block_used": [FIRST_SEED, LAST_SEED],
        "candidate_count": len(ledger),
        "frozen_identity": identity,
        "criteria": {
            "1_scientific_precondition": {
                "verdict": "PASS" if criterion_1 else "FAIL",
                "eligibility": eligibility,
                "retained_counts": bank["retained_counts"],
            },
            "2_semantic_integrity": {
                "verdict": "PASS" if criterion_2 else "FAIL",
                "retained_state_provenance_count": len(provenance),
                "provenance_failure_seeds": [
                    item["seed"]
                    for item in provenance
                    if not item["passed"]
                ],
                "maximum_provenance_error": max(
                    item["maximum_numeric_error"] for item in provenance
                ),
                "one_posterior_sample_method": (
                    "ten retained states sampled without replacement by "
                    "a deterministic PRNG seeded from the revealed "
                    "challenge SHA-256; custody-only, not scientific"
                ),
                "one_posterior_sample_seeds": [
                    item["seed"] for item in one_posterior
                ],
                "one_posterior_failures": [
                    item["seed"]
                    for item in one_posterior
                    if not item["passed"]
                ],
                "constructor_source_audit": constructor_source_audit,
            },
            "3_process_custody": {
                "verdict": "PASS" if criterion_3 else "FAIL",
                "ledger_complete_no_gaps": ledger_complete,
                "ledger_row_count": len(ledger),
                "retained_state_count": len(retained),
                "candidate_rehash_failure_seeds": bank[
                    "rehash_failures"
                ],
                "candidate_rehash_pass_count": (
                    len(ledger) - len(bank["rehash_failures"])
                ),
            },
            "4_distributional_stress": {
                "verdict": "DESCRIPTIVE_ONLY",
                "criterial": False,
                "q0_P_distribution": distribution_summary(q_values),
                "exclusion_counts": {
                    reason: sum(row["reason"] == reason for row in ledger)
                    for reason in sorted({row["reason"] for row in ledger})
                },
                "fill_curve_location": "per_seed.csv cumulative_* columns",
            },
        },
        "verdict_classes": {
            "scientific_precondition": (
                "PASS" if criterion_1 else "FAIL"
            ),
            "semantic_integrity": "PASS" if criterion_2 else "FAIL",
            "process_custody": "PASS" if criterion_3 else "FAIL",
            "distributional_stress": "DESCRIPTIVE_ONLY",
        },
        "failure_interpretation": (
            None
            if verdict == "PASS"
            else (
                "A stratum shortfall is a formation-yield finding and "
                "keeps maintenance closed; a provenance or custody "
                "failure is an architecture failure. No regeneration "
                "or rule change is permitted."
            )
        ),
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "challenge_spec_sha256": challenge_sha,
    }

    write_csv(RESULT_DIR / "per_seed.csv", ledger)
    write_json(
        RESULT_DIR / "banked_states.json",
        {
            "challenge": CHALLENGE,
            "retention_rule": "first 40 eligible per stratum",
            "states": retained,
        },
    )
    write_json(
        RESULT_DIR / "provenance-audit.json",
        {
            "challenge": CHALLENGE,
            "declared_prior_sources": {
                "H_formation": PRIOR.tolist(),
                "G": [0.5, 0.5],
                "availability_beta": [1.0, 1.0],
                "association": "frozen V2.2.1 spike-and-slab prior",
            },
            "retained_state_audits": provenance,
            "one_posterior_audits": one_posterior,
            "constructor_source_audit": constructor_source_audit,
        },
    )
    write_json(RESULT_DIR / "summary.json", summary)

    eligibility_lines = "\n".join(
        (
            f"- {stratum}: {details['eligible_count']}/800, rate "
            f"`{details['rate_95_wilson'][0]:.6f}` "
            f"(95% Wilson "
            f"`[{details['rate_95_wilson'][1]:.6f}, "
            f"{details['rate_95_wilson'][2]:.6f}]`); filled at "
            f"position `{details['fill']['position']}`, seed "
            f"`{details['fill']['seed']}`."
        )
        for stratum, details in eligibility.items()
    )
    q_summary = summary["criteria"]["4_distributional_stress"][
        "q0_P_distribution"
    ]
    report = f"""# {CHALLENGE}

Sealed verdict: **{verdict}**.

The frozen `3e9bad2` identity check verified all
`{identity['verified_file_count']}` manifest files with zero mismatches.
Exactly 800 candidate seeds (`815001:815800`) were consumed once in ascending
order. The maintenance seed block remains closed and was not accessed.

## Scientific precondition — {'PASS' if criterion_1 else 'FAIL'}

{eligibility_lines}

The first 40 eligible states in each stratum were retained; no regeneration,
replacement, or maintenance outcome informed selection.

## Semantic integrity — {'PASS' if criterion_2 else 'FAIL'}

All `{len(provenance)}` retained states numerically reconstruct from the
frozen developmental observations, declared priors, V2.3.2 evidence update,
V2.2.1 association update, root update, and conjugate count updates. Maximum
provenance error was
`{summary['criteria']['2_semantic_integrity']['maximum_provenance_error']:.3g}`.
The constructor source contains no stratum classifier, eligibility threshold,
or `formed` assignment. The one-posterior audit passed on all ten hash-seeded
randomly drawn retained states: `{summary['criteria']['2_semantic_integrity']['one_posterior_sample_seeds']}`.

## Process custody — {'PASS' if criterion_3 else 'FAIL'}

The ITS ledger has 800 consecutive rows with no seed or position gaps.
All 800 candidate states serialized, reloaded, and rehashed bitwise with zero
failures. The 120 retained serialized states and their SHA-256 hashes are
published in `banked_states.json`.

## Distributional stress — descriptive only

Across all candidates, q0(P) had mean `{q_summary['mean']:.6f}`, median
`{q_summary['median']:.6f}`, p05 `{q_summary['p05']:.6f}`, p95
`{q_summary['p95']:.6f}`, minimum `{q_summary['minimum']:.6f}`, and maximum
`{q_summary['maximum']:.6f}`. Full per-seed values and the three cumulative
fill curves are published in `per_seed.csv`. These values are non-criterial.

## Standing

Scientific precondition: **{'PASS' if criterion_1 else 'FAIL'}**. Semantic
integrity: **{'PASS' if criterion_2 else 'FAIL'}**. Process custody:
**{'PASS' if criterion_3 else 'FAIL'}**. Distributional stress:
**DESCRIPTIVE ONLY**. No class substitutes for another.
"""
    (RESULT_DIR / "report.md").write_text(report, encoding="utf-8")

    result_files = [
        RESULT_DIR / "per_seed.csv",
        RESULT_DIR / "banked_states.json",
        RESULT_DIR / "provenance-audit.json",
        RESULT_DIR / "summary.json",
        RESULT_DIR / "report.md",
    ]
    addendum = {
        "stage": "V2.3.3",
        "challenge": CHALLENGE,
        "freeze_commit": FREEZE_COMMIT,
        "sealed_gate_6_bank_run": True,
        "maintenance_challenge_run": False,
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "verdict": verdict,
        "criterion_verdicts": {
            "scientific_precondition": (
                "PASS" if criterion_1 else "FAIL"
            ),
            "semantic_integrity": "PASS" if criterion_2 else "FAIL",
            "process_custody": "PASS" if criterion_3 else "FAIL",
            "distributional_stress": "DESCRIPTIVE_ONLY",
        },
        "seed_block_used": [FIRST_SEED, LAST_SEED],
        "frozen_identity": identity,
        "challenge_spec_sha256": challenge_sha,
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in result_files
        },
        "frozen_manifest_modified": False,
    }
    write_json(ADDENDUM_PATH, addendum)

    MILESTONE_PATH.write_text(
        f"""# V2.3.3 Gate 6 bank qualification update

`{CHALLENGE}` verdict: **{verdict}**. The frozen identity verified
{identity['verified_file_count']}/{identity['verified_file_count']} files.
The 800-seed ITS block filled moderate, strong, and very-strong strata with
{bank['eligible_counts']['moderate']}, {bank['eligible_counts']['strong']},
and {bank['eligible_counts']['very_strong']} eligible worlds respectively.
All 120 retained-state provenance audits, ten one-posterior audits, 800
serialize/reload hashes, and the gap-free ledger passed. q0(P) and fill curves
are published as non-criterial stress results. The maintenance challenge and
its `816001:816900` seed block remain closed and were not accessed.
""",
        encoding="utf-8",
    )
    addendum["result_hashes"][
        str(MILESTONE_PATH.relative_to(ROOT))
    ] = sha256(MILESTONE_PATH)
    write_json(ADDENDUM_PATH, addendum)


def finalize_observed_seed_guard_failure() -> None:
    """Record the official first-seed stop without rerunning the constructor."""
    identity = verify_frozen_identity()
    challenge_sha = sha256(CHALLENGE_PATH)
    exact_error = "development seeds must be in [0, 799999]"
    rows = []
    for position, seed in enumerate(
        range(FIRST_SEED, LAST_SEED + 1), start=1
    ):
        attempted = position == 1
        rows.append(
            {
                "position": position,
                "seed": seed,
                "attempted": int(attempted),
                "constructor_status": (
                    "REJECTED_BY_FROZEN_SEED_GUARD"
                    if attempted
                    else "NOT_CONSUMED_AFTER_MANDATORY_STOP"
                ),
                "eligibility_decision": "UNAVAILABLE",
                "exclusion_reason": (
                    exact_error
                    if attempted
                    else "challenge stopped at first rejected seed"
                ),
                "q_P": "",
                "stratum": "",
                "state_sha256": "",
                "reload_sha256": "",
                "rehash_status": "NOT_RUN",
                "cumulative_moderate": "",
                "cumulative_strong": "",
                "cumulative_very_strong": "",
            }
        )
    summary = {
        "challenge": CHALLENGE,
        "verdict": "FAIL",
        "failure_class": "ARCHITECTURE_PROSPECTION_FAILURE",
        "seed_block_released": [FIRST_SEED, LAST_SEED],
        "first_seed_attempted": FIRST_SEED,
        "candidate_states_generated": 0,
        "frozen_identity": identity,
        "observed_failure_verbatim": {
            "exception_type": "ValueError",
            "message": exact_error,
            "trace_terminal": (
                "ref/rng.py:15 in component_rng -> "
                'raise ValueError("development seeds must be in [0, 799999]")'
            ),
        },
        "criteria": {
            "1_scientific_precondition": {
                "verdict": "FAIL_UNEXECUTABLE",
                "moderate": {
                    "eligible_count": None,
                    "eligibility_rate_95_interval": None,
                    "fill_position": None,
                },
                "strong": {
                    "eligible_count": None,
                    "eligibility_rate_95_interval": None,
                    "fill_position": None,
                },
                "very_strong": {
                    "eligible_count": None,
                    "eligibility_rate_95_interval": None,
                    "fill_position": None,
                },
                "reason": (
                    "The frozen constructor rejected the first released "
                    "candidate seed before producing q0(P). Rates and fill "
                    "curves cannot be estimated without changing the "
                    "frozen instrument."
                ),
            },
            "2_semantic_integrity": {
                "verdict": "NOT_RUN",
                "provenance_audits_completed": 0,
                "one_posterior_audits_completed": 0,
                "reason": "No bank state exists to audit.",
            },
            "3_process_custody": {
                "verdict": "FAIL_ARCHITECTURE",
                "frozen_identity_verified": True,
                "intended_seed_ledger_rows": 800,
                "eligibility_ledger_rows": 0,
                "serialize_rehash_audits_completed": 0,
                "reason": (
                    "The frozen bank procedure cannot consume its released "
                    "Gate-6 seed domain. The intended-seed ledger is "
                    "complete, but no eligibility decision or state hash "
                    "can be produced."
                ),
            },
            "4_distributional_stress": {
                "verdict": "UNAVAILABLE_DESCRIPTIVE",
                "criterial": False,
                "q0_P_distribution": None,
                "fill_curves": None,
                "reason": "No candidate posterior was generated.",
            },
        },
        "verdict_classes": {
            "scientific_precondition": "FAIL_UNEXECUTABLE",
            "semantic_integrity": "NOT_RUN",
            "process_custody": "FAIL_ARCHITECTURE",
            "distributional_stress": "UNAVAILABLE_DESCRIPTIVE",
        },
        "precommitted_failure_interpretation": (
            "This is an architecture failure of the bank procedure: the "
            "released configuration cannot be expressed through the "
            "frozen constructor. No regeneration, seed remapping, RNG "
            "monkeypatch, or rule change is permitted."
        ),
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "challenge_spec_sha256": challenge_sha,
    }
    failure = {
        "challenge": CHALLENGE,
        "official_run_count": 1,
        "failed_before_first_state": True,
        "seed": FIRST_SEED,
        "exception": (
            "ValueError: development seeds must be in [0, 799999]"
        ),
        "call_path": [
            "challenges/run_c_v233_m_bank.py:run_bank",
            "ref/v233.py:construct_bank_state",
            "ref/rng.py:component_rng",
        ],
        "frozen_code_changed": False,
        "bypass_attempted": False,
        "scientific_rerun_attempted": False,
    }
    write_csv(RESULT_DIR / "per_seed.csv", rows)
    write_json(RESULT_DIR / "failure.json", failure)
    write_json(RESULT_DIR / "summary.json", summary)
    (RESULT_DIR / "report.md").write_text(
        f"""# {CHALLENGE}

Sealed verdict: **FAIL**.

The frozen `3e9bad2` identity check passed for all
`{identity['verified_file_count']}` manifest files. The official run then
stopped at the first released candidate seed, `815001`, before constructing a
state:

> `ValueError: development seeds must be in [0, 799999]`

The error is raised by frozen `ref/rng.py` through the frozen
`construct_bank_state` call. Remapping the seed, replacing the RNG, or
monkeypatching the guard would change the frozen instrument and was not done.

## Scientific precondition — FAIL (unexecutable)

No q0(P) value was generated, so moderate/strong/very-strong eligibility
counts, rates, 95% intervals, and fill positions do not exist. Reporting
zeros would incorrectly describe observed formation yield; reporting inferred
values would fabricate data.

## Semantic integrity — NOT RUN

No bank state exists for the retained-state provenance reconstruction or the
ten-state one-posterior sample.

## Process custody — FAIL (architecture)

The frozen identity passed, but the frozen constructor cannot consume the
released Gate-6 seed domain. `per_seed.csv` records all 800 intended seeds in
order: seed 815001 is marked rejected by the frozen guard and seeds
815002–815800 are marked not consumed after the mandatory stop. There are no
eligibility decisions or serialize/rehash results to claim.

## Distributional stress — unavailable, descriptive only

No q0(P) distribution or fill curve can be published because no candidate
posterior was generated. This descriptive class is non-criterial.

## Standing

Scientific precondition: **FAIL_UNEXECUTABLE**. Semantic integrity:
**NOT_RUN**. Process custody: **FAIL_ARCHITECTURE**. Distributional stress:
**UNAVAILABLE_DESCRIPTIVE**. Under the precommitted interpretation, this is an
architecture/prospection failure of the frozen bank procedure. The
maintenance challenge and seeds `816001:816900` remain closed and were not
accessed.
""",
        encoding="utf-8",
    )
    result_files = [
        RESULT_DIR / "per_seed.csv",
        RESULT_DIR / "failure.json",
        RESULT_DIR / "summary.json",
        RESULT_DIR / "report.md",
    ]
    addendum = {
        "stage": "V2.3.3",
        "challenge": CHALLENGE,
        "freeze_commit": FREEZE_COMMIT,
        "sealed_gate_6_bank_run": True,
        "maintenance_challenge_run": False,
        "maintenance_seed_block_status": "CLOSED_NOT_ACCESSED",
        "verdict": "FAIL",
        "failure_class": "ARCHITECTURE_PROSPECTION_FAILURE",
        "criterion_verdicts": {
            "scientific_precondition": "FAIL_UNEXECUTABLE",
            "semantic_integrity": "NOT_RUN",
            "process_custody": "FAIL_ARCHITECTURE",
            "distributional_stress": "UNAVAILABLE_DESCRIPTIVE",
        },
        "first_seed_attempted": FIRST_SEED,
        "candidate_states_generated": 0,
        "failure_verbatim": (
            "ValueError: development seeds must be in [0, 799999]"
        ),
        "frozen_identity": identity,
        "challenge_spec_sha256": challenge_sha,
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            str(path.relative_to(ROOT)): sha256(path)
            for path in result_files
        },
        "frozen_manifest_modified": False,
    }
    write_json(ADDENDUM_PATH, addendum)
    MILESTONE_PATH.write_text(
        f"""# V2.3.3 Gate 6 bank qualification update

`{CHALLENGE}` verdict: **FAIL**. Frozen identity passed
{identity['verified_file_count']}/{identity['verified_file_count']}, but the
official run stopped before its first state: seed `815001` reached the frozen
constructor's development RNG and raised
`ValueError: development seeds must be in [0, 799999]`. Therefore formation
yield, provenance, rehash, q0(P), and fill-curve results are unavailable; no
seed remapping or instrument bypass was attempted. This is recorded as an
architecture/prospection failure. The maintenance bundle and seeds
`816001:816900` remain closed and were not accessed.
""",
        encoding="utf-8",
    )
    addendum["result_hashes"][
        str(MILESTONE_PATH.relative_to(ROOT))
    ] = sha256(MILESTONE_PATH)
    write_json(ADDENDUM_PATH, addendum)


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--finalize-seed-guard-failure":
        finalize_observed_seed_guard_failure()
    else:
        main()
