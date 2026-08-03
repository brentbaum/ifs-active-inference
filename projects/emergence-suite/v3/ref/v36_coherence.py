"""Zero-seed generator/support coherence audit for V3.6 bridge blocks."""

from __future__ import annotations

from dataclasses import replace
import math
from typing import Any, Mapping

from . import v32, v35, v36_bridge, v36_round12
from .trace_sink import serializing_trace_context


TOLERANCE = 1e-10
PARTNER_CHANNEL_TYPE = "remaining"


def _signs(structure: v35.ProtectStructure) -> tuple[int, ...]:
    """The frozen sign enumeration shared by v35 and v36_bridge."""
    return (-1, 1) if structure.cross_mode_outcome else (0,)


def _protect_prior_mass(
    structure: v35.ProtectStructure, sign: int, reliable: int
) -> float:
    signs = _signs(structure)
    if structure not in v35.PROGRAMS or sign not in signs or reliable not in (0, 1):
        return 0.0
    return math.exp(v35.structure_log_prior(structure)) / len(signs) / 2.0


def _temporal_prior_mass(structure: v32.TemporalStructure) -> float:
    if structure not in v32.PROGRAMS:
        return 0.0
    return math.exp(v32.structure_log_prior(structure))


def _adapter_log_mass(
    world: v36_bridge.CanonicalWorld, model: str
) -> tuple[float, float, tuple[Mapping[str, Any], ...]]:
    with serializing_trace_context(f"round16-coherence-{model}") as sink:
        predictions = (
            v36_bridge.score_v2(world)
            if model == "v2" else v36_bridge.score_v3(world)
        )
    targets = v36_bridge.observed_targets(world)
    log_mass = 0.0
    minimum = 1.0
    for target, prediction in predictions.items():
        for probabilities, delivered, observed in zip(
            prediction.probabilities, prediction.delivered, targets[target]
        ):
            if not delivered or observed is None:
                continue
            probability = float(probabilities[int(observed)])
            minimum = min(minimum, probability)
            if not math.isfinite(probability) or probability <= 0.0:
                return -math.inf, probability, tuple(sink.events)
            log_mass += math.log(probability)
    return log_mass, minimum, tuple(sink.events)


def _external_row(stratum: str) -> dict[str, Any]:
    structure, sign = v36_round12._external_structure(stratum)  # noqa: SLF001
    temporal = v36_round12._external_temporal(stratum)  # noqa: SLF001
    signs = _signs(structure)
    partner_rows = {
        str(reliable): [
            v35.partner_channel_probability(value, reliable, PARTNER_CHANNEL_TYPE)
            for value in (0, 1)
        ]
        for reliable in (0, 1)
    }
    v3_masses = [
        _protect_prior_mass(structure, sign, reliable)
        * _temporal_prior_mass(temporal)
        for reliable in (0, 1)
    ]
    dummy = replace(
        v36_bridge.public_dummy(),
        population="round16_zero_seed_external_coherence",
        stratum=stratum,
        active_modes=structure.active_modes,
        structure=structure,
        cross_sign=sign,
        temporal_structure=temporal,
    )
    v2_log_mass, v2_minimum, v2_events = _adapter_log_mass(dummy, "v2")
    v3_log_mass, v3_minimum, v3_events = _adapter_log_mass(dummy, "v3")
    partner_normalized = all(
        abs(math.fsum(row) - 1.0) <= TOLERANCE
        and all(math.isfinite(value) and value > 0.0 for value in row)
        for row in partner_rows.values()
    )
    passed = bool(
        structure in v35.PROGRAMS
        and sign in signs
        and temporal in v32.PROGRAMS
        and all(math.isfinite(value) and value > 0.0 for value in v3_masses)
        and partner_normalized
        and math.isfinite(v2_log_mass) and v2_minimum > 0.0
        and math.isfinite(v3_log_mass) and v3_minimum > 0.0
    )
    return {
        "stratum": stratum,
        "emitted_tuple": {
            "structure": {
                "active_modes": structure.active_modes,
                "mode_root_edges": list(structure.mode_root_edges),
                "joint_policy_outcome": structure.joint_policy_outcome,
                "cross_mode_outcome": structure.cross_mode_outcome,
            },
            "cross_sign": sign,
            "partner_channel_type": PARTNER_CHANNEL_TYPE,
            "temporal": {
                "active_contexts": temporal.active_contexts,
                "scopes": list(temporal.scopes),
                "dynamics": list(temporal.dynamics),
            },
        },
        "enumerated_sign_support": list(signs),
        "v3_native_prior_mass_by_partner_state": v3_masses,
        "v2_native_prior_predictive_log_mass": v2_log_mass,
        "v3_native_prior_predictive_log_mass": v3_log_mass,
        "v2_minimum_delivered_token_probability": v2_minimum,
        "v3_minimum_delivered_token_probability": v3_minimum,
        "partner_emission_rows": partner_rows,
        "partner_rows_normalized_positive": partner_normalized,
        "v2_trace_events": list(v2_events),
        "v3_trace_events": list(v3_events),
        "passed": passed,
    }


def _native_support() -> dict[str, Any]:
    protect = []
    for structure in v35.PROGRAMS:
        for sign in _signs(structure):
            for reliable in (0, 1):
                protect.append(_protect_prior_mass(structure, sign, reliable))
    temporal = [_temporal_prior_mass(program) for program in v32.PROGRAMS]
    passed = bool(
        protect and temporal
        and all(math.isfinite(value) and value > 0.0 for value in protect)
        and all(math.isfinite(value) and value > 0.0 for value in temporal)
        and abs(math.fsum(protect) - 1.0) <= TOLERANCE
        and abs(math.fsum(temporal) - 1.0) <= TOLERANCE
    )
    return {
        "strata": ["acute", "chronic", "danger", "mixed"],
        "same_complete_support_for_each_stratum": True,
        "protect_tuple_count": len(protect),
        "temporal_program_count": len(temporal),
        "protect_prior_sum": math.fsum(protect),
        "temporal_prior_sum": math.fsum(temporal),
        "minimum_protect_tuple_prior_mass": min(protect),
        "minimum_temporal_prior_mass": min(temporal),
        "passed": passed,
    }


def prove_generator_coherence() -> dict[str, Any]:
    external = [_external_row(stratum) for stratum in v36_round12.STRATA]
    native = _native_support()
    passed = all(row["passed"] for row in external) and native["passed"]
    return {
        "stage": "V3.6-R1",
        "proof": "permanent pre-block generator coherence",
        "zero_seed": True,
        "external_strata": external,
        "population_a_native_generator": native,
        "passed": passed,
        "verdict": "PASS" if passed else "FAIL_UNEXECUTABLE",
    }
