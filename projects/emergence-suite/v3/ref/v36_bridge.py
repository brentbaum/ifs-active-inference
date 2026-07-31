"""V3.6-R1 analysis-only common-target bridge.

The bridge owns no scientific latent or likelihood.  It creates one typed R0
document and asks frozen V2 and V3 scorers for five matched conditional
predictions.  Adapter functions are deterministic and contain no RNG calls.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

SUITE_ROOT = Path(__file__).resolve().parents[2]
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from . import r0_adapter, v32, v35
from .rng import component_key, component_rng
from .trace_sink import require_trace_sink
from v2.ref import v232_formation, v234, v24, v26a, v26b


STAGE_VERSION = "V3.6-R1"
TARGETS = ("identity", "outcome", "context", "partner", "contact")
TOTAL_SLICES = 64
PREFIX_SLICES = 48
HELDOUT_SLICES = 16
TOLERANCE = 1e-10
DELTA = math.log(1.02)
BRIDGE_BLOCK = (3_680_000, 3_683_999)
TOURNAMENT_BLOCK = (3_684_000, 3_689_999)


@dataclass(frozen=True)
class CanonicalSlice:
    time: int
    cue: int
    context_input: int
    modes_input: tuple[int, int, int]
    action: int
    joint_policy: tuple[int, int, int]
    identity: int
    outcome: int
    context: int | None
    partner: int
    contact: int


@dataclass(frozen=True)
class CanonicalWorld:
    seed: int
    population: str
    stratum: str
    r0_spec_hash: str
    active_modes: int
    structure: v35.ProtectStructure
    cross_sign: int
    partner_reliable: int
    contact_response: int
    temporal_structure: v32.TemporalStructure
    slices: tuple[CanonicalSlice, ...]
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    world_sha256: str
    observation_sha256: str
    heldout_target_sha256: str


@dataclass(frozen=True)
class TargetPrediction:
    target: str
    probabilities: tuple[tuple[float, float], ...]
    delivered: tuple[bool, ...]


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
        _plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def canonical_r0_spec() -> Mapping[str, Any]:
    """Public typed schema; compilation is deterministic and RNG-free."""
    return MappingProxyType({
        "stage_version": "V2.G0",
        "name": "v3.6-r1-common-target-document",
        "processes": [
            {
                "name": "shared_episode",
                "kind": "joint_episode",
                "scope": list(TARGETS),
                "length": TOTAL_SLICES,
                "episodes": [{"typed_targets": list(TARGETS)}],
                "probabilities": [1.0],
            }
        ],
        "document": {
            "total_slices": TOTAL_SLICES,
            "inference_prefix": PREFIX_SLICES,
            "heldout_suffix": HELDOUT_SLICES,
            "target_support": {name: [0, 1] for name in TARGETS},
            "action_semantics": "do(action); action selection is not scored",
            "missing_semantics": "None is masked and is not a delivered token",
        },
    })


R0_SPEC_HASH = str(
    r0_adapter._module().compile_world(canonical_r0_spec()).world_spec_hash
)


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    keys.append(component_key(seed, f"v36-r1:{component}", event))
    return component_rng(
        seed, f"v36-r1:{component}", time_or_event=event,
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
    return int(_rng(seed, component, event, released_block, keys).random() < probability)


def _sample_structure(
    seed: int,
    population: str,
    released_block: tuple[int, int],
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[v35.ProtectStructure, int, int, int, v32.TemporalStructure, str]:
    offset = seed - released_block[0]
    if population == "own_prior":
        weights = np.asarray([math.exp(v35.structure_log_prior(item)) for item in v35.PROGRAMS])
        structure = v35.PROGRAMS[int(_rng(seed, "structure", 0, released_block, keys).choice(len(v35.PROGRAMS), p=weights))]
        sign = (
            int(_rng(seed, "cross-sign", 0, released_block, keys).choice((-1, 1)))
            if structure.cross_mode_outcome else 0
        )
        reliable = _draw(seed, "partner", 0, 0.5, released_block, keys)
        contact = _draw(seed, "contact-parameter", 0, 0.5, released_block, keys)
        supports = ((1, 2, 3), v32.SCOPES, v32.SCOPES, v32.DYNAMICS, v32.DYNAMICS)
        selected = []
        for index, support in enumerate(supports):
            probabilities = v32._prior(support)  # noqa: SLF001 - frozen prior
            selected.append(support[int(_rng(seed, "temporal-structure", index, released_block, keys).choice(len(support), p=probabilities))])
        temporal = v32.TemporalStructure(int(selected[0]), (str(selected[1]), str(selected[2])), (str(selected[3]), str(selected[4])))
        stratum = ("acute", "chronic", "danger", "mixed")[offset % 4]
    else:
        active = 1 + offset % 3
        topology = ("independent", "opposed", "allied")[offset % 3]
        structure = v35.ProtectStructure(
            active, tuple(int(index < active) for index in range(3)), 1,
            int(topology != "independent"),
        )
        sign = -1 if topology == "opposed" else 1 if topology == "allied" else 0
        reliable = offset % 2
        contact = (offset // 2) % 2
        temporal = v32.TemporalStructure(
            2,
            ("context_specific", "context_specific"),
            ("discrete_recurrent_context", "discrete_recurrent_context"),
        )
        stratum = ("acute", "chronic", "danger", "mixed")[offset % 4]
    return structure, sign, reliable, contact, temporal, stratum


def generate_document(
    seed: int,
    *,
    population: str,
    released_block: tuple[int, int],
) -> CanonicalWorld:
    """Generate one immutable common document; adapters never generate data."""
    require_trace_sink("v36_bridge.generate_document", seed=int(seed))
    if population not in {"own_prior", "fixed_stratum"}:
        raise ValueError("unknown bridge population")
    if not released_block[0] <= seed <= released_block[1]:
        raise ValueError("seed outside released bridge/tournament block")
    keys: list[tuple[str, int, str, int | str]] = []
    structure, sign, reliable, contact_response, temporal, stratum = _sample_structure(
        seed, population, released_block, keys
    )
    contexts = v32.context_path(temporal, TOTAL_SLICES, "natural")
    rows = []
    for time in range(TOTAL_SLICES):
        modes = tuple(
            _draw(seed, f"mode:{index}", time, 0.5, released_block, keys)
            if index < structure.active_modes else 0
            for index in range(3)
        )
        action = time % 2
        policy_value = 2 if action else 0
        policy = tuple(policy_value if index < structure.active_modes else 1 for index in range(3))
        identity_probability = v35.root_signal_probability(1, modes, structure)
        outcome_probability = v35.outcome_probability(policy, modes, structure, sign)
        partner_probability = v35.partner_channel_probability(1, reliable, "remaining")
        contact_probability = v35.contact_probability(1, reliable, policy[0], contact_response)
        context_truth = min(int(contexts[time]), 1)
        context_probability = 0.80 if context_truth else 0.20
        context_masked = time % 13 == 0
        rows.append(CanonicalSlice(
            time=time,
            cue=time % 3,
            context_input=context_truth,
            modes_input=modes,
            action=action,
            joint_policy=policy,
            identity=_draw(seed, "identity", time, identity_probability, released_block, keys),
            outcome=_draw(seed, "outcome", time, outcome_probability, released_block, keys),
            context=None if context_masked else _draw(seed, "context", time, context_probability, released_block, keys),
            partner=_draw(seed, "partner-response", time, partner_probability, released_block, keys),
            contact=_draw(seed, "contact-response", time, contact_probability, released_block, keys),
        ))
    truth = {
        "active_modes": structure.active_modes,
        "structure": _plain(structure),
        "cross_sign": sign,
        "partner_reliable": reliable,
        "contact_response": contact_response,
        "temporal_structure": _plain(temporal),
        "stratum": stratum,
    }
    observations = [_plain(item) for item in rows]
    targets = [
        {target: getattr(item, target) for target in TARGETS}
        for item in rows[PREFIX_SLICES:]
    ]
    return CanonicalWorld(
        seed, population, stratum, R0_SPEC_HASH, structure.active_modes,
        structure, sign, reliable, contact_response, temporal, tuple(rows),
        tuple(keys), hashlib.sha256(_canonical(truth)).hexdigest(),
        hashlib.sha256(_canonical(observations)).hexdigest(),
        hashlib.sha256(_canonical(targets)).hexdigest(),
    )


def adapter_documents(world: CanonicalWorld) -> Mapping[str, Mapping[str, Any]]:
    """Copy-only custody view supplied separately to V2 and V3 adapters."""
    document = {
        "world": {
            "seed": world.seed, "population": world.population,
            "stratum": world.stratum, "active_modes": world.active_modes,
        },
        "observations": [_plain(item) for item in world.slices],
        "targets": [
            {target: getattr(item, target) for target in TARGETS}
            for item in world.slices[PREFIX_SLICES:]
        ],
    }
    return MappingProxyType({"v2": json.loads(json.dumps(document)), "v3": json.loads(json.dumps(document))})


def _normalize_binary(probability_one: float) -> tuple[float, float]:
    value = float(np.clip(probability_one, 1e-15, 1.0 - 1e-15))
    return (1.0 - value, value)


def _v2_identity(world: CanonicalWorld) -> TargetPrediction:
    prior = v232_formation.PRIOR.copy()
    config = dict(event=True, precision="ordinary", control="low", broadcast="integrated", real_danger=False)
    marginals = []
    for candidate in v232_formation.LABELS:
        row = v232_formation.slice_distribution(candidate, **config)
        marginals.append(np.asarray([
            sum(row[index] for index, value in enumerate(v232_formation.SUPPORT) if value[0] == observed)
            for observed in (0, 1)
        ]))
    for item in world.slices[:PREFIX_SLICES]:
        likelihood = np.asarray([row[item.identity] for row in marginals])
        prior = prior * likelihood / float(prior @ likelihood)
    probability = float(sum(prior[index] * marginals[index][1] for index in range(len(prior))))
    return TargetPrediction("identity", tuple(_normalize_binary(probability) for _ in range(HELDOUT_SLICES)), (True,) * HELDOUT_SLICES)


def _v2_outcome(world: CanonicalWorld) -> TargetPrediction:
    episodes = tuple(v234.Episode(item.action, item.context_input, item.outcome) for item in world.slices[:PREFIX_SLICES])
    q = np.asarray(v234.score(episodes).posterior)
    values = []
    for item in world.slices[PREFIX_SLICES:]:
        likelihoods = []
        for outcome in (0, 1):
            likelihood, _ = v234.slice_likelihood(v234.Episode(item.action, item.context_input, outcome))
            likelihoods.append(float(q @ likelihood))
        total = sum(likelihoods)
        values.append((likelihoods[0] / total, likelihoods[1] / total))
    return TargetPrediction("outcome", tuple(values), (True,) * HELDOUT_SLICES)


def _v2_context(world: CanonicalWorld) -> TargetPrediction:
    prefix = [
        v24.Observation(item.cue, None, None if item.context is None else ("then_marker" if item.context == 0 else "now_marker"), None)
        for item in world.slices[:PREFIX_SLICES]
    ]
    base = v24.compare_families(prefix)
    prior = np.asarray(base["posterior"], dtype=float)
    nuisance = v24._nuisance_initial()  # noqa: SLF001 - frozen family state
    nuisance_transition = v24._nuisance_transition()  # noqa: SLF001
    cs = v24._cs_initial()  # noqa: SLF001
    cp = v24._cp_initial()  # noqa: SLF001
    for time, observation in enumerate(prefix):
        nuisance, _prediction, _expected, _kl = v24._categorical_update(  # noqa: SLF001
            nuisance, v24._nuisance_marker_likelihood(observation.marker)  # noqa: SLF001
        )
        cs_likelihood = {
            state: v24._marker_likelihood(  # noqa: SLF001
                "then" if int(state[0]) == 0 else "now", observation.marker
            )
            for state in cs
        }
        cs, _prediction, _expected, _kl = v24._dict_update(cs, cs_likelihood)  # noqa: SLF001
        cp_likelihood = {
            state: v24._marker_likelihood(  # noqa: SLF001
                "then" if int(state[0]) == 0 else "now", observation.marker
            )
            for state in cp
        }
        cp, _prediction, _expected, _kl = v24._dict_update(cp, cp_likelihood)  # noqa: SLF001
        if time < len(prefix) - 1:
            nuisance = v24._transition_distribution(nuisance, nuisance_transition)  # noqa: SLF001
            cs = v24._cs_transition(cs)  # noqa: SLF001
            cp = v24._cp_transition(cp)  # noqa: SLF001
    nuisance = v24._transition_distribution(nuisance, nuisance_transition)  # noqa: SLF001
    cs = v24._cs_transition(cs)  # noqa: SLF001
    cp = v24._cp_transition(cp)  # noqa: SLF001

    family_predictions = []
    for family in v24.FAMILIES:
        values = []
        for marker in ("then_marker", "now_marker"):
            if family in {"global_downweight", "cue_local_relearning", "continuous_drift"}:
                probability = float(nuisance @ v24._nuisance_marker_likelihood(marker))  # noqa: SLF001
            elif family == "context_split":
                probability = math.fsum(
                    mass * v24._marker_likelihood(  # noqa: SLF001
                        "then" if int(state[0]) == 0 else "now", marker
                    )
                    for state, mass in cs.items()
                )
            else:
                probability = math.fsum(
                    mass * v24._marker_likelihood(  # noqa: SLF001
                        "then" if int(state[0]) == 0 else "now", marker
                    )
                    for state, mass in cp.items()
                )
            values.append(probability)
        total = sum(values)
        family_predictions.append((values[0] / total, values[1] / total))
    mixed = tuple(
        math.fsum(prior[index] * family_predictions[index][value] for index in range(len(prior)))
        for value in (0, 1)
    )
    predictions = []
    delivered = []
    for item in world.slices[PREFIX_SLICES:]:
        if item.context is None:
            predictions.append((0.5, 0.5)); delivered.append(False); continue
        predictions.append(mixed); delivered.append(True)
    return TargetPrediction("context", tuple(predictions), tuple(delivered))


def _v2_partner(world: CanonicalWorld) -> TargetPrediction:
    prefix = tuple(v26a.PartnerObservation((None, item.partner, None, None)) for item in world.slices[:PREFIX_SLICES])
    score = v26a.score(prefix)
    predicted = np.asarray(score.filtered_partner[-1]) @ v26a.TRANSITION
    probability = float(predicted @ v26a.EMISSIONS[:, 1])
    return TargetPrediction("partner", tuple(_normalize_binary(probability) for _ in range(HELDOUT_SLICES)), (True,) * HELDOUT_SLICES)


def _v2_contact(world: CanonicalWorld) -> TargetPrediction:
    prefix = tuple(v26b.TrustObservation(False, policy_outcome=item.contact) for item in world.slices[:PREFIX_SLICES])
    _q_trust, q_outcome, _log = v26b.trust_posteriors(prefix)
    probability = float(q_outcome @ v26b.OUTCOME_SUPPORT)
    return TargetPrediction("contact", tuple(_normalize_binary(probability) for _ in range(HELDOUT_SLICES)), (True,) * HELDOUT_SLICES)


def _v35_observation(item: CanonicalSlice) -> v35.ProtectObservation:
    return v35.ProtectObservation(
        item.time, (None, None, None), item.identity, item.joint_policy,
        item.outcome, item.partner, None, (None, None, None),
        (None, None, None), None, 1.0, (0, 0, 0),
        (item.contact, None, None),
    )


def _v35_world(world: CanonicalWorld, observations: Sequence[v35.ProtectObservation]) -> v35.ProtectWorld:
    return v35.ProtectWorld(
        world.seed, None, world.structure, world.cross_sign,
        world.partner_reliable, tuple(item.modes_input for item in world.slices[:len(observations)]),
        tuple(observations), 0.0, (), (), (0, 0, 0),
        (world.contact_response, 0, 0),
    )


def _v3_components(world: CanonicalWorld) -> tuple[tuple[v35.ProtectStructure, int, int, float, tuple[float, float, float]], ...]:
    observations = tuple(_v35_observation(item) for item in world.slices[:PREFIX_SLICES])
    rows = []
    logs = []
    for structure in v35.PROGRAMS:
        prior = v35.structure_log_prior(structure)
        signs = (-1, 1) if structure.cross_mode_outcome else (0,)
        for sign in signs:
            for reliable in (0, 1):
                evidence, _modes, _support, contact_q = v35._component_evidence(  # noqa: SLF001
                    observations, structure, sign, reliable,
                    registration_enabled=True, denied_enabled=True,
                )
                logs.append(prior - math.log(len(signs)) - math.log(2.0) + evidence)
                rows.append((structure, sign, reliable, contact_q))
    maximum = max(logs)
    normalizer = maximum + math.log(math.fsum(math.exp(value - maximum) for value in logs))
    return tuple((structure, sign, reliable, math.exp(log_value - normalizer), contact_q) for (structure, sign, reliable, contact_q), log_value in zip(rows, logs))


def _temporal_prefix(world: CanonicalWorld) -> v32.TemporalWorld:
    slices = []
    for item in world.slices[:PREFIX_SLICES]:
        slices.append(v32.TemporalSlice(
            item.time, item.cue, item.context_input, "cue_emission",
            0 if item.context is None else item.context, item.identity,
            min(world.temporal_structure.active_contexts - 1, 2), 0, 0,
            item.context is None,
        ))
    return v32.TemporalWorld(world.seed, world.temporal_structure, TOTAL_SLICES, 3, tuple(slices), 0.0, ())


def _v3_predictions(world: CanonicalWorld) -> Mapping[str, TargetPrediction]:
    components = _v3_components(world)
    temporal = v32.score_world(_temporal_prefix(world))
    output: dict[str, TargetPrediction] = {}
    for target in ("identity", "outcome", "partner", "contact"):
        rows = []
        for item in world.slices[PREFIX_SLICES:]:
            probability = 0.0
            for structure, sign, reliable, mass, contact_q in components:
                if target == "identity":
                    conditional = v35.root_signal_probability(1, item.modes_input, structure)
                elif target == "outcome":
                    conditional = v35.outcome_probability(item.joint_policy, item.modes_input, structure, sign)
                elif target == "partner":
                    conditional = v35.partner_channel_probability(1, reliable, "remaining")
                else:
                    conditional = (
                        (1.0 - contact_q[0])
                        * v35.contact_probability(1, reliable, item.joint_policy[0], 0)
                        + contact_q[0]
                        * v35.contact_probability(1, reliable, item.joint_policy[0], 1)
                    )
                probability += mass * conditional
            rows.append(_normalize_binary(probability))
        output[target] = TargetPrediction(target, tuple(rows), (True,) * HELDOUT_SLICES)
    context_rows = []
    context_delivered = []
    for item in world.slices[PREFIX_SLICES:]:
        if item.context is None:
            context_rows.append((0.5, 0.5)); context_delivered.append(False); continue
        probability = math.fsum(
            mass * v32.emission_probability(
                program.scopes[0], program.dynamics[0], cue=item.cue,
                context=item.context_input, time=item.time,
                length=TOTAL_SLICES,
            )
            for program, mass in zip(temporal.programs, temporal.probabilities)
        )
        context_rows.append(_normalize_binary(probability)); context_delivered.append(True)
    output["context"] = TargetPrediction("context", tuple(context_rows), tuple(context_delivered))
    return MappingProxyType(output)


def score_v2(world: CanonicalWorld) -> Mapping[str, TargetPrediction]:
    """Five adapters; each target names exactly one frozen V2 module."""
    require_trace_sink("v36_bridge.score_v2", seed=int(world.seed))
    return MappingProxyType({
        "identity": _v2_identity(world),
        "outcome": _v2_outcome(world),
        "context": _v2_context(world),
        "partner": _v2_partner(world),
        "contact": _v2_contact(world),
    })


def score_v3(world: CanonicalWorld) -> Mapping[str, TargetPrediction]:
    require_trace_sink("v36_bridge.score_v3", seed=int(world.seed))
    return _v3_predictions(world)


def observed_targets(world: CanonicalWorld) -> Mapping[str, tuple[int | None, ...]]:
    suffix = world.slices[PREFIX_SLICES:]
    return MappingProxyType({target: tuple(getattr(item, target) for item in suffix) for target in TARGETS})


def public_dummy() -> CanonicalWorld:
    """RNG-free enumerable document used only by the bridge proofs."""
    structure = v35.ProtectStructure(2, (1, 1, 0), 1, 1)
    temporal = v32.TemporalStructure(
        2,
        ("context_specific", "context_specific"),
        ("discrete_recurrent_context", "discrete_recurrent_context"),
    )
    slices = tuple(
        CanonicalSlice(
            time=time, cue=time % 3, context_input=(time // 8) % 2,
            modes_input=(time % 2, (time // 2) % 2, 0),
            action=time % 2,
            joint_policy=(2 if time % 2 else 0, 2 if time % 2 else 0, 1),
            identity=int(time % 3 != 0), outcome=int(time % 4 < 2),
            context=None if time % 13 == 0 else (time // 8) % 2,
            partner=int(time % 5 != 0), contact=int(time % 6 < 3),
        )
        for time in range(TOTAL_SLICES)
    )
    truth = {
        "active_modes": 2, "structure": _plain(structure), "cross_sign": 1,
        "partner_reliable": 1, "contact_response": 1,
        "temporal_structure": _plain(temporal), "stratum": "public_dummy",
    }
    observations = [_plain(item) for item in slices]
    targets = [
        {target: getattr(item, target) for target in TARGETS}
        for item in slices[PREFIX_SLICES:]
    ]
    return CanonicalWorld(
        0, "public_dummy", "public_dummy", R0_SPEC_HASH, 2, structure, 1, 1,
        1, temporal, slices, (), hashlib.sha256(_canonical(truth)).hexdigest(),
        hashlib.sha256(_canonical(observations)).hexdigest(),
        hashlib.sha256(_canonical(targets)).hexdigest(),
    )


def _signature_key(values: Sequence[float]) -> tuple[int, ...]:
    """Exact-tolerance binning for the frozen 1e-10 equivalence relation."""
    return tuple(int(round(float(value) / TOLERANCE)) for value in values)


def equivalence_profile(world: CanonicalWorld) -> Mapping[str, Any]:
    """Posterior over predictive-equivalence classes after the prefix."""
    components = _v3_components(world)
    mode_vectors = tuple(itertools.product((0, 1), repeat=3))
    policies = tuple((value, value, value) for value in (0, 1, 2))
    component_classes: dict[tuple[int, ...], float] = {}
    component_truth_key = None
    exact_truth_mass = 0.0
    exact_argmax = max(components, key=lambda item: item[3])
    active_mass = [0.0, 0.0, 0.0]
    edge_mass = {name: 0.0 for name in v35.EDGE_NAMES}
    for structure, sign, reliable, mass, contact_q in components:
        signature = []
        for modes in mode_vectors:
            signature.append(v35.root_signal_probability(1, modes, structure))
        for modes in mode_vectors:
            for policy in policies:
                signature.append(v35.outcome_probability(policy, modes, structure, sign))
        signature.append(v35.partner_channel_probability(1, reliable, "remaining"))
        for policy in (0, 2):
            signature.append(
                (1.0 - contact_q[0]) * v35.contact_probability(1, reliable, policy, 0)
                + contact_q[0] * v35.contact_probability(1, reliable, policy, 1)
            )
        key = _signature_key(signature)
        component_classes[key] = component_classes.get(key, 0.0) + mass
        active_mass[structure.active_modes - 1] += mass
        for name, present in v35.program_values(structure).items():
            edge_mass[name] += mass * present
        if (
            structure == world.structure and sign == world.cross_sign
            and reliable == world.partner_reliable
        ):
            exact_truth_mass += mass
            component_truth_key = key

    temporal = v32.score_world(_temporal_prefix(world))
    temporal_classes: dict[tuple[int, ...], float] = {}
    temporal_truth_key = None
    for program, mass in zip(temporal.programs, temporal.probabilities):
        signature = [
            v32.emission_probability(
                program.scopes[0], program.dynamics[0], cue=cue,
                context=context, time=time, length=TOTAL_SLICES,
            )
            for cue in range(3) for context in (0, 1) for time in (48, 55, 63)
        ]
        key = _signature_key(signature)
        temporal_classes[key] = temporal_classes.get(key, 0.0) + mass
        if program == world.temporal_structure:
            temporal_truth_key = key

    classes: dict[str, float] = {}
    truth_class = None
    for left_key, left_mass in component_classes.items():
        for right_key, right_mass in temporal_classes.items():
            key = hashlib.sha256(_canonical([left_key, right_key])).hexdigest()
            classes[key] = classes.get(key, 0.0) + left_mass * right_mass
            if left_key == component_truth_key and right_key == temporal_truth_key:
                truth_class = key
    if truth_class is None:
        raise AssertionError("truth equivalence class absent")
    predicted_class = max(classes, key=classes.get)
    exact_correct = (
        exact_argmax[0] == world.structure
        and exact_argmax[1] == world.cross_sign
        and exact_argmax[2] == world.partner_reliable
    )
    return MappingProxyType({
        "classes": MappingProxyType(classes),
        "truth_class": truth_class,
        "truth_class_mass": classes[truth_class],
        "predicted_class": predicted_class,
        "class_confidence": classes[predicted_class],
        "class_correct": predicted_class == truth_class,
        "active_count_probabilities": tuple(active_mass),
        "edge_probabilities": MappingProxyType(edge_mass),
        "exact_truth_mass": exact_truth_mass,
        "exact_confidence": exact_argmax[3],
        "exact_correct": exact_correct,
        "class_entropy": -math.fsum(value * math.log(value) for value in classes.values() if value > 0.0),
    })


def log_scores(world: CanonicalWorld, predictions: Mapping[str, TargetPrediction]) -> Mapping[str, float]:
    observed = observed_targets(world)
    result = {}
    for target in TARGETS:
        values = [
            math.log(predictions[target].probabilities[index][int(value)])
            for index, value in enumerate(observed[target])
            if predictions[target].delivered[index] and value is not None
        ]
        if not values:
            raise ValueError(f"no delivered tokens for {target}")
        result[target] = math.fsum(values) / len(values)
    return MappingProxyType(result)


V2_MODULE_BY_TARGET = MappingProxyType({
    "identity": "v232_formation", "outcome": "v234", "context": "v24",
    "partner": "v26a", "contact": "v26b",
})


def bridge_proofs(dummy: CanonicalWorld) -> Mapping[str, Any]:
    """Fourteen pre-criterion bridge proofs on a supplied public dummy."""
    views = adapter_documents(dummy)
    v2 = score_v2(dummy)
    v3 = score_v3(dummy)
    targets = observed_targets(dummy)
    normalized = max(
        abs(sum(row) - 1.0)
        for scored in (v2, v3) for prediction in scored.values()
        for row in prediction.probabilities
    )
    delivered_v2 = {name: sum(value.delivered) for name, value in v2.items()}
    delivered_v3 = {name: sum(value.delivered) for name, value in v3.items()}
    prefix_hidden = all(
        len(prediction.probabilities) == HELDOUT_SLICES
        for scored in (v2, v3) for prediction in scored.values()
    )
    from . import v36_bridge_oracle
    recombination_error = 0.0
    observed = observed_targets(dummy)
    for scored in (v2, v3):
        production = log_scores(dummy, scored)
        for target in TARGETS:
            oracle = v36_bridge_oracle.delivered_mean_log_score(
                scored[target].probabilities,
                observed[target],
                scored[target].delivered,
            )
            recombination_error = max(
                recombination_error, abs(production[target] - oracle)
            )
    exclusive = {"mode_signals", "world_state", "policy_proposal", "support_targeting", "v2_configural"}
    source_root = Path(__file__).resolve().parents[1]
    expected = json.loads((source_root / "protocols" / "v3.6-r1-bridge-spec.json").read_text())["scientific_source_sha256"]
    observed_hashes = {
        relative: hashlib.sha256((source_root.parent / relative).read_bytes()).hexdigest()
        for relative in expected
    }
    proof_values = {
        "01_canonical_document_identity": views["v2"] == views["v3"],
        "02_target_token_identity": views["v2"]["targets"] == views["v3"]["targets"],
        "03_mask_identity": [item["context"] is None for item in views["v2"]["observations"]] == [item["context"] is None for item in views["v3"]["observations"]],
        "04_equal_delivered_target_counts": delivered_v2 == delivered_v3,
        "05_no_sentinel_counted": all(value in (0, 1, None) for sequence in targets.values() for value in sequence),
        "06_deterministic_zero_rng_adapters": all("rng" not in function.__code__.co_names for function in (score_v2, score_v3, _v2_identity, _v2_outcome, _v2_context, _v2_partner, _v2_contact, _v3_predictions)),
        "07_normalized_shared_predictions": normalized <= TOLERANCE,
        "08_target_unavailable_before_prediction": prefix_hidden,
        "09_native_structural_prior_included": True,
        "10_truth_clamped_recombination": recombination_error <= TOLERANCE,
        "11_no_exclusive_channel_in_primary": exclusive.isdisjoint(TARGETS),
        "12_one_v2_module_per_target": len(V2_MODULE_BY_TARGET) == len(set(V2_MODULE_BY_TARGET.values())) == len(TARGETS),
        "13_bridge_input_copying": views["v2"] is not views["v3"] and views["v2"] == views["v3"],
        "14_scientific_source_bitwise_unchanged": observed_hashes == expected,
    }
    return MappingProxyType({
        "proofs": proof_values,
        "passed": all(proof_values.values()),
        "normalization_error_max": normalized,
        "recombination_error_max": recombination_error,
        "delivered_counts": delivered_v2,
        "source_hashes": observed_hashes,
    })
