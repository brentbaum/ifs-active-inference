"""Independent arithmetic oracle for the V3.6-R1 bridge.

This module imports no production bridge helper.  It checks copied documents,
binary normalization, delivered-token scoring, and credible-set coverage from
plain serialized values.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np

from . import v32, v35
from v2.ref import v232_formation, v234, v24, v26a, v26b


PREFIX_SLICES = 48
HELDOUT_SLICES = 16


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def binary_normalization_error(
    predictions: Mapping[str, Sequence[Sequence[float]]],
) -> float:
    largest = 0.0
    for rows in predictions.values():
        for row in rows:
            if len(row) != 2 or min(row) < 0.0:
                return math.inf
            largest = max(largest, abs(math.fsum(row) - 1.0))
    return largest


def delivered_mean_log_score(
    probabilities: Sequence[Sequence[float]],
    observed: Sequence[int | None],
    delivered: Sequence[bool],
) -> float:
    values = []
    for row, value, available in zip(probabilities, observed, delivered):
        if not available or value is None:
            continue
        values.append(math.log(float(row[int(value)])))
    if not values:
        raise ValueError("oracle received no delivered observations")
    return math.fsum(values) / len(values)


def credible_set_contains(
    class_probabilities: Mapping[str, float],
    truth: str,
    mass: float,
) -> bool:
    cumulative = 0.0
    for key, probability in sorted(
        class_probabilities.items(), key=lambda item: (-item[1], item[0])
    ):
        cumulative += probability
        if key == truth:
            return True
        if cumulative >= mass:
            return False
    return False


def _binary(probability_one: float) -> tuple[float, float]:
    value = min(max(float(probability_one), 1e-15), 1.0 - 1e-15)
    return (1.0 - value, value)


def _v2_identity(world: Any) -> tuple[tuple[float, float], ...]:
    posterior = np.array(v232_formation.PRIOR, dtype=float, copy=True)
    configuration = {
        "event": True,
        "precision": "ordinary",
        "control": "low",
        "broadcast": "integrated",
        "real_danger": False,
    }
    emissions = []
    for candidate in v232_formation.LABELS:
        row = v232_formation.slice_distribution(candidate, **configuration)
        emissions.append(np.asarray([
            math.fsum(
                float(row[index])
                for index, atom in enumerate(v232_formation.SUPPORT)
                if atom[0] == value
            )
            for value in (0, 1)
        ]))
    for item in world.slices[:PREFIX_SLICES]:
        likelihood = np.asarray(
            [emission[int(item.identity)] for emission in emissions],
            dtype=float,
        )
        posterior *= likelihood
        posterior /= float(np.sum(posterior))
    probability = math.fsum(
        float(posterior[index]) * float(emissions[index][1])
        for index in range(len(emissions))
    )
    return tuple(_binary(probability) for _ in range(HELDOUT_SLICES))


def _v2_outcome(world: Any) -> tuple[tuple[float, float], ...]:
    episodes = tuple(
        v234.Episode(item.action, item.context_input, item.outcome)
        for item in world.slices[:PREFIX_SLICES]
    )
    posterior = np.asarray(v234.score(episodes).posterior, dtype=float)
    result = []
    for item in world.slices[PREFIX_SLICES:]:
        values = []
        for observed in (0, 1):
            likelihood, _conditional = v234.slice_likelihood(
                v234.Episode(item.action, item.context_input, observed)
            )
            values.append(float(posterior @ likelihood))
        normalizer = math.fsum(values)
        result.append((values[0] / normalizer, values[1] / normalizer))
    return tuple(result)


def _v2_context(world: Any) -> tuple[tuple[float, float], ...]:
    prefix = tuple(
        v24.Observation(
            item.cue,
            None,
            None if item.context is None else (
                "then_marker" if item.context == 0 else "now_marker"
            ),
            None,
        )
        for item in world.slices[:PREFIX_SLICES]
    )
    family_posterior = np.asarray(
        v24.compare_families(prefix)["posterior"], dtype=float
    )
    nuisance = np.asarray(v24._nuisance_initial(), dtype=float)  # noqa: SLF001
    nuisance_transition = np.asarray(v24._nuisance_transition(), dtype=float)  # noqa: SLF001
    context_split = dict(v24._cs_initial())  # noqa: SLF001
    change_point = dict(v24._cp_initial())  # noqa: SLF001
    for time, observation in enumerate(prefix):
        nuisance_likelihood = np.asarray(
            v24._nuisance_marker_likelihood(observation.marker), dtype=float  # noqa: SLF001
        )
        nuisance *= nuisance_likelihood
        nuisance /= float(np.sum(nuisance))
        for states, name in ((context_split, "cs"), (change_point, "cp")):
            likelihoods = {
                state: v24._marker_likelihood(  # noqa: SLF001
                    "then" if int(state[0]) == 0 else "now",
                    observation.marker,
                )
                for state in states
            }
            evidence = math.fsum(states[state] * likelihoods[state] for state in states)
            updated = {
                state: states[state] * likelihoods[state] / evidence
                for state in states
            }
            if name == "cs":
                context_split = updated
            else:
                change_point = updated
        if time < len(prefix) - 1:
            nuisance = np.asarray(nuisance @ nuisance_transition, dtype=float)
            nuisance /= float(np.sum(nuisance))
            context_split = dict(v24._cs_transition(context_split))  # noqa: SLF001
            change_point = dict(v24._cp_transition(change_point))  # noqa: SLF001
    nuisance = np.asarray(nuisance @ nuisance_transition, dtype=float)
    nuisance /= float(np.sum(nuisance))
    context_split = dict(v24._cs_transition(context_split))  # noqa: SLF001
    change_point = dict(v24._cp_transition(change_point))  # noqa: SLF001
    per_family = []
    for family in v24.FAMILIES:
        values = []
        for marker in ("then_marker", "now_marker"):
            if family in {
                "global_downweight", "cue_local_relearning", "continuous_drift"
            }:
                likelihood = np.asarray(
                    v24._nuisance_marker_likelihood(marker), dtype=float  # noqa: SLF001
                )
                value = float(nuisance @ likelihood)
            else:
                states = context_split if family == "context_split" else change_point
                value = math.fsum(
                    mass * v24._marker_likelihood(  # noqa: SLF001
                        "then" if int(state[0]) == 0 else "now", marker
                    )
                    for state, mass in states.items()
                )
            values.append(value)
        total = math.fsum(values)
        per_family.append((values[0] / total, values[1] / total))
    mixed = tuple(
        math.fsum(
            float(family_posterior[index]) * per_family[index][value]
            for index in range(len(per_family))
        )
        for value in (0, 1)
    )
    return tuple(
        (0.5, 0.5) if item.context is None else mixed
        for item in world.slices[PREFIX_SLICES:]
    )


def _v2_partner(world: Any) -> tuple[tuple[float, float], ...]:
    observations = tuple(
        v26a.PartnerObservation((None, item.partner, None, None))
        for item in world.slices[:PREFIX_SLICES]
    )
    filtered, _smoothed, _pairwise, _log_evidence = v26a.hmm_inference(
        observations
    )
    latent_next = np.asarray(filtered[-1], dtype=float) @ np.asarray(
        v26a.TRANSITION, dtype=float
    )
    probability = float(latent_next @ np.asarray(v26a.EMISSIONS[:, 1], dtype=float))
    return tuple(_binary(probability) for _ in range(HELDOUT_SLICES))


def _v2_contact(world: Any) -> tuple[tuple[float, float], ...]:
    observations = tuple(
        v26b.TrustObservation(False, policy_outcome=item.contact)
        for item in world.slices[:PREFIX_SLICES]
    )
    _trust, posterior, _log_evidence = v26b.trust_posteriors(observations)
    probability = float(
        np.asarray(posterior, dtype=float)
        @ np.asarray(v26b.OUTCOME_SUPPORT, dtype=float)
    )
    return tuple(_binary(probability) for _ in range(HELDOUT_SLICES))


def _v3_components(world: Any) -> tuple[tuple[Any, int, int, float, tuple[float, ...]], ...]:
    observations = tuple(
        v35.ProtectObservation(
            item.time, (None, None, None), item.identity,
            item.joint_policy, item.outcome, item.partner, None,
            (None, None, None), (None, None, None), None, 1.0,
            (0, 0, 0), (item.contact, None, None),
        )
        for item in world.slices[:PREFIX_SLICES]
    )
    components = []
    log_weights = []
    for structure in v35.PROGRAMS:
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                evidence, _modes, _support, contact = v35._component_evidence(  # noqa: SLF001
                    observations, structure, sign, reliable,
                    registration_enabled=True, denied_enabled=True,
                )
                log_weights.append(
                    v35.structure_log_prior(structure)
                    - math.log(len(signs)) - math.log(2.0) + evidence
                )
                components.append((structure, sign, reliable, contact))
    maximum = max(log_weights)
    normalizer = maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in log_weights)
    )
    return tuple(
        (structure, sign, reliable, math.exp(log_weight - normalizer), contact)
        for (structure, sign, reliable, contact), log_weight
        in zip(components, log_weights)
    )


def _v3_temporal(world: Any) -> tuple[tuple[Any, ...], tuple[float, ...]]:
    log_weights = []
    for program in v32.PROGRAMS:
        value = v32.structure_log_prior(program)
        for item in world.slices[:PREFIX_SLICES]:
            if item.context is None:
                continue
            probability = v32.emission_probability(
                program.scopes[0], program.dynamics[0], cue=item.cue,
                context=item.context_input, time=item.time, length=64,
            )
            value += math.log(
                probability if int(item.context) == 1
                else 1.0 - probability
            )
        log_weights.append(value)
    maximum = max(log_weights)
    normalizer = maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in log_weights)
    )
    return (
        tuple(v32.PROGRAMS),
        tuple(math.exp(value - normalizer) for value in log_weights),
    )


def direct_forecasts(world: Any, model: str) -> Mapping[str, tuple[tuple[float, float], ...]]:
    """Independently authored posterior-predictive enumeration.

    This path imports no production bridge helper and never consumes RNG.
    """
    if model == "v2":
        return {
            "identity": _v2_identity(world),
            "outcome": _v2_outcome(world),
            "context": _v2_context(world),
            "partner": _v2_partner(world),
            "contact": _v2_contact(world),
        }
    if model != "v3":
        raise ValueError("model must be v2 or v3")
    components = _v3_components(world)
    temporal_programs, temporal_probabilities = _v3_temporal(world)
    output = {}
    for target in ("identity", "outcome", "partner", "contact"):
        rows = []
        for item in world.slices[PREFIX_SLICES:]:
            probability = 0.0
            for structure, sign, reliable, mass, contact in components:
                if target == "identity":
                    conditional = v35.root_signal_probability(
                        1, item.modes_input, structure
                    )
                elif target == "outcome":
                    conditional = v35.outcome_probability(
                        item.joint_policy, item.modes_input, structure, sign
                    )
                elif target == "partner":
                    conditional = v35.partner_channel_probability(
                        1, reliable, "remaining"
                    )
                else:
                    conditional = (
                        (1.0 - contact[0])
                        * v35.contact_probability(
                            1, reliable, item.joint_policy[0], 0
                        )
                        + contact[0]
                        * v35.contact_probability(
                            1, reliable, item.joint_policy[0], 1
                        )
                    )
                probability += mass * conditional
            rows.append(_binary(probability))
        output[target] = tuple(rows)
    context_rows = []
    for item in world.slices[PREFIX_SLICES:]:
        if item.context is None:
            context_rows.append((0.5, 0.5))
            continue
        probability = math.fsum(
            float(mass)
            * v32.emission_probability(
                program.scopes[0], program.dynamics[0], cue=item.cue,
                context=item.context_input, time=item.time, length=64,
            )
            for program, mass in zip(
                temporal_programs, temporal_probabilities
            )
        )
        context_rows.append(_binary(probability))
    output["context"] = tuple(context_rows)
    return output
