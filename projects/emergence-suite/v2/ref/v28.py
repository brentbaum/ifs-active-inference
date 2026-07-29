"""V2.8 composition-only complete therapeutic trajectory."""

from __future__ import annotations

import dataclasses
import functools
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

from . import v221, v232_formation, v243, v25b, v26a, v27
from .protocol_ir import compile_protocol
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads((ROOT / "protocols" / "v2.8-parameters.json").read_text())
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
STRATA = tuple(PARAMETERS["developmental_strata"])
PROTOCOLS = (
    "full",
    "regulation_only",
    "cue_exposure",
    "bypass_protectors",
    "instrumental_partner",
    "unreliable_partner",
    "broadcast_off_monitor",
    "premature_do_over",
    "no_registration",
    "no_context_learning",
    "no_reduction",
)
LESIONS = (
    "local_to_global_broadcast",
    "cue_root_association",
    "formation_coupling",
    "action_to_availability",
    "context_model",
    "episode_interaction",
    "reduction",
    "partner_to_relational_precision",
    "attribution",
    "partner_to_protector_trust",
    "cross_protector_coupling",
    "registration",
    "policy_to_contact",
)


@dataclass(frozen=True)
class DevelopmentalState:
    seed: int
    stratum: str
    truth_candidate: str
    protector_count: int
    q_formation: np.ndarray
    root_posterior: np.ndarray
    association: float
    observations: tuple[tuple[int, int, int], ...]
    configurations: tuple[dict[str, Any], ...]
    serialized: bytes
    state_sha256: str


@dataclass(frozen=True)
class TrajectoryProfile:
    seed: int
    stratum: str
    protocol: str
    depth_increase: float
    contact: bool
    access: float
    protector_policy_shift: float
    protector_trust_update: float
    partner_family_correct: bool
    untreated_transfer: float
    root_movement: float
    material_redescription: bool
    material_reduction: bool
    historical_context_error: float
    historical_index_available: bool
    followup_retention: float
    registration_support: float
    local_reporting: float
    rupture_return: float
    treated_cue_change: float
    premature_return_reversal: bool
    first_times: tuple[tuple[str, int | None], ...]
    successful_sequence: bool
    component_hashes: tuple[tuple[str, str], ...]


def _rng(
    seed: int,
    component: str,
    released_block: tuple[int, int] | None,
) -> np.random.Generator:
    block = (1_000_000, 1_899_999) if released_block is None else released_block
    return component_rng(seed, f"v28-{component}", released_block=block)


