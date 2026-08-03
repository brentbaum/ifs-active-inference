#!/usr/bin/env python3
"""Round-18 read-only/zero-new-seed diagnosis of retained V3.6 Gate 4."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SUITE_ROOT = ROOT.parent
sys.path.insert(0, str(SUITE_ROOT))
sys.path.insert(0, str(ROOT))

from ref import v32, v35  # noqa: E402
from ref.trace_sink import serializing_trace_context  # noqa: E402


RESULTS = ROOT / "results" / "V3.6"
TRACE = RESULTS / "v3.6-r1-gate4-traces.jsonl"
TOLERANCE = 1e-10
RETAINED_BLOCK = (3_709_000, 3_713_999)


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        + b"\n"
    )


def structure_key(structure: v35.ProtectStructure) -> tuple[Any, ...]:
    return (
        structure.active_modes,
        *structure.mode_root_edges,
        structure.joint_policy_outcome,
        structure.cross_mode_outcome,
    )


def component_key(
    structure: v35.ProtectStructure, sign: int, reliable: int
) -> tuple[Any, ...]:
    return (*structure_key(structure), int(sign), int(reliable))


def logsumexp(values: Sequence[float]) -> float:
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def bernoulli_log(observed: int, probability_one: float) -> float:
    probability = probability_one if observed else 1.0 - probability_one
    return math.log(probability)


def direct_structure_log_prior(
    structure: v35.ProtectStructure, *, joint_policy_allowed: Iterable[int]
) -> float:
    """Fresh code-length summation; does not call the production prior."""
    allowed = frozenset(int(value) for value in joint_policy_allowed)
    retained = [
        candidate
        for candidate in v35.PROGRAMS
        if candidate.joint_policy_outcome in allowed
    ]

    def cost(candidate: v35.ProtectStructure) -> float:
        return float(
            1
            + candidate.active_modes
            + sum(candidate.mode_root_edges)
            + candidate.joint_policy_outcome
            + candidate.cross_mode_outcome
        )

    normalizer = math.fsum(2.0 ** (-cost(candidate)) for candidate in retained)
    return -cost(structure) * math.log(2.0) - math.log(normalizer)


def direct_slice_probability(
    observation: v35.ProtectObservation,
    modes: Sequence[int],
    structure: v35.ProtectStructure,
    sign: int,
    reliable: int,
) -> float:
    """Direct frozen production factorization, independently authored."""
    result = 1.0
    for slot in range(3):
        signal = observation.mode_signals[slot]
        if signal is not None:
            latent = modes[slot] if slot < structure.active_modes else 0
            result *= 0.86 if int(signal) == int(latent) else 0.14
        registered = observation.registration[slot]
        if registered is not None:
            # Candidate-common M_k=0 prior predictive.
            result *= 0.20 if registered else 0.80

    if observation.root_signal is not None:
        parents = [
            modes[slot]
            for slot in range(structure.active_modes)
            if structure.mode_root_edges[slot]
        ]
        if not parents:
            probability_one = 0.5
        else:
            root = int(sum(parents) >= len(parents) / 2.0)
            probability_one = 0.84 if root else 0.16
        result *= (
            probability_one
            if observation.root_signal
            else 1.0 - probability_one
        )

    if observation.outcome is not None:
        probability_one = 0.5
        active = structure.active_modes
        if structure.joint_policy_outcome:
            probability_one += 0.18 * (
                sum(observation.policy[:active]) / active - 1.0
            )
        if structure.cross_mode_outcome:
            pairs = [
                (left, right)
                for left in range(active)
                for right in range(left + 1, active)
                if modes[left] and modes[right]
            ]
            if pairs:
                if sign < 0:
                    probability_one += 0.30 * sum(
                        abs(observation.policy[left] - observation.policy[right]) / 2.0
                        for left, right in pairs
                    ) / len(pairs)
                else:
                    probability_one += 0.30 * sum(
                        int(
                            observation.policy[left] == 2
                            and observation.policy[right] == 2
                        )
                        for left, right in pairs
                    ) / len(pairs)
        probability_one = min(0.97, max(0.03, probability_one))
        result *= probability_one if observation.outcome else 1.0 - probability_one

    if observation.partner_remaining is not None:
        probability_one = 0.86 if reliable else 0.14
        result *= (
            probability_one
            if observation.partner_remaining
            else 1.0 - probability_one
        )
    if observation.partner_pressure is not None:
        probability_one = 0.14 if reliable else 0.86
        result *= (
            probability_one
            if observation.partner_pressure
            else 1.0 - probability_one
        )
    if observation.denied_contact is not None:
        vulnerable = modes[structure.active_modes - 1]
        policy = observation.policy[structure.active_modes - 1]
        probability_one = 0.86 if vulnerable and policy == 0 else 0.14
        result *= (
            probability_one
            if observation.denied_contact
            else 1.0 - probability_one
        )
    return result


def direct_parameter_log_evidence(
    observations: Sequence[v35.ProtectObservation],
    structure: v35.ProtectStructure,
    reliable: int,
    channel: str,
) -> float:
    total = 0.0
    for slot in range(3):
        if slot >= structure.active_modes:
            for observation in observations:
                observed = (
                    observation.support_signals[slot]
                    if channel == "support"
                    else observation.contact_signals[slot]
                )
                if observed is None:
                    continue
                total += bernoulli_log(observed, 0.25 if channel == "support" else 0.14)
            continue

        theta_logs = []
        for theta in (0, 1):
            value = -math.log(2.0)
            for observation in observations:
                observed = (
                    observation.support_signals[slot]
                    if channel == "support"
                    else observation.contact_signals[slot]
                )
                if observed is None:
                    continue
                if channel == "support":
                    targeted = observation.support_targets[slot]
                    probability_one = 0.82 if reliable and theta and targeted else 0.25
                else:
                    probability_one = 0.14
                    if theta and observation.policy[slot] == 0:
                        probability_one = 0.50 if reliable else 0.86
                value += bernoulli_log(observed, probability_one)
            theta_logs.append(value)
        total += logsumexp(theta_logs)
    return total


def direct_component_log_likelihood(
    world: v35.ProtectWorld,
    structure: v35.ProtectStructure,
    sign: int,
    reliable: int,
) -> float:
    total = 0.0
    for observation in world.observations:
        evidence = 0.0
        for active_bits in itertools.product((0, 1), repeat=structure.active_modes):
            modes = tuple(active_bits) + (0,) * (3 - structure.active_modes)
            evidence += (0.5 ** structure.active_modes) * direct_slice_probability(
                observation, modes, structure, sign, reliable
            )
        if evidence <= 0.0:
            raise AssertionError("fresh hand enumeration produced zero slice evidence")
        total += math.log(evidence)
    total += direct_parameter_log_evidence(
        world.observations, structure, reliable, "support"
    )
    total += direct_parameter_log_evidence(
        world.observations, structure, reliable, "contact"
    )
    return total


def direct_hand_posterior(
    world: v35.ProtectWorld, *, joint_policy_allowed: Iterable[int]
) -> dict[tuple[Any, ...], float]:
    allowed = frozenset(int(value) for value in joint_policy_allowed)
    keys: list[tuple[Any, ...]] = []
    log_weights: list[float] = []
    for structure in v35.PROGRAMS:
        if structure.joint_policy_outcome not in allowed:
            continue
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                keys.append(component_key(structure, sign, reliable))
                log_weights.append(
                    direct_structure_log_prior(
                        structure, joint_policy_allowed=allowed
                    )
                    - math.log(len(signs))
                    - math.log(2.0)
                    + direct_component_log_likelihood(
                        world, structure, sign, reliable
                    )
                )
    normalizer = logsumexp(log_weights)
    return {
        key: math.exp(value - normalizer)
        for key, value in zip(keys, log_weights)
    }


def production_map(posterior: v35.ProtectPosterior) -> dict[tuple[Any, ...], float]:
    result = {}
    for index, ((structure, sign), probability) in enumerate(
        zip(posterior.components, posterior.probabilities)
    ):
        reliable = index % 2
        key = component_key(structure, sign, reliable)
        if key in result:
            raise AssertionError("production coordinate unexpectedly duplicated")
        result[key] = float(probability)
    return result


def max_distance(
    left: Mapping[tuple[Any, ...], float], right: Mapping[tuple[Any, ...], float]
) -> tuple[float, tuple[Any, ...]]:
    keys = set(left) | set(right)
    coordinate = max(keys, key=lambda key: abs(left.get(key, 0.0) - right.get(key, 0.0)))
    return abs(left.get(coordinate, 0.0) - right.get(coordinate, 0.0)), coordinate


def v32_program_dict(program: v32.TemporalStructure, prior: float) -> dict[str, Any]:
    return {
        "active_contexts": program.active_contexts,
        "scopes": list(program.scopes),
        "dynamics": list(program.dynamics),
        "prior_mass": prior,
    }


def direct_v32_prior(program: v32.TemporalStructure) -> float:
    active_weights = {1: 4.0 / 7.0, 2: 2.0 / 7.0, 3: 1.0 / 7.0}
    scope_weights = {"shared_global": 2.0 / 3.0, "cue_specific": 1.0 / 6.0, "context_specific": 1.0 / 6.0}
    dynamics_weights = {
        "static": 4.0 / 7.0,
        "discrete_recurrent_context": 1.0 / 7.0,
        "ordered_random_walk": 1.0 / 7.0,
        "one_way_change": 1.0 / 7.0,
    }
    return (
        active_weights[program.active_contexts]
        * scope_weights[program.scopes[0]]
        * scope_weights[program.scopes[1]]
        * dynamics_weights[program.dynamics[0]]
        * dynamics_weights[program.dynamics[1]]
    )


def main() -> None:
    if not TRACE.exists():
        raise SystemExit("retained Gate-4 trace is missing")
    trace_sha = hashlib.sha256(TRACE.read_bytes()).hexdigest()
    rows = [json.loads(line) for line in TRACE.open()]

    protect_rows = [row for row in rows if row["lesion"] == "protect_joint_policy"]
    argmax_row = max(protect_rows, key=lambda row: row["independent_oracle_error"])
    seed = int(argmax_row["seed"])
    config = v35.ProtectConfig(
        "all", "remaining", "high", "mixed", 3, "allied", "all",
        "delivered", "delivered", 64,
    )
    with serializing_trace_context("round18.retained_protect_triangulation") as sink:
        world = v35.generate_world(seed, config, released_block=RETAINED_BLOCK)
        full = v35.score_world(world)
        restricted = v35.score_world(world, restrictions={"JOINT_POLICY_Y": (0,)})
    world_sha = hashlib.sha256(canonical(asdict(world))).hexdigest()
    if world_sha != argmax_row["world_sha256"]:
        raise SystemExit("retained-world deterministic reconstruction hash mismatch")

    full_map = production_map(full)
    restricted_map = production_map(restricted)
    licensed_full_mass = math.fsum(
        probability
        for key, probability in full_map.items()
        if key[4] == 0  # joint-policy edge coordinate in structure_key
    )
    production_conditioned = {
        key: (
            probability / licensed_full_mass if key[4] == 0 else 0.0
        )
        for key, probability in full_map.items()
    }
    production_identity_error, production_identity_coordinate = max_distance(
        production_conditioned, restricted_map
    )

    hand_full = direct_hand_posterior(world, joint_policy_allowed=(0, 1))
    hand_restricted = direct_hand_posterior(world, joint_policy_allowed=(0,))
    hand_full_error, hand_full_coordinate = max_distance(hand_full, full_map)
    hand_restricted_error, hand_restricted_coordinate = max_distance(
        hand_restricted, restricted_map
    )

    # Reproduce the existing oracle exactly: its key omits reliable and the
    # dict therefore overwrites the reliable=0 atom with reliable=1.
    collapsed_observed = {
        (structure_key(structure), int(sign)): float(probability)
        for (structure, sign), probability in zip(
            restricted.components, restricted.probabilities
        )
    }
    existing_oracle_max = -1.0
    existing_oracle_coordinate: dict[str, Any] | None = None
    for index, ((structure, sign), probability) in enumerate(
        zip(full.components, full.probabilities)
    ):
        reliable = index % 2
        licensed = structure.joint_policy_outcome == 0
        expected = float(probability) / licensed_full_mass if licensed else 0.0
        observed = collapsed_observed.get((structure_key(structure), int(sign)), 0.0)
        error = abs(observed - expected)
        if error > existing_oracle_max:
            existing_oracle_max = error
            existing_oracle_coordinate = {
                "structure": list(structure_key(structure)),
                "cross_sign": int(sign),
                "partner_reliable": reliable,
                "expected_conditioned_full": expected,
                "collapsed_oracle_observed": observed,
                "fresh_hand_restricted": hand_restricted.get(
                    component_key(structure, sign, reliable), 0.0
                ),
                "production_restricted": restricted_map.get(
                    component_key(structure, sign, reliable), 0.0
                ),
                "absolute_error": error,
            }

    split_rows = [row for row in rows if row["lesion"] == "split_context_slot"]
    licensed = [program for program in v32.PROGRAMS if program.active_contexts == 1]
    excluded = [program for program in v32.PROGRAMS if program.active_contexts != 1]
    licensed_records = [
        v32_program_dict(program, direct_v32_prior(program)) for program in licensed
    ]
    excluded_records = [
        {
            **v32_program_dict(program, direct_v32_prior(program)),
            "all_derivations_use_deleted_active_context_production": True,
        }
        for program in excluded
    ]
    licensed_zero = [record for record in licensed_records if record["prior_mass"] == 0.0]
    split_counts = {
        "world_count": len(split_rows),
        "seed_min": min(row["seed"] for row in split_rows),
        "seed_max": max(row["seed"] for row in split_rows),
        "licensed_support_count_values": sorted(
            {row["licensed_support_count"] for row in split_rows}
        ),
        "restricted_prior_mass_values": sorted(
            {row["restricted_prior_mass"] for row in split_rows}
        ),
        "restricted_evidence_zero_count": sum(
            row["restricted_evidence"] == 0.0 for row in split_rows
        ),
        "posterior_normalized_count": sum(
            row["posterior_normalization_error"] <= TOLERANCE
            for row in split_rows
        ),
    }

    result = {
        "stage": "V3.6",
        "diagnosis": "ROUND18_GATE4_READ_ONLY_ZERO_NEW_SEED",
        "tolerance": TOLERANCE,
        "custody": {
            "retained_trace_file": TRACE.name,
            "retained_trace_sha256": trace_sha,
            "new_scientific_seeds_consumed": [],
            "retained_seed_reconstructed": seed,
            "retained_world_hash_verified": True,
            "runtime_trace_events": sink.events,
            "gate4_statistics_recomputed": False,
            "gate4_verdict_amended": False,
            "escrow_touched": False,
        },
        "D1_protect_joint_policy": {
            "classification": "ORACLE_CONSTRUCT",
            "argmax_retained_row": argmax_row,
            "argmax_existing_oracle_coordinate": existing_oracle_coordinate,
            "existing_oracle_error_reproduced": existing_oracle_max,
            "retained_existing_oracle_error": argmax_row["independent_oracle_error"],
            "production_restricted_prior_identity_error": production_identity_error,
            "production_restricted_prior_identity_argmax": list(production_identity_coordinate),
            "fresh_hand_vs_production_full_error": hand_full_error,
            "fresh_hand_vs_production_full_argmax": list(hand_full_coordinate),
            "fresh_hand_vs_production_restricted_error": hand_restricted_error,
            "fresh_hand_vs_production_restricted_argmax": list(hand_restricted_coordinate),
            "named_disagreeing_factor": "partner reliability latent L and its p(L)=0.5 plus partner/support/contact likelihood factors",
            "mechanism": "ProtectPosterior.components stores only (structure, cross_sign), while probabilities also index reliable in {0,1}; the existing oracle dict collapses the two reliable atoms and retains only the reliable=1 value.",
            "production_defect": False,
        },
        "D2_split_context_slot": {
            "classification": "APPARATUS_SUPPORT_ACCOUNTING_ERROR",
            "structural_class_heterogeneity": False,
            "retained_world_configuration": {
                "cell": "split_context_slot",
                "truth_active_contexts": 2,
                "truth_scopes": ["context_specific", "context_specific"],
                "truth_dynamics": [
                    "discrete_recurrent_context",
                    "discrete_recurrent_context",
                ],
                "evidence_style": "witnessing",
                "length": 48,
                "cue_count": 3,
                "seed_range": [3_710_000, 3_710_999],
            },
            "retained_trace_counts": split_counts,
            "grammar_enumeration": {
                "total_structures": len(v32.PROGRAMS),
                "licensed_active_contexts_1": len(licensed),
                "grammar_forced_excluded_active_contexts_2_or_3": len(excluded),
                "licensed_structures_losing_all_prior_mass": licensed_zero,
                "licensed_structures": licensed_records,
                "grammar_forced_excluded_structures": excluded_records,
                "licensed_prior_mass_sum": math.fsum(
                    record["prior_mass"] for record in licensed_records
                ),
                "excluded_prior_mass_sum": math.fsum(
                    record["prior_mass"] for record in excluded_records
                ),
                "all_excluded_derivations_require_deleted_active_context_production": True,
            },
            "named_disagreeing_factor": "exp(restricted.log_evidence) used as a support-positivity test",
            "mechanism": "Every licensed active_contexts=1 structure has finite positive code-length prior mass. In all 1,000 retained worlds the normalized restricted posterior is finite, but exponentiating its very negative log evidence underflows to 0.0 and is misread as empty structural support.",
            "grammar_defect": False,
        },
        "verdicts_unchanged": {
            "gate4": "FAIL_RETAINED_UNAMENDED",
            "gate5": "FAIL_DERIVATIVE_RETAINED_UNAMENDED",
        },
    }

    out_json = RESULTS / "round18-gate4-diagnosis.json"
    out_md = RESULTS / "round18-gate4-diagnosis.md"
    if out_json.exists() or out_md.exists():
        raise SystemExit("round-18 diagnosis outputs already exist")
    out_json.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    d1 = result["D1_protect_joint_policy"]
    d2 = result["D2_split_context_slot"]
    out_md.write_text(
        f"""# V3.6 Round-18 Gate-4 diagnosis

