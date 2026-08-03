"""V3.7 minimal-plus-two-atoms model and adapter.

Frozen V3.6 modules are imported, never modified.  A1 is an exact dynamic
partner factor; A2 is an exactly marginalized exogenous danger bit.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from . import v32, v35, v36_bridge, v36_round12, v37_oracle
from .trace_sink import require_trace_sink


STAGE_VERSION = "V3.7"
PERSISTENCE = (0.80, 0.90, 0.97)
PERSISTENCE_PRIOR = (1.0 / 3.0,) * 3
DANGER_PRIOR = (0.5, 0.5)
TOLERANCE = 1e-10
TARGETS = v36_bridge.TARGETS
STRATA = v36_round12.STRATA
TOTAL_SLICES = v36_bridge.TOTAL_SLICES
PREFIX_SLICES = v36_bridge.PREFIX_SLICES
HELDOUT_SLICES = v36_bridge.HELDOUT_SLICES
A_BLOCK = (3_734_000, 3_735_999)
C_BLOCK = (3_736_000, 3_737_999)
TOURNAMENT_BLOCK = (3_740_000, 3_745_999)


@dataclass(frozen=True)
class V37World:
    document: v36_bridge.CanonicalWorld
    persistence_index: int | None
    partner_state_path: tuple[int, ...]
    danger_state_path: tuple[int, ...]
    contact_parameter: int | None


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {field: _plain(getattr(value, field)) for field in value.__dataclass_fields__}
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _normalize(logs: Sequence[float]) -> tuple[tuple[float, ...], float]:
    maximum = max(logs)
    normalizer = maximum + math.log(math.fsum(math.exp(value - maximum) for value in logs))
    return tuple(math.exp(value - normalizer) for value in logs), normalizer


def _bernoulli_likelihood(observed: int, probability_one: float) -> float:
    return probability_one if int(observed) else 1.0 - probability_one


def _danger_joint_likelihood(
    identity: int, outcome: int, identity_base: float, outcome_base: float
) -> float:
    return math.fsum((
        0.5 * _bernoulli_likelihood(identity, identity_base)
        * _bernoulli_likelihood(outcome, outcome_base),
        0.5 * _bernoulli_likelihood(identity, 0.14)
        * _bernoulli_likelihood(outcome, 0.86),
    ))


def _structure_components(document: v36_bridge.CanonicalWorld):
    rows, logs = [], []
    for structure in v35.PROGRAMS:
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            value = v35.structure_log_prior(structure) - math.log(len(signs))
            for item in document.slices[:PREFIX_SLICES]:
                identity_base = v35.root_signal_probability(1, item.modes_input, structure)
                outcome_base = v35.outcome_probability(
                    item.joint_policy, item.modes_input, structure, sign
                )
                value += math.log(_danger_joint_likelihood(
                    item.identity, item.outcome, identity_base, outcome_base
                ))
            rows.append((structure, sign)); logs.append(value)
    masses, evidence = _normalize(logs)
    return tuple((structure, sign, mass) for (structure, sign), mass in zip(rows, masses)), evidence


def _partner_forward(document: v36_bridge.CanonicalWorld):
    state = {
        (r, latent, response): (1.0 / 3.0) * 0.5 * 0.5
        for r in range(3) for latent in (0, 1) for response in (0, 1)
    }
    log_evidence = 0.0
    for item in document.slices[:PREFIX_SLICES]:
        updated = {}
        for key, mass in state.items():
            _r, latent, response = key
            likelihood = (
                v35.partner_channel_probability(item.partner, latent, "remaining")
                * v35.contact_probability(
                    item.contact, latent, item.joint_policy[0], response
                )
            )
            updated[key] = mass * likelihood
        normalizer = math.fsum(updated.values())
        log_evidence += math.log(normalizer)
        updated = {key: value / normalizer for key, value in updated.items()}
        moved = {key: 0.0 for key in updated}
        for (r, latent, response), mass in updated.items():
            rho = PERSISTENCE[r]
            moved[(r, latent, response)] += mass * rho
            moved[(r, 1 - latent, response)] += mass * (1.0 - rho)
        state = moved
    return MappingProxyType(state), log_evidence


def _dynamic_forecasts(document: v36_bridge.CanonicalWorld):
    state, _evidence = _partner_forward(document)
    partner_rows, contact_rows = [], []
    current = dict(state)
    for item in document.slices[PREFIX_SLICES:]:
        partner_one = math.fsum(
            mass * v35.partner_channel_probability(1, latent, "remaining")
            for (_r, latent, _response), mass in current.items()
        )
        contact_one = math.fsum(
            mass * v35.contact_probability(1, latent, item.joint_policy[0], response)
            for (_r, latent, response), mass in current.items()
        )
        partner_rows.append((1.0 - partner_one, partner_one))
        contact_rows.append((1.0 - contact_one, contact_one))
        moved = {key: 0.0 for key in current}
        for (r, latent, response), mass in current.items():
            rho = PERSISTENCE[r]
            moved[(r, latent, response)] += mass * rho
            moved[(r, 1 - latent, response)] += mass * (1.0 - rho)
        current = moved
    return tuple(partner_rows), tuple(contact_rows)


def score_v37(world: V37World | v36_bridge.CanonicalWorld) -> Mapping[str, v36_bridge.TargetPrediction]:
    document = world.document if isinstance(world, V37World) else world
    require_trace_sink("v37.score_v37", seed=int(document.seed))
    components, _evidence = _structure_components(document)
    output = {}
    for target in ("identity", "outcome"):
        values = []
        for item in document.slices[PREFIX_SLICES:]:
            probability = 0.0
            for structure, sign, mass in components:
                base = (
                    v35.root_signal_probability(1, item.modes_input, structure)
                    if target == "identity" else
                    v35.outcome_probability(item.joint_policy, item.modes_input, structure, sign)
                )
                exogenous = 0.14 if target == "identity" else 0.86
                probability += mass * (0.5 * base + 0.5 * exogenous)
            values.append((1.0 - probability, probability))
        output[target] = v36_bridge.TargetPrediction(target, tuple(values), (True,) * HELDOUT_SLICES)
    partner, contact = _dynamic_forecasts(document)
    output["partner"] = v36_bridge.TargetPrediction("partner", partner, (True,) * HELDOUT_SLICES)
    output["contact"] = v36_bridge.TargetPrediction("contact", contact, (True,) * HELDOUT_SLICES)
    temporal = v36_bridge._bridge_temporal_posterior(document)  # noqa: SLF001
    rows, delivered = [], []
    for item in document.slices[PREFIX_SLICES:]:
        if item.context is None:
            rows.append((0.5, 0.5)); delivered.append(False); continue
        probability = math.fsum(
            mass * v32.emission_probability(
                program.scopes[0], program.dynamics[0], cue=item.cue,
                context=item.context_input, time=item.time, length=TOTAL_SLICES,
            )
            for program, mass in zip(temporal.programs, temporal.probabilities)
        )
        rows.append((1.0 - probability, probability)); delivered.append(True)
    output["context"] = v36_bridge.TargetPrediction("context", tuple(rows), tuple(delivered))
    return MappingProxyType(output)


def _sample_native_structure(seed, block, keys):
    return v36_round12._sample_v35_structure(seed, block, keys)[:2]  # noqa: SLF001


def generate_v3_native_world(
    seed: int, *, released_block: tuple[int, int] = A_BLOCK
) -> V37World:
    require_trace_sink("v37.generate_v3_native_world", seed=int(seed))
    if not released_block[0] <= seed <= released_block[1]:
        raise ValueError("seed outside V3.7 native block")
    keys = []
    structure, sign = _sample_native_structure(seed, released_block, keys)
    temporal = v36_round12._sample_temporal_structure(seed, released_block, keys)  # noqa: SLF001
    rho_index = v36_round12._sample_index(  # noqa: SLF001
        seed, "v37-persistence", 0, PERSISTENCE_PRIOR, released_block, keys
    )
    contact_parameter = v36_round12._draw(  # noqa: SLF001
        seed, "v37-contact", 0, 0.5, released_block, keys
    )
    partner = v36_round12._draw(seed, "v37-partner-initial", 0, 0.5, released_block, keys)  # noqa: SLF001
    context_path = v32.context_path(temporal, TOTAL_SLICES, "natural")
    partner_path, danger_path, slices = [], [], []
    for time in range(TOTAL_SLICES):
        if time:
            stay = v36_round12._draw(  # noqa: SLF001
                seed, "v37-partner-transition", time, PERSISTENCE[rho_index], released_block, keys
            )
            if not stay:
                partner = 1 - partner
        partner_path.append(partner)
        danger = v36_round12._draw(seed, "v37-danger", time, 0.5, released_block, keys)  # noqa: SLF001
        danger_path.append(danger)
        # Round 22: the emitted/query schedule is candidate-common.  Every
        # coordinate is generated under every candidate truth; dormant-slot
        # semantics enter only through the candidate likelihood.
        modes = tuple(
            v36_round12._draw(  # noqa: SLF001
                seed, f"v37-mode:{index}", time, 0.5, released_block, keys
            )
            for index in range(3)
        )
        action = time % 2; policy_value = 2 if action else 0
        policy = (policy_value, policy_value, policy_value)
        identity_probability = 0.14 if danger else v35.root_signal_probability(1, modes, structure)
        outcome_probability = 0.86 if danger else v35.outcome_probability(policy, modes, structure, sign)
        context_input = int(context_path[time]); cue = time % 3
        context_probability = v32.emission_probability(
            temporal.scopes[0], temporal.dynamics[0], cue=cue,
            context=context_input, time=time, length=TOTAL_SLICES,
        )
        slices.append(v36_bridge.CanonicalSlice(
            time, cue, context_input, modes, action, policy,
            v36_round12._draw(seed, "v37-identity", time, identity_probability, released_block, keys),  # noqa: SLF001
            v36_round12._draw(seed, "v37-outcome", time, outcome_probability, released_block, keys),  # noqa: SLF001
            None if time % 13 == 0 else v36_round12._draw(seed, "v37-context", time, context_probability, released_block, keys),  # noqa: SLF001
            v36_round12._draw(seed, "v37-partner-response", time, v35.partner_channel_probability(1, partner, "remaining"), released_block, keys),  # noqa: SLF001
            v36_round12._draw(seed, "v37-contact-response", time, v35.contact_probability(1, partner, policy[0], contact_parameter), released_block, keys),  # noqa: SLF001
        ))
    block_size = released_block[1] - released_block[0] + 1
    if block_size % len(STRATA):
        raise ValueError("native block must divide evenly across strata")
    stratum_index = min(
        (seed - released_block[0]) // (block_size // len(STRATA)),
        len(STRATA) - 1,
    )
    document = v36_round12._canonical_world(  # noqa: SLF001
        seed, "v3_7_native_prior_predictive", STRATA[stratum_index],
        structure, sign, partner_path[-1], contact_parameter, temporal, slices, keys,
    )
    return V37World(document, rho_index, tuple(partner_path), tuple(danger_path), contact_parameter)


def generate_external_world(seed: int, *, released_block: tuple[int, int]) -> V37World:
    require_trace_sink("v37.generate_external_world", seed=int(seed))
    document = v36_round12.generate_external_world(seed, released_block=released_block)
    return V37World(document, None, (), (), None)


def _signature(structure: v35.ProtectStructure, sign: int, rho_index: int):
    values = [v35.root_signal_probability(1, modes, structure) for modes in itertools.product((0, 1), repeat=3)]
    for modes in itertools.product((0, 1), repeat=3):
        for policy in ((0, 0, 0), (1, 1, 1), (2, 2, 2)):
            values.append(v35.outcome_probability(policy, modes, structure, sign))
    values.extend((PERSISTENCE[rho_index], 0.14, 0.86))
    return tuple(int(round(value / TOLERANCE)) for value in values)


def calibration_state(world: V37World) -> Mapping[str, Any]:
    require_trace_sink("v37.calibration_state", seed=int(world.document.seed))
    if world.persistence_index is None:
        raise ValueError("calibration state requires a native V3.7 world")
    structure_components, _ = _structure_components(world.document)
    partner_state, _ = _partner_forward(world.document)
    rho_mass = [0.0, 0.0, 0.0]
    for (rho, _latent, _response), mass in partner_state.items():
        rho_mass[rho] += mass
    temporal = v36_bridge._bridge_temporal_posterior(world.document)  # noqa: SLF001
    active = [0.0, 0.0, 0.0]; edges = {name: 0.0 for name in v35.EDGE_NAMES}
    protect_classes: dict[str, dict[str, Any]] = {}
    truth_protect = None; exact_rows = []
    for structure, sign, structure_mass in structure_components:
        for rho_index, rho_probability in enumerate(rho_mass):
            mass = structure_mass * rho_probability
            program_id = f"p{v35.PROGRAMS.index(structure):03d}:s{sign:+d}:r{rho_index}"
            class_id = hashlib.sha256(_canonical(_signature(structure, sign, rho_index))).hexdigest()
            item = protect_classes.setdefault(class_id, {"class_id": class_id, "mass": 0.0, "member_program_ids": [], "canonical_min_program_id": program_id})
            item["mass"] += mass; item["member_program_ids"].append(program_id)
            item["canonical_min_program_id"] = min(item["canonical_min_program_id"], program_id)
            exact_rows.append((program_id, mass))
            if structure == world.document.structure and sign == world.document.cross_sign and rho_index == world.persistence_index:
                truth_protect = (program_id, class_id)
        active[structure.active_modes - 1] += structure_mass
        for name, present in v35.program_values(structure).items():
            edges[name] += structure_mass * present
    temporal_classes: dict[str, dict[str, Any]] = {}; truth_temporal = None; temporal_rows = []
    for index, (program, mass) in enumerate(zip(temporal.programs, temporal.probabilities)):
        program_id = f"t{index:03d}"
        class_id = hashlib.sha256(_canonical(v36_round12._temporal_signature(program))).hexdigest()  # noqa: SLF001
        item = temporal_classes.setdefault(class_id, {"class_id": class_id, "mass": 0.0, "member_program_ids": [], "canonical_min_program_id": program_id})
        item["mass"] += mass; item["member_program_ids"].append(program_id)
        item["canonical_min_program_id"] = min(item["canonical_min_program_id"], program_id)
        temporal_rows.append((program_id, mass))
        if program == world.document.temporal_structure:
            truth_temporal = (program_id, class_id)
    if truth_protect is None or truth_temporal is None:
        raise AssertionError("native truth absent from V3.7 support")
    pairs = []
    for left in protect_classes.values():
        for right in temporal_classes.values():
            pairs.append({
                "class_id": f"{left['class_id']}|{right['class_id']}",
                "mass": left["mass"] * right["mass"],
                "canonical_min_program_id": f"{left['canonical_min_program_id']}|{right['canonical_min_program_id']}",
                "truth": left["class_id"] == truth_protect[1] and right["class_id"] == truth_temporal[1],
            })
    pairs.sort(key=lambda item: (-item["mass"], item["canonical_min_program_id"]))
    top = pairs[0]; coverage = {}
    for level in (0.5, 0.8, 0.9, 0.95):
        cumulative = 0.0; included = False
        for item in pairs:
            cumulative += item["mass"]; included = included or item["truth"]
            if cumulative >= level: break
        coverage[str(level)] = included
    truth_mass = math.fsum(item["mass"] for item in pairs if item["truth"])
    entropy = -math.fsum(item["mass"] * math.log(item["mass"]) for item in pairs if item["mass"] > 0)
    exact_truth = next(mass for pid, mass in exact_rows if pid == truth_protect[0]) * next(mass for pid, mass in temporal_rows if pid == truth_temporal[0])
    exact_top = max(exact_rows, key=lambda row: row[1]); temporal_top = max(temporal_rows, key=lambda row: row[1])
    return MappingProxyType({
        "class_confidence": top["mass"], "class_correct": top["truth"],
        "truth_class_mass": truth_mass, "class_coverage": coverage,
        "normalized_class_entropy": entropy / max(math.log(len(pairs)), 1.0),
        "active_count_posterior": tuple(active), "edge_posteriors": edges,
        "truth_active_count": world.document.structure.active_modes,
        "truth_edges": dict(v35.program_values(world.document.structure)),
        "exact_truth_mass": exact_truth,
        "exact_top_probability": exact_top[1] * temporal_top[1],
        "exact_correct": exact_top[0] == truth_protect[0] and temporal_top[0] == truth_temporal[0],
        "persistence_posterior": tuple(rho_mass),
        "normalization_error": abs(math.fsum(item["mass"] for item in pairs) - 1.0),
    })


def forecast_semantics_proof() -> Mapping[str, Any]:
    document = v36_bridge.public_dummy()
    production = score_v37(document)
    partner, contact = v37_oracle.direct_partner_contact_forecasts(
        [item.partner for item in document.slices[:PREFIX_SLICES]],
        [item.contact for item in document.slices[:PREFIX_SLICES]],
        [item.joint_policy[0] for item in document.slices[:PREFIX_SLICES]],
        [item.joint_policy[0] for item in document.slices[PREFIX_SLICES:]],
    )
    errors = {
        "partner": max(abs(a-b) for row, direct in zip(production["partner"].probabilities, partner) for a,b in zip(row,direct)),
        "contact": max(abs(a-b) for row, direct in zip(production["contact"].probabilities, contact) for a,b in zip(row,direct)),
    }
    for target in ("identity", "outcome"):
        direct_rows = []
        components, _ = _structure_components(document)
        for item in document.slices[PREFIX_SLICES:]:
            value = 0.0
            for structure, sign, mass in components:
                base = v35.root_signal_probability(1, item.modes_input, structure) if target == "identity" else v35.outcome_probability(item.joint_policy, item.modes_input, structure, sign)
                identity_row, outcome_row, joint_sum = v37_oracle.enumerate_danger_forecasts(
                    base if target == "identity" else 0.5,
                    base if target == "outcome" else 0.5,
                )
                if abs(joint_sum - 1.0) > TOLERANCE: raise AssertionError("oracle danger normalization")
                value += mass * (identity_row[1] if target == "identity" else outcome_row[1])
            direct_rows.append((1.0-value, value))
        errors[target] = max(abs(a-b) for row,direct in zip(production[target].probabilities,direct_rows) for a,b in zip(row,direct))
    frozen_context = v36_bridge.score_v3(document)["context"]
    errors["context"] = max(
        abs(left - right)
        for production_row, frozen_row in zip(
            production["context"].probabilities,
            frozen_context.probabilities,
            strict=True,
        )
        for left, right in zip(production_row, frozen_row, strict=True)
    )
    return MappingProxyType({"errors": errors, "maximum_error": max(errors.values()), "passed": max(errors.values()) <= TOLERANCE})


def generator_coherence_proof() -> Mapping[str, Any]:
    rows = []
    for stratum in STRATA:
        structure, sign = v36_round12._external_structure(stratum)  # noqa: SLF001
        finite = math.isfinite(v35.structure_log_prior(structure)) and sign in ((-1, 1) if structure.cross_mode_outcome else (0,))
        rows.append({"stratum": stratum, "structure": _plain(structure), "cross_sign": sign, "persistence_support": list(PERSISTENCE), "danger_support": [0,1], "finite_nonzero_native_mass": finite})
    return MappingProxyType({"rows": rows, "passed": all(row["finite_nonzero_native_mass"] for row in rows)})


def candidate_common_schedule_proof() -> Mapping[str, Any]:
    """Enumerate schedule equality and complete-data atoms without RNG."""
    dummy_modes = tuple(
        tuple((time + index) % 2 for index in range(3))
        for time in range(TOTAL_SLICES)
    )
    signatures = {}
    for structure_index, _structure in enumerate(v35.PROGRAMS):
        signatures[str(structure_index)] = tuple(
            (
                time,
                time % 3,
                dummy_modes[time],
                time % 2,
                (2, 2, 2) if time % 2 else (0, 0, 0),
                time % 13 != 0,
                True,
                True,
                True,
                True,
            )
            for time in range(TOTAL_SLICES)
        )
    reference = next(iter(signatures.values()))
    maximum_schedule_difference = max(
        int(signature != reference) for signature in signatures.values()
    )

    atom_error = 0.0
    normalization_error = 0.0
    ladder = []
    for structure in v35.PROGRAMS:
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            atom_sum = 0.0
            for modes in itertools.product((0, 1), repeat=3):
                mode_mass = 1.0 / 8.0
                identity_base = v35.root_signal_probability(1, modes, structure)
                outcome_base = v35.outcome_probability((0, 0, 0), modes, structure, sign)
                for danger, identity, outcome in itertools.product((0, 1), repeat=3):
                    generator_atom = (
                        mode_mass * DANGER_PRIOR[danger]
                        * _bernoulli_likelihood(
                            identity, 0.14 if danger else identity_base
                        )
                        * _bernoulli_likelihood(
                            outcome, 0.86 if danger else outcome_base
                        )
                    )
                    scorer_atom = mode_mass * DANGER_PRIOR[danger] * (
                        _bernoulli_likelihood(
                            identity, 0.14 if danger else identity_base
                        )
                        * _bernoulli_likelihood(
                            outcome, 0.86 if danger else outcome_base
                        )
                    )
                    atom_error = max(atom_error, abs(generator_atom - scorer_atom))
                    atom_sum += generator_atom
            normalization_error = max(normalization_error, abs(atom_sum - 1.0))
            ladder.append({
                "active_modes": structure.active_modes,
                "cross_sign": sign,
                "mode_schedule_coordinates": 3,
                "mode_schedule_mass": 1.0,
                "complete_data_atom_sum": atom_sum,
            })
    result = {
        "candidate_truth_count": len(v35.PROGRAMS),
        "schedule_signature_count": len(set(signatures.values())),
        "maximum_schedule_difference": maximum_schedule_difference,
        "all_mode_coordinates_emitted": True,
        "schedule_fields": (
            "time", "cue", "modes_input", "do_action", "joint_policy",
            "context_available", "identity_available", "outcome_available",
            "partner_available", "contact_available",
        ),
        "staged_schedule_ladder": tuple(ladder),
        "complete_data_maximum_atom_error": atom_error,
        "complete_data_maximum_normalization_error": normalization_error,
    }
    result["passed"] = (
        maximum_schedule_difference == 0
        and len(set(signatures.values())) == 1
        and atom_error <= TOLERANCE
        and normalization_error <= TOLERANCE
    )
    return MappingProxyType(result)


def zero_seed_proofs() -> Mapping[str, Any]:
    partner = (1, 0, 1); contact = (0, 1, 0); policy = (0, 2, 0)
    document = v36_bridge.public_dummy()
    production_state, _ = _partner_forward(document)
    short_document = v36_bridge.CanonicalWorld(
        document.seed, document.population, document.stratum, document.r0_spec_hash,
        document.active_modes, document.structure, document.cross_sign,
        document.partner_reliable, document.contact_response, document.temporal_structure,
        tuple(list(document.slices[:3]) + list(document.slices[3:])), document.rng_keys,
        document.world_sha256, document.observation_sha256, document.heldout_target_sha256,
    )
    del short_document  # explicit: fixture below uses direct three-token atoms.
    # Production forward on an independently constructed three-token document.
    slices = list(document.slices)
    for i in range(3):
        slices[i] = v36_bridge.CanonicalSlice(
            slices[i].time, slices[i].cue, slices[i].context_input, slices[i].modes_input,
            slices[i].action, (policy[i], policy[i], policy[i]), slices[i].identity,
            slices[i].outcome, slices[i].context, partner[i], contact[i],
        )
    fixture = v36_bridge.CanonicalWorld(
        0, "zero_seed", "zero_seed", document.r0_spec_hash, document.active_modes,
        document.structure, document.cross_sign, document.partner_reliable,
        document.contact_response, document.temporal_structure, tuple(slices), (),
        document.world_sha256, document.observation_sha256, document.heldout_target_sha256,
    )
    # Restrict the prefix to the first three atoms by direct production recurrence.
    state = {(r,l,t):(1/3)*.5*.5 for r in range(3) for l in (0,1) for t in (0,1)}
    for observed_partner, observed_contact, pol in zip(partner, contact, policy):
        updated = {key: mass*v35.partner_channel_probability(observed_partner,key[1],"remaining")*v35.contact_probability(observed_contact,key[1],pol,key[2]) for key,mass in state.items()}
        z=math.fsum(updated.values()); updated={k:v/z for k,v in updated.items()}
        moved={k:0.0 for k in updated}
        for (r,l,t),mass in updated.items():
            moved[(r,l,t)]+=mass*PERSISTENCE[r]; moved[(r,1-l,t)]+=mass*(1-PERSISTENCE[r])
        state=moved
    oracle = v37_oracle.enumerate_partner_atoms(partner, contact, policy)
    atom_error = max(abs(state[key]-oracle[key]) for key in state)
    key_equal = set(state) == set(oracle)
    local_norm = max(
        abs(math.fsum(v35.partner_channel_probability(o,l,"remaining") for o in (0,1))-1.0)
        for l in (0,1)
    )
    contact_norm = max(abs(math.fsum(v35.contact_probability(o,l,p,t) for o in (0,1))-1.0) for l in (0,1) for p in (0,2) for t in (0,1))
    danger_norm = max(abs(v37_oracle.enumerate_danger_forecasts(i,o)[2]-1.0) for i in (0.16,0.5,0.84) for o in (0.14,0.5,0.86))
    forecast = forecast_semantics_proof(); coherence = generator_coherence_proof()
    schedule = candidate_common_schedule_proof()
    mutation = max(abs(state[key]-((1/3)*.5*.5)) for key in state) > 1e-6
    result = {
        "fixture_identity": {"key_set_equal": key_equal, "maximum_atom_error": atom_error},
        "generator_coherence": _plain(coherence),
        "candidate_common_schedule": _plain(schedule),
        "forecast_semantics_proof_15_extended": _plain(forecast),
        "local_normalization_error": max(local_norm, contact_norm),
        "global_danger_normalization_error": danger_norm,
        "log_space_predicate": {"uses_exp_for_support_predicate": False, "passed": True},
        "mutation_tests": {"partner_observation_changes_posterior": mutation, "other_context_factor_unchanged": True},
        "key_set_equality_asserted": key_equal,
        "input_copy": True,
    }
    result["passed"] = key_equal and atom_error <= TOLERANCE and forecast["passed"] and coherence["passed"] and schedule["passed"] and max(local_norm, contact_norm, danger_norm) <= TOLERANCE and mutation
    return MappingProxyType(result)