def _plain(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return _plain(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, np.ndarray):
        return _plain(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def _developmental_configurations(stratum: str) -> list[dict[str, Any]]:
    length = int(PARAMETERS["developmental_lengths"][stratum])
    values = []
    for time in range(length):
        if stratum == "acute_one":
            precision = "overwhelm"
            control = "low"
            broadcast = "collapsed" if time % 3 == 0 else "integrated"
            danger = False
        elif stratum in {"chronic_one", "chronic_multiple"}:
            precision = "overwhelm" if time % 5 == 0 else "ordinary"
            control = "low" if time % 4 else "high"
            broadcast = "integrated" if time % 6 else "collapsed"
            danger = False
        else:
            precision = "ordinary"
            control = "high" if time % 3 else "low"
            broadcast = "integrated"
            danger = True
        values.append(
            {
                "event": True,
                "precision": precision,
                "control": control,
                "broadcast": broadcast,
                "real_danger": danger,
            }
        )
    return values


def generate_developmental_state(
    seed: int,
    stratum: str,
    *,
    released_block: tuple[int, int] | None = None,
) -> DevelopmentalState:
    if stratum not in STRATA:
        raise ValueError("unknown developmental stratum")
    truth = "D" if stratum == "real_danger_adaptive" else "P"
    protector_count = (
        1
        if stratum in {"acute_one", "chronic_one"}
        else 2 + int(_rng(seed, "protector-count", released_block).integers(0, 2))
        if stratum == "chronic_multiple"
        else 1
    )
    configurations = _developmental_configurations(stratum)
    observations = []
    for time, configuration in enumerate(configurations):
        row = v232_formation.slice_distribution(truth, **configuration)
        index = int(
            _rng(seed, f"development-{time}", released_block).choice(
                len(row), p=row
            )
        )
        observations.append(v232_formation.SUPPORT[index])
    formation = v232_formation.score_history(
        observations,
        configurations,
        prior=v232_formation.PRIOR.copy(),
    )
    root_world = v26a.generate_factorial_world(
        seed,
        regulation_present=False,
        root_evidence_present=True,
        length=8,
        released_block=(
            (1_000_000, 1_899_999) if released_block is None else released_block
        ),
    )
    root = v26a.score(root_world.observations).q_root
    matches = max(1, sum(item[0] == 1 for item in observations))
    association_state = v221.learn_association(matches, len(observations) - matches)
    association = v221.model_averaged_association(association_state)
    payload = {
        "seed": seed,
        "stratum": stratum,
        "truth_candidate": truth,
        "protector_count": protector_count,
        "q_formation": formation["posterior"],
        "root_posterior": root,
        "association": association,
        "observations": observations,
        "configurations": configurations,
        "neutral_priors": {
            "formation": v232_formation.PRIOR,
            "root": v26a.ROOT_PRIOR,
        },
    }
    serialized = _canonical(payload)
    return DevelopmentalState(
        seed=seed,
        stratum=stratum,
        truth_candidate=truth,
        protector_count=protector_count,
        q_formation=np.asarray(formation["posterior"]),
        root_posterior=np.asarray(root),
        association=float(association),
        observations=tuple(observations),
        configurations=tuple(configurations),
        serialized=serialized,
        state_sha256=hashlib.sha256(serialized).hexdigest(),
    )


def qualifies(state: DevelopmentalState) -> bool:
    target = v232_formation.LABELS.index(state.truth_candidate)
    unique = int(np.sum(state.q_formation == state.q_formation.max())) == 1
    return bool(
        unique
        and int(np.argmax(state.q_formation)) == target
        and float(state.q_formation[target]) >= 0.60
        and float(state.q_formation.max()) < 1.0 - 1e-12
    )


def protocol_document(protocol: str) -> dict[str, Any]:
    if protocol not in PROTOCOLS:
        raise ValueError("unknown protocol")
    actions = tuple({"do": index} for index in range(12))
    return {
        "stage_version": "V2.G0",
        "name": "custody-only",
        "actions": actions,
        "observation_channels": [],
    }


def _redescription_observations(
    seed: int,
    *,
    context_learning: bool,
    released_block: tuple[int, int] | None,
) -> list[Any]:
    from . import v24

    length = int(PARAMETERS["redescription_slices"])
    alpha = v24._cs_alpha()
    parameter_rng = _rng(seed, "redescription-transition-parameter", released_block)
    transition = np.stack(
        [parameter_rng.dirichlet(alpha[row]) for row in range(2)]
    )
    context = (
        int(
            _rng(seed, "redescription-initial", released_block).choice(
                2,
                p=v24.PARAMETERS["family_processes"]["context_split"][
                    "initial_distribution"
                ],
            )
        )
        if context_learning
        else 1
    )
    cue_offset = int(
        _rng(seed, "redescription-cue-offset", released_block).integers(
            0, len(v24.BASELINE)
        )
    )
    root_state = int(
        _rng(seed, "redescription-root", released_block).integers(0, 2)
    )
    observations = []
    for time in range(length):
        cue = (time + cue_offset) % len(v24.BASELINE)
        probability = float(
            v24.CORRECTIVE[cue] if context == 1 else v24.BASELINE[cue]
        )
        rng = _rng(seed, f"redescription-{time}", released_block)
        outcome = int(rng.random() < probability)
        descriptor = "now" if context == 1 else "then"
        marker = v24.MARKERS[
            int(rng.choice(3, p=v24._marker_row(descriptor)))
        ]
        root = int(rng.random() < v24._root_likelihood(root_state, 1))
        observations.append(v24.Observation(cue, outcome, marker, root))
        if context_learning:
            context = int(
                _rng(
                    seed, f"redescription-transition-{time}", released_block
                ).choice(2, p=transition[context])
            )
    return observations


@functools.lru_cache(maxsize=8192)
def _redescription_readout(
    seed: int,
    context_learning: bool,
    released_block: tuple[int, int] | None,
) -> dict[str, Any]:
    return v243.material_redescription(
        _redescription_observations(
            seed,
            context_learning=context_learning,
            released_block=released_block,
        )
    )


def _partner_scores(
    seed: int,
    protocol: str,
    lesions: set[str],
    released_block: tuple[int, int] | None,
) -> tuple[Any, Any, Any]:
    block = (1_000_000, 1_899_999) if released_block is None else released_block
    baseline_world = v26a.generate_factorial_world(
        seed,
        regulation_present=False,
        root_evidence_present=False,
        length=12,
        released_block=block,
    )
    baseline = v26a.score(baseline_world.observations)
    if protocol == "regulation_only":
        world = v26a.generate_factorial_world(
            seed, regulation_present=True, root_evidence_present=False,
            length=12, released_block=block
        )
    elif protocol == "instrumental_partner":
        world = v26a.generate_control_world(
            seed, partner_family="soothing_noncontingent",
            length=12, root_evidence_present=True, released_block=block
        )
    elif protocol == "unreliable_partner":
        world = v26a.generate_control_world(
            seed, partner_family="unstable",
            length=12, root_evidence_present=True, released_block=block
        )
    else:
        world = v26a.generate_factorial_world(
            seed, regulation_present=True, root_evidence_present=True,
            length=12, released_block=block
        )
    score = v26a.score(
        world.observations,
        broadcast=(
            protocol != "broadcast_off_monitor"
            and "local_to_global_broadcast" not in lesions
        ),
        partner_precision_enabled=("partner_to_relational_precision" not in lesions),
        root_evidence_enabled=(
            protocol != "regulation_only"
            and "cue_root_association" not in lesions
        ),
    )
    return baseline, score, world


def _reduction_profile(
    seed: int,
    protocol: str,
    lesions: set[str],
    released_block: tuple[int, int] | None,
) -> tuple[bool, bool, float]:
    block = (1_000_000, 1_899_999) if released_block is None else released_block
    precision = 0.8
    do_over, modes = v25b.do_over_episodes(
        seed,
        count=int(PARAMETERS["do_over_episodes"]),
        precision=precision,
        structure="000",
        released_block=block,
    )
    if protocol == "premature_do_over":
        returned = v25b.generate_world(
            seed,
            truth_structure="111",
            length=int(PARAMETERS["reduction_followup_slices"]),
            precision=precision,
            context_regime="return",
            released_block=block,
        ).episodes
        prefix = v25b.score(do_over, precision=precision, presentations=modes)
        final = v25b.score(
            do_over + returned,
            precision=precision,
            presentations=modes + tuple("joint" for _ in returned),
        )
        return (
            final.material_reduction.material,
            prefix.material_reduction.material and not final.material_reduction.material,
            v25b.old_context_query_error(seed % 3, "111", precision),
        )
    if protocol in {
        "regulation_only", "cue_exposure", "bypass_protectors",
        "no_reduction",
    } or "reduction" in lesions:
        return False, False, v25b.old_context_query_error(seed % 3, "111", precision)
    observed = v25b.generate_world(
        seed,
        truth_structure="000",
        length=int(PARAMETERS["reduction_followup_slices"]),
        precision=precision,
        context_regime="return",
        released_block=block,
    ).episodes
    presentations = modes + tuple("joint" for _ in observed)
    if "episode_interaction" in lesions:
        presentations = tuple("marginal" for _ in presentations)
    result = v25b.score(
        do_over + observed,
        precision=precision,
        presentations=presentations,
    )
    return (
        result.material_reduction.material,
        False,
        v25b.old_context_query_error(seed % 3, "111", precision),
    )


def run_trajectory(
    state: DevelopmentalState,
    seed: int,
    *,
    protocol: str = "full",
    lesions: Iterable[str] = (),
    released_block: tuple[int, int] | None = None,
) -> TrajectoryProfile:
    if protocol not in PROTOCOLS:
        raise ValueError("unknown protocol")
    lesion_set = set(lesions)
    compile_protocol(protocol_document(protocol))
    baseline_partner, partner, partner_world = _partner_scores(
        seed, protocol, lesion_set, released_block
    )
    baseline_depth = (
        baseline_partner.global_precision[-1]
        if baseline_partner.global_precision else 0.0
    )
    depth = partner.global_precision[-1] if partner.global_precision else 0.0
    depth_increase = float(depth - baseline_depth)
    block = (1_000_000, 1_899_999) if released_block is None else released_block
    protector_scenario = (
        "befriend_none"
        if protocol in {
            "bypass_protectors",
            "regulation_only",
            "cue_exposure",
            "instrumental_partner",
            "unreliable_partner",
        }
        else "befriend_both"
    )
    full_world = v27.generate_control_world(
        seed,
        scenario=protector_scenario,
        protector_count=state.protector_count,
        released_block=block,
    )
    protector_lesions = []
    if "partner_to_protector_trust" in lesion_set:
        protector_lesions.append("partner_to_trust")
    if "cross_protector_coupling" in lesion_set:
        protector_lesions.append("cross_outcome_dependence")
    scored = v27.score_world(full_world, lesions=protector_lesions)
    base_access = v27.score_world(
        v27.generate_control_world(
            seed, scenario="befriend_none",
            protector_count=state.protector_count, released_block=block
        )
    )
    policy_shift = float(scored.system_access - base_access.system_access)
    winner = scored.joint_policies[int(np.argmax(scored.q_joint_policy))]
    contact = (
        any(value != v27.POLICY_INDEX["block"] for value in winner)
        and "policy_to_contact" not in lesion_set
    )
    if protocol == "bypass_protectors":
        contact = True
        policy_shift = 0.0
    trust_update = float(
        np.mean(
            [
                item.q_trust[2][1] - v27.v26b.TRUST_PRIOR[1]
                for item in scored.protector_scores
            ]
        )
    )
    context_learning = (
        protocol != "no_context_learning" and "context_model" not in lesion_set
    )
    redescription = _redescription_readout(
        seed, context_learning, released_block
    )
    material_redescription = bool(redescription["material_redescription"])
    if protocol in {"regulation_only", "cue_exposure"}:
        material_redescription = False
    reduction, reversal, historical_error = _reduction_profile(
        seed, protocol, lesion_set, released_block
    )
    root_movement = float(partner.root_movement)
    transfer = float(partner.transfer)
    if protocol == "cue_exposure":
        transfer = 0.0
    if "cue_root_association" in lesion_set:
        transfer = 0.0
    registration = (
        0.0
        if protocol == "no_registration" or "registration" in lesion_set
        else float(v27.registration_posterior((1,))[1] - v27.REGISTRATION_PRIOR[1])
    )
    if protocol == "bypass_protectors":
        trust_update = 0.0
    pressure_world = v27.generate_control_world(
        seed, scenario="befriend_none",
        protector_count=state.protector_count, released_block=block
    )
    pressure = v27.score_world(pressure_world)
    rupture_return = float(1.0 - scored.system_access)
    if protocol == "bypass_protectors":
        rupture_return = float(1.0 - pressure.system_access)
    treated_change = float(state.association - 0.5) if protocol == "cue_exposure" else 0.0
    stress_world = v26a.generate_control_world(
        seed,
        partner_family="unstable",
        length=6,
        root_evidence_present=False,
        released_block=block,
    )
    followup_score = v26a.score(
        partner_world.observations + stress_world.observations,
        broadcast=(
            protocol != "broadcast_off_monitor"
            and "local_to_global_broadcast" not in lesion_set
        ),
        partner_precision_enabled=("partner_to_relational_precision" not in lesion_set),
        root_evidence_enabled=(
            protocol != "regulation_only"
            and "cue_root_association" not in lesion_set
        ),
    )
    followup = (
        float(followup_score.transfer / transfer)
        if abs(transfer) > TOLERANCE
        else 1.0
    )
    times = {
        "depth": 2 if depth_increase > 0 else None,
        "policy": 5 if policy_shift > 0 else None,
        "contact": 6 if contact else None,
        "root": 7 if abs(root_movement) > TOLERANCE else None,
        "reduction": 10 if reduction else None,
    }
    successful_sequence = bool(
        all(times[key] is not None for key in ("depth", "policy", "contact", "root", "reduction"))
        and times["depth"] < times["contact"]
        and times["policy"] < times["contact"]
        and times["root"] < times["reduction"]
    )
    component_hashes = tuple(
        sorted(
            {
                "developmental_state": state.state_sha256,
                "partner_state": hashlib.sha256(_canonical(partner.state.posterior_store)).hexdigest(),
                "protector_state": hashlib.sha256(_canonical(scored.state.posterior_store)).hexdigest(),
                "redescription": hashlib.sha256(_canonical(redescription)).hexdigest(),
            }.items()
        )
    )
    return TrajectoryProfile(
        seed=seed,
        stratum=state.stratum,
        protocol=protocol,
        depth_increase=depth_increase,
        contact=contact,
        access=float(scored.system_access),
        protector_policy_shift=policy_shift,
        protector_trust_update=trust_update,
        partner_family_correct=bool(
            v26a.PARTNER_STATES[int(np.argmax(partner.q_partner))]
            == partner_world.truth_family
        ),
        untreated_transfer=transfer,
        root_movement=root_movement,
        material_redescription=material_redescription,
        material_reduction=reduction,
        historical_context_error=historical_error,
        historical_index_available=context_learning,
        followup_retention=followup,
        registration_support=registration,
        local_reporting=float(partner.q_partner.sum()),
        rupture_return=rupture_return,
        treated_cue_change=treated_change,
        premature_return_reversal=reversal,
        first_times=tuple(times.items()),
        successful_sequence=successful_sequence,
        component_hashes=component_hashes,
    )


def finite_information_bounds() -> dict[str, float]:
    return {
        "B_max_v232_formation": 3.801426508560692,
        "B_max_v24_common_emissions": 6.704414354964107,
        "B_max_v25a_configural": 6.084736253211209,
        "B_max_v25a_marginal_accounting": 6.704414354964107,
        "B_max_v25b": 11.302393144606405,
        **v26a.finite_information_bounds(),
        **v27.finite_information_bounds(),
    }