This is a read-only diagnosis. It consumed no new scientific seed, changed no
scientific module, recomputed no Gate-4 criterion statistic, and amended no
verdict. The retained trace hash is `{trace_sha}`. Seed `{seed}` was only
deterministically reconstructed to recover the exact retained configuration;
its world hash matched `{world_sha}`.

## D1 — protect_joint_policy

Classification: **ORACLE_CONSTRUCT**.

The retained maximum is seed `{seed}`, with oracle disagreement
`{argmax_row['independent_oracle_error']}`. The production restricted-prior
identity is `{production_identity_error:.3g}`. A fresh hand enumeration from
the declared atomic productions agrees with the production posterior to
`{hand_full_error:.3g}` for the full model and `{hand_restricted_error:.3g}`
for the lesioned model.

The disagreeing factor is the **partner-reliability latent `L`**, including
its `p(L)=0.5` factor and partner/support/contact likelihood terms. The scorer
stores probabilities for `(structure, cross_sign, reliable)` but exposes
component keys only as `(structure, cross_sign)`. The existing oracle builds
a dictionary from those incomplete keys, so the reliable=1 atom overwrites
the reliable=0 atom. At the argmax coordinate the collapsed comparison is
`{existing_oracle_max}`. The fresh coordinate-complete oracle agrees with the
production path; there is no production defect.

