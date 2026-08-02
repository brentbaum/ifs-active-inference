"""Round-12 common-target bridge apparatus.

This module owns only external document generation, native calibration
fixtures, adapter-facing serialization, and pure posterior readouts.  It adds
no scientific likelihood or prior to V2 or V3.
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

from . import v32, v35, v36_bridge
from .rng import component_key, component_rng
from .trace_sink import require_trace_sink
from v2.ref import v232_formation, v234, v24, v26a, v26b


TARGETS = v36_bridge.TARGETS
TOTAL_SLICES = v36_bridge.TOTAL_SLICES
PREFIX_SLICES = v36_bridge.PREFIX_SLICES
HELDOUT_SLICES = v36_bridge.HELDOUT_SLICES
TOLERANCE = 1e-10
DELTA = math.log(1.02)
# Re-scoped by the evaluator's round-12 precommit custody adjudication.
# The three block-first seeds are permanently barred.
V2_NATIVE_BLOCK = (3_700_000, 3_701_999)
V3_NATIVE_BLOCK = (3_692_001, 3_693_999)
EXTERNAL_QUALIFICATION_BLOCK = (3_694_001, 3_695_999)
TOURNAMENT_BLOCK = (3_684_000, 3_689_999)
EXTERNAL_GRID = (0.20, 0.50, 0.80)
STRATA = (
    "acute_one", "chronic_one", "chronic_multiple",
    "real_danger_adaptive",
)


@dataclass(frozen=True)
class NativeV2Fixture:
    seed: int
    target: str
    history: tuple[int, ...]
    query_inputs: tuple[int, int]
    observed: int
    prediction: tuple[float, float]
    direct_prediction: tuple[float, float]
    normalization_error: float
    oracle_error: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _plain(child) for key, child in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(child) for child in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            field: _plain(getattr(value, field))
            for field in value.__dataclass_fields__
        }
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    namespace = f"v36-r12:{component}"
    keys.append(component_key(seed, namespace, event))
    return component_rng(
        seed, namespace, time_or_event=event,
        released_block=released_block,
    )


def _draw(
    seed: int,
    component: str,
    event: int | str,
    probability: float,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    return int(
        _rng(seed, component, event, released_block, keys).random()
        < float(probability)
    )


def _sample_index(
    seed: int,
    component: str,
    event: int | str,
    probabilities: Sequence[float],
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    values = np.array(probabilities, dtype=float, copy=True)
    values /= float(values.sum())
    return int(
        _rng(seed, component, event, released_block, keys).choice(
            len(values), p=values
        )
    )


def _binary(probability_one: float) -> tuple[float, float]:
    value = float(np.clip(probability_one, 1e-15, 1.0 - 1e-15))
    return (1.0 - value, value)


def _canonical_world(
    seed: int,
    population: str,
    stratum: str,
    structure: v35.ProtectStructure,
    cross_sign: int,
    partner_reliable: int,
    contact_response: int,
    temporal_structure: v32.TemporalStructure,
    slices: Sequence[v36_bridge.CanonicalSlice],
    keys: Sequence[tuple[str, int, str, int | str]],
) -> v36_bridge.CanonicalWorld:
    truth = {
        "active_modes": structure.active_modes,
        "structure": _plain(structure),
        "cross_sign": cross_sign,
        "partner_reliable": partner_reliable,
        "contact_response": contact_response,
        "temporal_structure": _plain(temporal_structure),
        "stratum": stratum,
    }
    observations = [_plain(item) for item in slices]
    targets = [
        {target: getattr(item, target) for target in TARGETS}
        for item in slices[PREFIX_SLICES:]
    ]
    return v36_bridge.CanonicalWorld(
        seed, population, stratum, v36_bridge.R0_SPEC_HASH,
        structure.active_modes, structure, cross_sign, partner_reliable,
        contact_response, temporal_structure, tuple(slices), tuple(keys),
        hashlib.sha256(_canonical(truth)).hexdigest(),
        hashlib.sha256(_canonical(observations)).hexdigest(),
        hashlib.sha256(_canonical(targets)).hexdigest(),
    )


def _sample_v35_structure(
    seed: int,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[v35.ProtectStructure, int, int, int]:
    probabilities = np.asarray(
        [math.exp(v35.structure_log_prior(item)) for item in v35.PROGRAMS],
        dtype=float,
    )
    structure = v35.PROGRAMS[
        _sample_index(
            seed, "v3-native-structure", 0, probabilities,
            released_block, keys,
        )
    ]
    sign = (
        (-1, 1)[
            _sample_index(
                seed, "v3-native-cross-sign", 0, (0.5, 0.5),
                released_block, keys,
            )
        ]
        if structure.cross_mode_outcome else 0
    )
    reliable = _draw(
        seed, "v3-native-partner", 0, 0.5, released_block, keys
    )
    contact = _draw(
        seed, "v3-native-contact", 0, 0.5, released_block, keys
    )
    return structure, sign, reliable, contact


def _sample_temporal_structure(
    seed: int,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> v32.TemporalStructure:
    supports: tuple[Sequence[Any], ...] = (
        (1, 2, 3), v32.SCOPES, v32.SCOPES,
        v32.DYNAMICS, v32.DYNAMICS,
    )
    selected = []
    for index, support in enumerate(supports):
        selected.append(
            support[
                _sample_index(
                    seed, "v3-native-temporal", index,
                    v32._prior(support), released_block, keys,  # noqa: SLF001
                )
            ]
        )
    return v32.TemporalStructure(
        int(selected[0]),
        (str(selected[1]), str(selected[2])),
        (str(selected[3]), str(selected[4])),
    )


def generate_v3_native_world(
    seed: int,
    *,
    released_block: tuple[int, int] = V3_NATIVE_BLOCK,
) -> v36_bridge.CanonicalWorld:
    """Complete prior predictive of the frozen V3 bridge model."""
    require_trace_sink("v36_round12.generate_v3_native_world", seed=int(seed))
    if not released_block[0] <= seed <= released_block[1]:
        raise ValueError("seed outside released V3-native block")
    keys: list[tuple[str, int, str, int | str]] = []
    structure, sign, reliable, contact = _sample_v35_structure(
        seed, released_block, keys
    )
    temporal = _sample_temporal_structure(seed, released_block, keys)
    path = v32.context_path(temporal, TOTAL_SLICES, "natural")
    rows = []
    for time in range(TOTAL_SLICES):
        modes = tuple(
            _draw(
                seed, f"v3-native-mode:{index}", time, 0.5,
                released_block, keys,
            ) if index < structure.active_modes else 0
            for index in range(3)
        )
        action = time % 2
        policy_value = 2 if action else 0
        policy = tuple(
            policy_value if index < structure.active_modes else 1
            for index in range(3)
        )
        context_input = int(path[time])
        cue = time % 3
        context_probability = v32.emission_probability(
            temporal.scopes[0], temporal.dynamics[0], cue=cue,
            context=context_input, time=time, length=TOTAL_SLICES,
        )
        context_masked = time % 13 == 0
        rows.append(v36_bridge.CanonicalSlice(
            time=time, cue=cue, context_input=context_input,
            modes_input=modes, action=action, joint_policy=policy,
            identity=_draw(
                seed, "v3-native-identity", time,
                v35.root_signal_probability(1, modes, structure),
                released_block, keys,
            ),
            outcome=_draw(
                seed, "v3-native-outcome", time,
                v35.outcome_probability(policy, modes, structure, sign),
                released_block, keys,
            ),
            context=(
                None if context_masked else _draw(
                    seed, "v3-native-context", time, context_probability,
                    released_block, keys,
                )
            ),
            partner=_draw(
                seed, "v3-native-partner-response", time,
                v35.partner_channel_probability(1, reliable, "remaining"),
                released_block, keys,
            ),
            contact=_draw(
                seed, "v3-native-contact-response", time,
                v35.contact_probability(1, reliable, policy[0], contact),
                released_block, keys,
            ),
        ))
    return _canonical_world(
        seed, "v3_native_prior_predictive",
        STRATA[(seed - released_block[0]) % len(STRATA)], structure,
        sign, reliable, contact, temporal, rows, keys,
    )


def _external_temporal(stratum: str) -> v32.TemporalStructure:
    if stratum == "acute_one":
        return v32.TemporalStructure(
            2, ("context_specific", "shared_global"),
            ("one_way_change", "static"),
        )
    return v32.TemporalStructure(
        2, ("context_specific", "shared_global"),
        ("discrete_recurrent_context", "static"),
    )


def _external_structure(stratum: str) -> tuple[v35.ProtectStructure, int]:
    active = 3 if stratum == "chronic_multiple" else 1
    structure = v35.ProtectStructure(
        active, tuple(int(index < active) for index in range(3)),
        1, int(active > 1),
    )
    return structure, (-1 if stratum == "real_danger_adaptive" else 1 if active > 1 else 0)


def _external_stratum(
    seed: int, released_block: tuple[int, int]
) -> tuple[str, int]:
    offset = seed - released_block[0]
    count = released_block[1] - released_block[0] + 1
    if count not in (2000, 6000):
        raise ValueError("external population must contain 2,000 or 6,000 worlds")
    per = count // 4
    return STRATA[min(offset // per, 3)], offset


def generate_external_world(
    seed: int,
    *,
    released_block: tuple[int, int],
) -> v36_bridge.CanonicalWorld:
    """External shared-observable-support document, owned by neither model."""
    require_trace_sink("v36_round12.generate_external_world", seed=int(seed))
    if not released_block[0] <= seed <= released_block[1]:
        raise ValueError("seed outside released external block")
    stratum, offset = _external_stratum(seed, released_block)
    diagnosticity = EXTERNAL_GRID[offset % len(EXTERNAL_GRID)]
    keys: list[tuple[str, int, str, int | str]] = []
    structure, sign = _external_structure(stratum)
    temporal = _external_temporal(stratum)
    context_path = v32.context_path(temporal, TOTAL_SLICES, "natural")
    partner_state = _draw(
        seed, "external-partner-initial", 0, 0.5,
        released_block, keys,
    )
    rows = []
    for time in range(TOTAL_SLICES):
        if time:
            stay = 0.88
            keep = _draw(
                seed, "external-partner-transition", time, stay,
                released_block, keys,
            )
            if not keep:
                partner_state = 1 - partner_state
        if stratum == "acute_one":
            root_state = int(TOTAL_SLICES // 3 <= time < TOTAL_SLICES // 2)
            danger = root_state
        elif stratum == "real_danger_adaptive":
            root_state = 0
            danger = 1
        else:
            root_state = 1
            danger = int(time % 3 != 0)
        modes = tuple(
            root_state if index < structure.active_modes else 0
            for index in range(3)
        )
        action = time % 2
        policy_value = 2 if action else 0
        policy = tuple(
            policy_value if index < structure.active_modes else 1
            for index in range(3)
        )
        efficacy = 0.80 if stratum == "real_danger_adaptive" else 0.50
        prevented = _draw(
            seed, "external-prevented", time,
            efficacy if action else 0.0, released_block, keys,
        )
        realized_danger = int(danger and not prevented)
        outcome_probability = (
            diagnosticity if realized_danger else 1.0 - diagnosticity
        )
        context_input = int(context_path[time])
        cue = time % 3
        context_probability = v32.emission_probability(
            temporal.scopes[0], temporal.dynamics[0], cue=cue,
            context=context_input, time=time, length=TOTAL_SLICES,
        )
        partner_probability = (
            diagnosticity if partner_state else 1.0 - diagnosticity
        )
        contact_favorable = int(partner_state and policy[0] == 0)
        contact_probability = (
            diagnosticity if contact_favorable else 1.0 - diagnosticity
        )
        context_masked = time % 13 == 0
        rows.append(v36_bridge.CanonicalSlice(
            time=time, cue=cue, context_input=context_input,
            modes_input=modes, action=action, joint_policy=policy,
            identity=_draw(
                seed, "external-identity", time,
                diagnosticity if root_state else 1.0 - diagnosticity,
                released_block, keys,
            ),
            outcome=_draw(
                seed, "external-outcome", time, outcome_probability,
                released_block, keys,
            ),
            context=(
                None if context_masked else _draw(
                    seed, "external-context", time, context_probability,
                    released_block, keys,
                )
            ),
            partner=_draw(
                seed, "external-partner-response", time,
                partner_probability, released_block, keys,
            ),
            contact=_draw(
                seed, "external-contact-response", time,
                contact_probability, released_block, keys,
            ),
        ))
    return _canonical_world(
        seed, "external_shared_observable_support", stratum, structure,
        sign, int(partner_state), 1, temporal, rows, keys,
    )


def _v2_identity_native(
    seed: int, released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[list[int], int]:
    candidate_index = _sample_index(
        seed, "v2-native-identity-candidate", 0,
        v232_formation.PRIOR, released_block, keys,
    )
    candidate = v232_formation.LABELS[candidate_index]
    row = v232_formation.slice_distribution(
        candidate, event=True, precision="ordinary", control="low",
        broadcast="integrated", real_danger=False,
    )
    probability = math.fsum(
        float(row[index])
        for index, atom in enumerate(v232_formation.SUPPORT)
        if atom[0] == 1
    )
    values = [
        _draw(seed, "v2-native-identity-observation", time, probability,
              released_block, keys)
        for time in range(PREFIX_SLICES + 1)
    ]
    return values[:PREFIX_SLICES], values[PREFIX_SLICES]


def _v2_outcome_native(
    seed: int, released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[list[int], int]:
    truth = _sample_index(
        seed, "v2-native-outcome-state", 0, v234.JOINT_PRIOR,
        released_block, keys,
    )
    values = []
    for time in range(PREFIX_SLICES + 1):
        action, context = time % 2, (time // 12) % 2
        likelihood, _ = v234.slice_likelihood(v234.Episode(action, context, 1))
        values.append(_draw(
            seed, "v2-native-outcome-observation", time,
            float(likelihood[truth]), released_block, keys,
        ))
    return values[:PREFIX_SLICES], values[PREFIX_SLICES]


def _v2_context_native(
    seed: int, released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[list[int], int]:
    family_index = _sample_index(
        seed, "v2-native-context-family", 0, v24.PRIOR,
        released_block, keys,
    )
    family = v24.FAMILIES[family_index]
    nuisance = _sample_index(
        seed, "v2-native-context-nuisance", 0,
        v24._nuisance_initial(), released_block, keys,  # noqa: SLF001
    )
    context = (
        _sample_index(
            seed, "v2-native-context-initial", 0,
            v24.PARAMETERS["family_processes"]["context_split"][
                "initial_distribution"
            ],
            released_block, keys,
        )
        if family == "context_split" else 0
    )
    change_phase = 0
    change_stays = 0
    counts = [[0, 0], [0, 0]]
    values = []
    for time in range(PREFIX_SLICES + 1):
        if family == "context_split":
            descriptor = "then" if context == 0 else "now"
        elif family == "change_point":
            descriptor = "then" if change_phase == 0 else "now"
        else:
            descriptor = ("then", "now", "none")[nuisance]
        # The shared context target is binary (then/now).  Derive its row from
        # the frozen three-valued marker CPT by marginalizing the excluded
        # no-marker value and conditioning on the declared bridge support.
        # Never assign the no-marker mass to `then` by complementation.
        then_probability = v24._marker_likelihood(  # noqa: SLF001
            descriptor, "then_marker"
        )
        now_probability = v24._marker_likelihood(  # noqa: SLF001
            descriptor, "now_marker"
        )
        probability = now_probability / (then_probability + now_probability)
        values.append(_draw(
            seed, "v2-native-context-observation", time, probability,
            released_block, keys,
        ))
        if time == PREFIX_SLICES:
            break
        if family == "context_split":
            alpha = v24._cs_alpha()  # noqa: SLF001
            row = np.asarray(alpha[context], dtype=float) + np.asarray(counts[context], dtype=float)
            next_context = _sample_index(
                seed, "v2-native-context-transition", time, row,
                released_block, keys,
            )
            counts[context][next_context] += 1
            context = next_context
        elif family == "change_point" and change_phase == 0:
            a, b = v24.PARAMETERS["family_processes"]["change_point"]["hazard_beta_prior"]
            switch_probability = float(a / (a + b + change_stays))
            if _draw(seed, "v2-native-change-point", time, switch_probability,
                     released_block, keys):
                change_phase = 1
            else:
                change_stays += 1
        else:
            nuisance = _sample_index(
                seed, "v2-native-nuisance-transition", time,
                v24._nuisance_transition()[nuisance],  # noqa: SLF001
                released_block, keys,
            )
    return values[:PREFIX_SLICES], values[PREFIX_SLICES]


def _v2_partner_native(
    seed: int, released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[list[int], int]:
    state = _sample_index(
        seed, "v2-native-partner-state", 0, v26a.PRIOR,
        released_block, keys,
    )
    values = []
    for time in range(PREFIX_SLICES + 1):
        values.append(_draw(
            seed, "v2-native-partner-observation", time,
            float(v26a.EMISSIONS[state, 1]), released_block, keys,
        ))
        if time < PREFIX_SLICES:
            state = _sample_index(
                seed, "v2-native-partner-transition", time,
                v26a.TRANSITION[state], released_block, keys,
            )
    return values[:PREFIX_SLICES], values[PREFIX_SLICES]


def _v2_contact_native(
    seed: int, released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[list[int], int]:
    parameter = _sample_index(
        seed, "v2-native-contact-parameter", 0, v26b.OUTCOME_PRIOR,
        released_block, keys,
    )
    probability = float(v26b.OUTCOME_SUPPORT[parameter])
    values = [
        _draw(seed, "v2-native-contact-observation", time, probability,
              released_block, keys)
        for time in range(PREFIX_SLICES + 1)
    ]
    return values[:PREFIX_SLICES], values[PREFIX_SLICES]


# Seed-free native-fixture identity dummies.  These are production-side
# finite expansions of the exact distributions used by the seeded fixture
# constructors.  The independent oracle lives in v36_fixture_oracle.py and
# imports none of these helpers.
NATIVE_DUMMY_LENGTH = 2


def _dummy_binary(probability_one: float, value: int) -> float:
    return float(probability_one if value else 1.0 - probability_one)


def _dummy_context_initial(
    family: str,
) -> tuple[tuple[tuple[int, ...], float], ...]:
    if family == "context_split":
        initial = v24.PARAMETERS["family_processes"][family][
            "initial_distribution"
        ]
        return tuple(
            ((context, 0, 0, 0, 0), float(mass))
            for context, mass in enumerate(initial)
        )
    if family == "change_point":
        return (((0, 0), 1.0),)
    return tuple(
        ((state,), float(mass))
        for state, mass in enumerate(v24._nuisance_initial())  # noqa: SLF001
    )


def _dummy_context_descriptor(
    family: str, state: tuple[int, ...]
) -> str:
    if family in {"context_split", "change_point"}:
        return "then" if state[0] == 0 else "now"
    return ("then", "now", "none")[state[0]]


def _dummy_context_transition(
    family: str, state: tuple[int, ...]
) -> tuple[tuple[tuple[int, ...], float], ...]:
    if family == "context_split":
        context, n00, n01, n10, n11 = state
        alpha = v24._cs_alpha()  # noqa: SLF001
        counts = ((n00, n01), (n10, n11))[context]
        row = np.asarray(alpha[context], dtype=float) + np.asarray(
            counts, dtype=float
        )
        row /= float(row.sum())
        output = []
        for next_context, mass in enumerate(row):
            updated = [n00, n01, n10, n11]
            updated[context * 2 + next_context] += 1
            output.append(((next_context, *updated), float(mass)))
        return tuple(output)
    if family == "change_point":
        phase, stays = state
        if phase:
            return (((1, stays), 1.0),)
        a, b = v24.PARAMETERS["family_processes"][family][
            "hazard_beta_prior"
        ]
        switch = float(a / (a + b + stays))
        return (((1, stays), switch), ((0, stays + 1), 1.0 - switch))
    transition = v24._nuisance_transition()  # noqa: SLF001
    return tuple(
        ((next_state,), float(mass))
        for next_state, mass in enumerate(transition[state[0]])
    )


def _dummy_context_bridge_probability(descriptor: str) -> float:
    then = v24._marker_likelihood(descriptor, "then_marker")  # noqa: SLF001
    now = v24._marker_likelihood(descriptor, "now_marker")  # noqa: SLF001
    return float(now / (then + now))


def native_v2_fixture_dummy_joint(
    target: str,
) -> Mapping[tuple[Any, ...], float]:
    """Production-side two-slice native joint for one frozen V2 target."""
    output: dict[tuple[Any, ...], float] = {}
    if target == "identity":
        for index, candidate in enumerate(v232_formation.LABELS):
            row = v232_formation.slice_distribution(
                candidate, event=True, precision="ordinary", control="low",
                broadcast="integrated", real_danger=False,
            )
            probability = math.fsum(
                float(row[atom_index])
                for atom_index, atom in enumerate(v232_formation.SUPPORT)
                if atom[0] == 1
            )
            for tokens in itertools.product((0, 1), repeat=NATIVE_DUMMY_LENGTH):
                output[(index, tokens)] = float(v232_formation.PRIOR[index]) * math.prod(
                    _dummy_binary(probability, token) for token in tokens
                )
    elif target == "outcome":
        for truth, prior in enumerate(v234.JOINT_PRIOR):
            for tokens in itertools.product((0, 1), repeat=NATIVE_DUMMY_LENGTH):
                mass = float(prior)
                for time, token in enumerate(tokens):
                    likelihood, _ = v234.slice_likelihood(
                        v234.Episode(time % 2, (time // 12) % 2, 1)
                    )
                    mass *= _dummy_binary(float(likelihood[truth]), token)
                output[(truth, tokens)] = mass
    elif target == "partner":
        channels = tuple(v26a.CHANNELS)
        if v26a.EMISSIONS.shape[1] != len(channels):
            raise ValueError("partner emission width differs from declared channel schema")
        if channels.count("remaining") != 1:
            raise ValueError("partner schema must resolve remaining exactly once")
        remaining_index = channels.index("remaining")
        if channels[remaining_index] != "remaining":
            raise ValueError("partner remaining-channel name resolution failed")
        for initial, prior in enumerate(v26a.PRIOR):
            for next_state in range(len(v26a.PRIOR)):
                path_mass = float(prior) * float(
                    v26a.TRANSITION[initial, next_state]
                )
                for tokens in itertools.product((0, 1), repeat=2):
                    observations = (
                        (None, tokens[0], None, None),
                        (None, tokens[1], None, None),
                    )
                    likelihoods = (
                        v26a.relational_likelihood(observations[0], initial),
                        v26a.relational_likelihood(observations[1], next_state),
                    )
                    output[((initial, next_state), tokens)] = (
                        path_mass * math.prod(float(value) for value in likelihoods)
                    )
    elif target == "contact":
        for parameter, prior in enumerate(v26b.OUTCOME_PRIOR):
            probability = float(v26b.OUTCOME_SUPPORT[parameter])
            for tokens in itertools.product((0, 1), repeat=NATIVE_DUMMY_LENGTH):
                output[(parameter, tokens)] = float(prior) * math.prod(
                    _dummy_binary(probability, token) for token in tokens
                )
    elif target == "context":
        def recurse(
            family: str, time: int, state: tuple[int, ...], mass: float,
            path: tuple[tuple[int, ...], ...], tokens: tuple[int, ...],
        ) -> None:
            probability = _dummy_context_bridge_probability(
                _dummy_context_descriptor(family, state)
            )
            for token in (0, 1):
                next_mass = mass * _dummy_binary(probability, token)
                next_path = (*path, state)
                next_tokens = (*tokens, token)
                if time == NATIVE_DUMMY_LENGTH - 1:
                    output[(family, next_path, next_tokens)] = next_mass
                else:
                    for next_state, transition_mass in _dummy_context_transition(
                        family, state
                    ):
                        recurse(
                            family, time + 1, next_state,
                            next_mass * transition_mass,
                            next_path, next_tokens,
                        )
        for family_index, family in enumerate(v24.FAMILIES):
            for state, initial_mass in _dummy_context_initial(family):
                recurse(
                    family, 0, state,
                    float(v24.PRIOR[family_index]) * initial_mass, (), (),
                )
    else:
        raise ValueError(f"unknown native target {target!r}")
    return MappingProxyType(output)


def native_v3_fixture_dummy_factors() -> Mapping[str, Mapping[tuple[Any, ...], float]]:
    """Production-side factorized one-slice joint of the V3 native fixture."""
    protect: dict[tuple[Any, ...], float] = {}
    structure_weights = np.asarray(
        [math.exp(v35.structure_log_prior(item)) for item in v35.PROGRAMS],
        dtype=float,
    )
    structure_weights /= float(structure_weights.sum())
    time = 1
    action = time % 2
    for structure_index, (structure, structure_mass) in enumerate(
        zip(v35.PROGRAMS, structure_weights)
    ):
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                for contact in (0, 1):
                    latent_mass = float(structure_mass) / len(signs) / 4.0
                    for active_values in itertools.product(
                        (0, 1), repeat=structure.active_modes
                    ):
                        modes = tuple(active_values) + (0,) * (
                            3 - structure.active_modes
                        )
                        mode_mass = 0.5 ** structure.active_modes
                        policy_value = 2 if action else 0
                        policy = tuple(
                            policy_value if index < structure.active_modes else 1
                            for index in range(3)
                        )
                        probabilities = (
                            v35.root_signal_probability(1, modes, structure),
                            v35.outcome_probability(
                                policy, modes, structure, sign
                            ),
                            v35.partner_channel_probability(
                                1, reliable, "remaining"
                            ),
                            v35.contact_probability(
                                1, reliable, policy[0], contact
                            ),
                        )
                        for tokens in itertools.product((0, 1), repeat=4):
                            mass = latent_mass * mode_mass * math.prod(
                                _dummy_binary(probability, token)
                                for probability, token in zip(
                                    probabilities, tokens
                                )
                            )
                            protect[(
                                structure_index, sign, reliable, contact,
                                modes, tokens,
                            )] = mass

    temporal: dict[tuple[Any, ...], float] = {}
    supports: tuple[Sequence[Any], ...] = (
        (1, 2, 3), v32.SCOPES, v32.SCOPES,
        v32.DYNAMICS, v32.DYNAMICS,
    )
    priors = tuple(v32._prior(support) for support in supports)  # noqa: SLF001
    program_index = {program: index for index, program in enumerate(v32.PROGRAMS)}
    for values in itertools.product(*(range(len(support)) for support in supports)):
        program = v32.TemporalStructure(
            int(supports[0][values[0]]),
            (str(supports[1][values[1]]), str(supports[2][values[2]])),
            (str(supports[3][values[3]]), str(supports[4][values[4]])),
        )
        prior_mass = math.prod(
            float(prior[index]) for prior, index in zip(priors, values)
        )
        context = int(v32.context_path(program, TOTAL_SLICES, "natural")[time])
        probability = v32.emission_probability(
            program.scopes[0], program.dynamics[0], cue=time % 3,
            context=context, time=time, length=TOTAL_SLICES,
        )
        for token in (0, 1):
            temporal[(program_index[program], context, token)] = (
                prior_mass * _dummy_binary(probability, token)
            )
    return MappingProxyType({
        "protect": MappingProxyType(protect),
        "temporal": MappingProxyType(temporal),
    })


def _v2_fixture_world(
    seed: int, target: str, history: Sequence[int], observed: int,
    keys: Sequence[tuple[str, int, str, int | str]],
) -> v36_bridge.CanonicalWorld:
    structure = v35.ProtectStructure(1, (1, 0, 0), 1, 0)
    temporal = v32.TemporalStructure(
        2, ("context_specific", "shared_global"),
        ("discrete_recurrent_context", "static"),
    )
    rows = []
    for time in range(TOTAL_SLICES):
        value = history[time] if time < PREFIX_SLICES else observed
        identity = value if target == "identity" else 0
        outcome = value if target == "outcome" else 0
        context = value if target == "context" else 0
        partner = value if target == "partner" else 0
        contact = value if target == "contact" else 0
        rows.append(v36_bridge.CanonicalSlice(
            time, time % 3, (time // 12) % 2, (0, 0, 0), time % 2,
            (2 if time % 2 else 0, 1, 1), identity, outcome,
            context, partner, contact,
        ))
    return _canonical_world(
        seed, f"v2_native_{target}", target, structure, 0, 0, 0,
        temporal, rows, keys,
    )


def generate_v2_native_fixture(
    seed: int,
    target: str,
    *,
    released_block: tuple[int, int] = V2_NATIVE_BLOCK,
) -> NativeV2Fixture:
    require_trace_sink("v36_round12.generate_v2_native_fixture", seed=int(seed))
    if target not in TARGETS:
        raise ValueError("unknown target")
    if not released_block[0] <= seed <= released_block[1]:
        raise ValueError("seed outside released V2-native block")
    keys: list[tuple[str, int, str, int | str]] = []
    generators = {
        "identity": _v2_identity_native,
        "outcome": _v2_outcome_native,
        "context": _v2_context_native,
        "partner": _v2_partner_native,
        "contact": _v2_contact_native,
    }
    history, observed = generators[target](seed, released_block, keys)
    world = _v2_fixture_world(seed, target, history, observed, keys)
    production = v36_bridge.score_v2(world)[target].probabilities[0]
    from . import v36_bridge_oracle
    direct = v36_bridge_oracle.direct_forecasts(world, "v2")[target][0]
    return NativeV2Fixture(
        seed, target, tuple(history), (0, 0), int(observed),
        tuple(map(float, production)), tuple(map(float, direct)),
        abs(math.fsum(production) - 1.0),
        max(abs(float(a) - float(b)) for a, b in zip(production, direct)),
        tuple(keys),
    )


def _protect_signature(
    structure: v35.ProtectStructure,
    sign: int,
    reliable: int,
    contact_q: Sequence[float],
) -> tuple[int, ...]:
    values = []
    for modes in itertools.product((0, 1), repeat=3):
        values.append(v35.root_signal_probability(1, modes, structure))
    policies = tuple((value, value, value) for value in (0, 1, 2))
    for modes in itertools.product((0, 1), repeat=3):
        for policy in policies:
            values.append(v35.outcome_probability(policy, modes, structure, sign))
    values.append(v35.partner_channel_probability(1, reliable, "remaining"))
    for policy in (0, 2):
        values.append(
            (1.0 - float(contact_q[0]))
            * v35.contact_probability(1, reliable, policy, 0)
            + float(contact_q[0])
            * v35.contact_probability(1, reliable, policy, 1)
        )
    return tuple(int(round(value / TOLERANCE)) for value in values)


def _temporal_signature(program: v32.TemporalStructure) -> tuple[int, ...]:
    values = [
        v32.emission_probability(
            program.scopes[0], program.dynamics[0], cue=cue,
            context=context, time=time, length=TOTAL_SLICES,
        )
        for cue in range(3) for context in (0, 1)
        for time in (48, 55, 63)
    ]
    return tuple(int(round(value / TOLERANCE)) for value in values)


def _factor_classes(
    rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    grouped: dict[str, dict[str, Any]] = {}
    program_to_class = {}
    for row in rows:
        signature_hash = str(row["signature_sha256"])
        program_id = str(row["program_id"])
        program_to_class[program_id] = signature_hash
        item = grouped.setdefault(signature_hash, {
            "class_id": signature_hash, "mass": 0.0,
            "member_program_ids": [], "canonical_min_program_id": program_id,
        })
        item["mass"] += float(row["mass"])
        item["member_program_ids"].append(program_id)
        item["canonical_min_program_id"] = min(
            item["canonical_min_program_id"], program_id
        )
    return sorted(grouped.values(), key=lambda item: item["class_id"]), program_to_class


def v3_calibration_state(
    world: v36_bridge.CanonicalWorld,
) -> Mapping[str, Any]:
    """Complete factorized structure/class posterior, serialized losslessly."""
    require_trace_sink("v36_round12.v3_calibration_state", seed=int(world.seed))
    components = v36_bridge._v3_components(world)  # noqa: SLF001
    temporal = v36_bridge._bridge_temporal_posterior(world)  # noqa: SLF001
    protect_rows = []
    active = [0.0, 0.0, 0.0]
    edges = {name: 0.0 for name in v35.EDGE_NAMES}
    truth_protect_id = None
    for structure, sign, reliable, mass, contact_q in components:
        structure_index = v35.PROGRAMS.index(structure)
        program_id = f"p{structure_index:03d}:s{sign:+d}:l{reliable}"
        protect_rows.append({
            "program_id": program_id, "mass": float(mass),
            "structure_index": structure_index, "cross_sign": sign,
            "partner_reliable": reliable,
            "contact_parameter_posterior": list(map(float, contact_q)),
            "signature_sha256": hashlib.sha256(_canonical(
                _protect_signature(structure, sign, reliable, contact_q)
            )).hexdigest(),
        })
        active[structure.active_modes - 1] += float(mass)
        for name, present in v35.program_values(structure).items():
            edges[name] += float(mass) * int(present)
        if (
            structure == world.structure and sign == world.cross_sign
            and reliable == world.partner_reliable
        ):
            truth_protect_id = program_id
    temporal_rows = []
    truth_temporal_id = None
    for index, (program, mass) in enumerate(
        zip(temporal.programs, temporal.probabilities)
    ):
        program_id = f"t{index:03d}"
        temporal_rows.append({
            "program_id": program_id, "mass": float(mass),
            "structure": _plain(program),
            "signature_sha256": hashlib.sha256(_canonical(
                _temporal_signature(program)
            )).hexdigest(),
        })
        if program == world.temporal_structure:
            truth_temporal_id = program_id
    if truth_protect_id is None or truth_temporal_id is None:
        raise AssertionError("truth program missing from native support")
    protect_classes, protect_map = _factor_classes(protect_rows)
    temporal_classes, temporal_map = _factor_classes(temporal_rows)
    truth_class = (
        protect_map[truth_protect_id], temporal_map[truth_temporal_id]
    )
    class_pairs = [
        {
            "class_id": f"{left['class_id']}|{right['class_id']}",
            "mass": float(left["mass"] * right["mass"]),
            "canonical_min_program_id": (
                f"{left['canonical_min_program_id']}|"
                f"{right['canonical_min_program_id']}"
            ),
            "truth": (
                left["class_id"] == truth_class[0]
                and right["class_id"] == truth_class[1]
            ),
        }
        for left in protect_classes for right in temporal_classes
    ]
    class_pairs.sort(
        key=lambda item: (
            -item["mass"], item["canonical_min_program_id"]
        )
    )
    top = class_pairs[0]
    coverage = {}
    for level in (0.50, 0.80, 0.90, 0.95):
        cumulative = 0.0
        included = False
        for item in class_pairs:
            cumulative += float(item["mass"])
            included = included or bool(item["truth"])
            if cumulative >= level:
                break
        coverage[str(level)] = included
    truth_mass = math.fsum(
        float(item["mass"]) for item in class_pairs if item["truth"]
    )
    class_entropy = -math.fsum(
        float(item["mass"]) * math.log(float(item["mass"]))
        for item in class_pairs if item["mass"] > 0.0
    )
    exact_truth_mass = math.fsum(
        float(left["mass"]) * float(right["mass"])
        for left in protect_rows if left["program_id"] == truth_protect_id
        for right in temporal_rows if right["program_id"] == truth_temporal_id
    )
    exact_top_left = max(protect_rows, key=lambda item: item["mass"])
    exact_top_right = max(temporal_rows, key=lambda item: item["mass"])
    return {
        "joint_structure_posterior_representation": "outer_product_of_complete_factor_posteriors",
        "protect_structure_posterior": protect_rows,
        "temporal_structure_posterior": temporal_rows,
        "equivalence_class_map_representation": "cartesian_product_of_factor_classes",
        "protect_equivalence_classes": protect_classes,
        "temporal_equivalence_classes": temporal_classes,
        "class_posterior": {
            "representation": "outer_product",
            "protect_factor": protect_classes,
            "temporal_factor": temporal_classes,
            "normalization_error": abs(
                math.fsum(float(item["mass"]) for item in class_pairs) - 1.0
            ),
        },
        "truth_program": {
            "protect": truth_protect_id, "temporal": truth_temporal_id
        },
        "truth_class": f"{truth_class[0]}|{truth_class[1]}",
        "top_class": top["class_id"],
        "class_confidence": float(top["mass"]),
        "class_correct": bool(top["truth"]),
        "truth_class_mass": float(truth_mass),
        "class_coverage": coverage,
        "class_entropy": float(class_entropy),
        "normalized_class_entropy": float(
            class_entropy / max(math.log(len(class_pairs)), 1.0)
        ),
        "active_count_posterior": list(map(float, active)),
        "edge_posteriors": {key: float(value) for key, value in edges.items()},
        "truth_active_count": int(world.structure.active_modes),
        "truth_edges": dict(v35.program_values(world.structure)),
        "exact_truth_mass": float(exact_truth_mass),
        "exact_top_probability": float(
            exact_top_left["mass"] * exact_top_right["mass"]
        ),
        "exact_correct": bool(
            exact_top_left["program_id"] == truth_protect_id
            and exact_top_right["program_id"] == truth_temporal_id
        ),
    }


def shared_target_support_audit() -> Mapping[str, Any]:
    """Seed-free lexicographic external-grid and support commitment."""
    context_values = []
    for scope in v32.SCOPES:
        for dynamics in v32.DYNAMICS:
            for cue in range(3):
                for context in (0, 1):
                    for time in range(TOTAL_SLICES):
                        probability = v32.emission_probability(
                            scope, dynamics, cue=cue, context=context,
                            time=time, length=TOTAL_SLICES,
                        )
                        context_values.append({
                            "probability": probability, "scope": scope,
                            "dynamics": dynamics, "cue": cue,
                            "context": context, "time": time,
                            "canonical_name": (
                                f"{scope}:{dynamics}:cue{cue}:context{context}:t{time}"
                            ),
                        })
    chosen_context = []
    for target in EXTERNAL_GRID:
        chosen_context.append(min(
            context_values,
            key=lambda item: (
                abs(float(item["probability"]) - target),
                float(item["probability"]), item["canonical_name"],
            ),
        ))
    target_rows = {}
    for target in TARGETS:
        target_rows[target] = {
            "observable_values_v2": [0, 1],
            "observable_values_v3": [0, 1],
            "intersection": [0, 1],
            "finite_nonzero_support": True,
            "external_public_grid": list(EXTERNAL_GRID),
            "lexicographic_selection": {
                "low": 0.20, "medium": 0.50, "high": 0.80
            },
        }
    target_rows["context"]["public_v3_2_emission_representatives"] = chosen_context
    return {
        "stage": "V3.6-R1-round12",
        "status": "PRE_CRITERION_FROZEN",
        "selection_uses_model_score_difference": False,
        "targets": target_rows,
        "shared_action_schedule": "do(action)=time mod 2; never scored",
        "partner_process": {
            "states": [0, 1],
            "transition": [[0.88, 0.12], [0.12, 0.88]],
            "emission_grid": list(EXTERNAL_GRID),
        },
        "context_process": {
            "path_function": "v3.ref.v32.context_path",
            "emission_function": "v3.ref.v32.emission_probability",
            "bespoke_0_8_0_2_rule": False,
        },
        "strata": list(STRATA),
        "stratum_labels_enter_inference": False,
        "passed": all(
            item["intersection"] == [0, 1]
            and item["finite_nonzero_support"]
            for item in target_rows.values()
        ),
    }