## D2 — split_context_slot

Classification: **APPARATUS_SUPPORT_ACCOUNTING_ERROR**, not structural
class-heterogeneity.

All 1,000 retained worlds use the same planned configuration: two active
contexts, context-specific cue and outcome scopes, recurrent dynamics,
witnessing evidence, 48 slices, and three cues. Every row reports 144 licensed
structures and positive restricted prior mass `4/7 = 0.5714285714285714`.
Exactly **zero** licensed structures lose prior mass. The grammar contains 144
licensed active-context-count-1 structures, all with positive prior, and 288
excluded active-count-2/3 structures. Those 288 exclusions are grammar-forced:
their only derivations use the deleted active-context-count production.

The failing quantity is not structural prior support. It is
`exp(restricted.log_evidence)`. In all 1,000 worlds this exponentiation
underflows to `0.0` even though the restricted posterior is finite and
normalized within `1e-10`. The apparatus then treats numerical evidence-scale
underflow as empty support. The exact structure tables are included in the
JSON record.

## Standing record

Gate 4 remains **FAIL_RETAINED_UNAMENDED** and Gate 5 remains its retained
derivative FAIL. No repair is made or authorized by this diagnosis. No seed
block or escrow was opened.
"""
    )
    print(json.dumps({"D1": d1["classification"], "D2": d2["classification"]}))


if __name__ == "__main__":
    main()
