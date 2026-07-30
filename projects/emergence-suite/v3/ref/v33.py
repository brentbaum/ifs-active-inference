"""V3.3 PRUNE: exact reverse movement over the V3.1 graph.

No reduction operation exists.  Historical, corrective, imaginal, neutral, and
return episodes enter one typed evidence interface.  The posterior always
ranges over the same programs and edge identities used by V3.1 GROW.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from . import v31
from .trace_sink import require_trace_sink


STAGE_VERSION = "V3.3"
DEVELOPMENT_BLOCK = (3_300_000, 3_329_999)
BURDEN_EDGES = ("M1_G", "G_W", "G_A", "G_Y")
EDGE_NAMES = v31.EDGE_NAMES
PROGRAMS = v31.PROGRAMS


@dataclass(frozen=True)
class ReductionConfig:
    corrective_evidence: str
    do_over: str
    adaptive_edge: str = "none"
    root_revision: bool = True
    return_burden: bool = False
    history_length: int = 48
    corrective_length: int = 36
    return_length: int = 12

    def __post_init__(self) -> None:
        if self.corrective_evidence not in {
            "configural",
            "suggestion_only",
            "none",
        }:
            raise ValueError("invalid corrective evidence")
        if self.do_over not in {"none", "premature", "post_revision"}:
            raise ValueError("invalid do-over")
        if self.adaptive_edge not in {"none", "W_Y"}:
            raise ValueError("invalid adaptive edge")
        if min(
            self.history_length,
            self.corrective_length,
            self.return_length,
        ) < 1:
            raise ValueError("episode lengths must be positive")


@dataclass(frozen=True)
class ReductionSlice:
    time: int
    context: int
    mode: int | None
    root: int | None
    world: int | None
    policy_proposal: int | None
    action: int | None
    outcome: int | None
    episode_kind: str


@dataclass(frozen=True)
class ReductionWorld:
    seed: int
    config: ReductionConfig | None
    historical_structure: Any
    current_truth_structure: Any
    slices: tuple[ReductionSlice, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class ContextPosterior:
    programs: tuple[Any, ...]
    probabilities: tuple[float, ...]
    log_evidence: float
    edge_probabilities: Mapping[str, float]
    active_mode_probability: float
    parameter_means: Mapping[str, tuple[float, ...]]

    def structure_probability(self, structure: Any) -> float:
        if structure not in self.programs:
            return 0.0
        return self.probabilities[self.programs.index(structure)]


@dataclass(frozen=True)
class ReductionPosterior:
    current: ContextPosterior
    historical: ContextPosterior
    burden_edge_mass: float
    root_revision: float
    old_graph_probability: float


@dataclass(frozen=True)
class MaterialReductionThresholds:
    mode_retained: float
    burden_edge_mass_max: float
    absent_present_bf_min: float
    stability_observations: int = 3
    neutral_tolerance: float = 1e-10


def formed_structure(*, adaptive_edge: str = "none") -> Any:
    return v31.make_structure(
        1,
        M1_G=1,
        G_W=1,
        G_A=1,
        G_Y=1,
        W_Y=int(adaptive_edge == "W_Y"),
        doA_Y=0,
    )


def reduced_structure(*, adaptive_edge: str = "none") -> Any:
    return v31.make_structure(
        1,
        M1_G=0,
        G_W=0,
        G_A=0,
        G_Y=0,
        W_Y=int(adaptive_edge == "W_Y"),
        doA_Y=0,
    )


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    if not block[0] <= int(seed) <= block[1]:
        raise ValueError("seed is outside the authorized V3.3 block")
    key = (STAGE_VERSION, int(seed), str(component), event)
    keys.append(key)
    digest = hashlib.sha256(repr(key).encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _bernoulli(
    seed: int,
    component: str,
    event: int,
    probability: float,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    return int(
        _rng(seed, component, event, released_block, keys).random()
        < probability
    )


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def _beta_score(rows: Sequence[tuple[int, int]], concentration: float) -> float:
    return math.fsum(
        _log_beta(zeros + concentration, ones + concentration)
        - _log_beta(concentration, concentration)
        for zeros, ones in rows
    )


def _context_slices(
    world: ReductionWorld, context: int
) -> tuple[ReductionSlice, ...]:
    return tuple(item for item in world.slices if item.context == context)


def _counts(
    slices: Sequence[ReductionSlice],
    child: str,
    parents: tuple[str, ...],
) -> tuple[tuple[int, int], ...]:
    counts = [[0, 0] for _ in range(1 << len(parents))]
    for item in slices:
        values = {
            "mode": item.mode,
            "root": item.root,
            "world": item.world,
            "policy": item.policy_proposal,
            "action": item.action,
            "outcome": item.outcome,
        }
        child_value = values[child]
        if child_value is None or any(values[parent] is None for parent in parents):
            continue
        row = 0
        for bit, parent in enumerate(parents):
            row |= int(values[parent]) << bit
        counts[row][int(child_value)] += 1
    return tuple((row[0], row[1]) for row in counts)


def _mode_score(
    slices: Sequence[ReductionSlice], active: int, concentration: float
) -> float:
    observed = [item.mode for item in slices if item.mode is not None]
    if active == 0:
        return 0.0 if not any(observed) else -math.inf
    return _beta_score(
        ((observed.count(0), observed.count(1)),), concentration
    )


def _program_log_joint(
    slices: Sequence[ReductionSlice],
    structure: Any,
    hyperparameters: v31.V31Hyperparameters,
) -> float:
    values = v31.program_values(structure)
    concentration = hyperparameters.concentration
    total = v31.structure_log_prior(structure, hyperparameters)
    total += _mode_score(slices, values["active_mode"], concentration)
    total += _beta_score(
        _counts(slices, "root", ("mode",) if values["M1_G"] else ()),
        concentration,
    )
    total += _beta_score(
        _counts(slices, "world", ("root",) if values["G_W"] else ()),
        concentration,
    )
    total += _beta_score(
        _counts(slices, "policy", ("root",) if values["G_A"] else ()),
        concentration,
    )
    parents = tuple(
        parent
        for edge, parent in (
            ("G_Y", "root"),
            ("W_Y", "world"),
            ("doA_Y", "action"),
        )
        if values[edge]
    )
    total += _beta_score(_counts(slices, "outcome", parents), concentration)
    return total


def _parameter_means(
    slices: Sequence[ReductionSlice],
    structure: Any,
    concentration: float,
) -> Mapping[str, tuple[float, ...]]:
    values = v31.program_values(structure)
    definitions = {
        "mode": ("mode", ()),
        "root": ("root", ("mode",) if values["M1_G"] else ()),
        "world": ("world", ("root",) if values["G_W"] else ()),
        "policy": ("policy", ("root",) if values["G_A"] else ()),
        "outcome": (
            "outcome",
            tuple(
                parent
                for edge, parent in (
                    ("G_Y", "root"),
                    ("W_Y", "world"),
                    ("doA_Y", "action"),
                )
                if values[edge]
            ),
        ),
    }
    result = {}
    for name, (child, parents) in definitions.items():
        rows = _counts(slices, child, parents)
        result[name] = tuple(
            (ones + concentration) / (zeros + ones + 2 * concentration)
            for zeros, ones in rows
        )
    return MappingProxyType(result)


def _score_context(
    slices: Sequence[ReductionSlice],
    hyperparameters: v31.V31Hyperparameters,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
) -> ContextPosterior:
    restrictions = {} if restrictions is None else dict(restrictions)
    programs = tuple(
        program
        for program in PROGRAMS
        if all(
            v31.program_values(program)[name] in allowed
            for name, allowed in restrictions.items()
        )
    )
    log_weights = tuple(
        _program_log_joint(slices, program, hyperparameters)
        for program in programs
    )
    maximum = max(log_weights)
    log_evidence = maximum + math.log(
        math.fsum(math.exp(value - maximum) for value in log_weights)
    )
    probabilities = tuple(
        math.exp(value - log_evidence) for value in log_weights
    )
    edges = {
        edge: math.fsum(
            probability
            for program, probability in zip(programs, probabilities)
            if v31.program_values(program)[edge]
        )
        for edge in EDGE_NAMES
    }
    active = math.fsum(
        probability
        for program, probability in zip(programs, probabilities)
        if v31.program_values(program)["active_mode"]
    )
    map_structure = programs[int(np.argmax(probabilities))]
    return ContextPosterior(
        programs,
        probabilities,
        float(log_evidence),
        MappingProxyType(edges),
        float(active),
        _parameter_means(
            slices, map_structure, hyperparameters.concentration
        ),
    )


def score_world(
    world: ReductionWorld,
    *,
    hyperparameters: v31.V31Hyperparameters = v31.DEFAULT_HYPERPARAMETERS,
    restrictions: Mapping[str, tuple[int, ...]] | None = None,
) -> ReductionPosterior:
    require_trace_sink("v33.score_world", seed=int(world.seed))
    if world.analysis_labels:
        raise ValueError("analysis labels may not reach V3.3 inference")
    current = _score_context(
        _context_slices(world, 1), hyperparameters, restrictions
    )
    historical = _score_context(
        _context_slices(world, 0), hyperparameters, restrictions
    )
    burden_mass = max(current.edge_probabilities[name] for name in BURDEN_EDGES)
    historical_root = historical.parameter_means["root"][0]
    current_root = current.parameter_means["root"][0]
    return ReductionPosterior(
        current,
        historical,
        float(burden_mass),
        float(historical_root - current_root),
        historical.structure_probability(world.historical_structure),
    )


def _sample_history_slice(
    seed: int,
    time: int,
    adaptive_edge: str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> ReductionSlice:
    mode = _bernoulli(seed, "history:mode", time, 0.5, released_block, keys)
    root = _bernoulli(
        seed,
        "history:root",
        time,
        0.9 if mode else 0.1,
        released_block,
        keys,
    )
    world = _bernoulli(
        seed,
        "history:world",
        time,
        0.9 if root else 0.1,
        released_block,
        keys,
    )
    policy = _bernoulli(
        seed,
        "history:policy",
        time,
        0.9 if root else 0.1,
        released_block,
        keys,
    )
    action = time % 2
    if adaptive_edge == "W_Y":
        outcome_probability = 0.9 if world else 0.1
    else:
        outcome_probability = 0.9 if root else 0.1
    outcome = _bernoulli(
        seed,
        "history:outcome",
        time,
        outcome_probability,
        released_block,
        keys,
    )
    return ReductionSlice(
        time, 0, mode, root, world, policy, action, outcome, "historical"
    )


def _sample_current_slice(
    seed: int,
    time: int,
    config: ReductionConfig,
    kind: str,
    local_index: int,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> ReductionSlice:
    event = time
    mode = _bernoulli(seed, f"{kind}:mode", event, 0.5, released_block, keys)
    dependency_returns = kind == "return" and config.return_burden
    suggestion = config.corrective_evidence == "suggestion_only"
    configural = (
        config.corrective_evidence == "configural"
        or kind == "imaginal_post"
    )
    premature_imaginal = kind == "imaginal_premature"
    if dependency_returns or suggestion:
        root_probability = 0.9 if mode else 0.1
    elif configural or premature_imaginal:
        root_probability = 0.2 if config.root_revision else 0.5
    else:
        root_probability = 0.9 if mode else 0.1
    root = _bernoulli(
        seed, f"{kind}:root", event, root_probability, released_block, keys
    )
    if dependency_returns or suggestion:
        world_probability = 0.9 if root else 0.1
        policy_probability = 0.9 if root else 0.1
    else:
        world_probability = 0.5
        policy_probability = 0.5
    world = _bernoulli(
        seed, f"{kind}:world", event, world_probability, released_block, keys
    )
    policy = _bernoulli(
        seed, f"{kind}:policy", event, policy_probability, released_block, keys
    )
    action = local_index % 2
    if config.adaptive_edge == "W_Y":
        outcome_probability = 0.9 if world else 0.1
    elif dependency_returns or suggestion:
        outcome_probability = 0.9 if root else 0.1
    else:
        outcome_probability = 0.2
    outcome = _bernoulli(
        seed,
        f"{kind}:outcome",
        event,
        outcome_probability,
        released_block,
        keys,
    )
    return ReductionSlice(
        time,
        1,
        mode,
        root,
        world,
        policy,
        action,
        outcome,
        kind,
    )


def generate_world(
    seed: int,
    config: ReductionConfig,
    *,
    released_block: tuple[int, int] | None = None,
) -> ReductionWorld:
    require_trace_sink("v33.generate_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    history_structure = formed_structure(adaptive_edge=config.adaptive_edge)
    current_structure = (
        reduced_structure(adaptive_edge=config.adaptive_edge)
        if config.corrective_evidence == "configural"
        and not config.return_burden
        else history_structure
    )
    slices: list[ReductionSlice] = []
    for time in range(config.history_length):
        slices.append(
            _sample_history_slice(
                seed,
                time,
                config.adaptive_edge,
                released_block,
                keys,
            )
        )
    current_time = config.history_length
    if config.do_over == "premature":
        for index in range(12):
            slices.append(
                _sample_current_slice(
                    seed,
                    current_time,
                    config,
                    "imaginal_premature",
                    index,
                    released_block,
                    keys,
                )
            )
            current_time += 1
    for index in range(config.corrective_length):
        kind = (
            "corrective"
            if config.corrective_evidence != "none"
            else "ordinary"
        )
        slices.append(
            _sample_current_slice(
                seed,
                current_time,
                config,
                kind,
                index,
                released_block,
                keys,
            )
        )
        current_time += 1
    if config.do_over == "post_revision":
        for index in range(12):
            slices.append(
                _sample_current_slice(
                    seed,
                    current_time,
                    config,
                    "imaginal_post",
                    index,
                    released_block,
                    keys,
                )
            )
            current_time += 1
    elif (
        config.do_over == "none"
        and config.corrective_evidence == "configural"
    ):
        # Same scheduled opportunity as the imaginal arm, but with every typed
        # channel masked.  It contributes exactly zero structural evidence.
        for _ in range(12):
            slices.append(
                ReductionSlice(
                    current_time,
                    1,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "no_do_masked",
                )
            )
            current_time += 1
    for index in range(config.return_length):
        slices.append(
            _sample_current_slice(
                seed,
                current_time,
                config,
                "return",
                index,
                released_block,
                keys,
            )
        )
        current_time += 1
    provisional = ReductionWorld(
        int(seed),
        config,
        history_structure,
        current_structure,
        tuple(slices),
        0.0,
        tuple(keys),
    )
    exact = _program_log_joint(
        _context_slices(provisional, 1),
        current_structure,
        v31.DEFAULT_HYPERPARAMETERS,
    )
    return ReductionWorld(
        provisional.seed,
        provisional.config,
        provisional.historical_structure,
        provisional.current_truth_structure,
        provisional.slices,
        float(exact),
        provisional.rng_keys,
    )


def append_neutral_observation(world: ReductionWorld) -> ReductionWorld:
    require_trace_sink("v33.append_neutral_observation", seed=int(world.seed))
    time = max((item.time for item in world.slices), default=-1) + 1
    neutral = ReductionSlice(
        time, 1, None, None, None, None, None, None, "neutral"
    )
    return ReductionWorld(
        world.seed,
        world.config,
        world.historical_structure,
        world.current_truth_structure,
        world.slices + (neutral,),
        world.exact_log_probability,
        world.rng_keys,
        world.analysis_labels,
    )


def relabel_episode(
    world: ReductionWorld, source: str, target: str
) -> ReductionWorld:
    """Change analysis metadata only; scientific typed evidence is untouched."""
    require_trace_sink("v33.relabel_episode", seed=int(world.seed))
    slices = tuple(
        ReductionSlice(
            item.time,
            item.context,
            item.mode,
            item.root,
            item.world,
            item.policy_proposal,
            item.action,
            item.outcome,
            target if item.episode_kind == source else item.episode_kind,
        )
        for item in world.slices
    )
    return ReductionWorld(
        world.seed,
        world.config,
        world.historical_structure,
        world.current_truth_structure,
        slices,
        world.exact_log_probability,
        world.rng_keys,
        world.analysis_labels,
    )


def burden_absent_present_bf(
    posterior: ContextPosterior,
    hyperparameters: v31.V31Hyperparameters = v31.DEFAULT_HYPERPARAMETERS,
) -> float:
    absent_mass = math.fsum(
        probability
        for program, probability in zip(
            posterior.programs, posterior.probabilities
        )
        if all(v31.program_values(program)[edge] == 0 for edge in BURDEN_EDGES)
    )
    present_mass = math.fsum(
        probability
        for program, probability in zip(
            posterior.programs, posterior.probabilities
        )
        if all(v31.program_values(program)[edge] == 1 for edge in BURDEN_EDGES)
    )
    prior_absent = math.fsum(
        math.exp(v31.structure_log_prior(program, hyperparameters))
        for program in PROGRAMS
        if all(v31.program_values(program)[edge] == 0 for edge in BURDEN_EDGES)
    )
    prior_present = math.fsum(
        math.exp(v31.structure_log_prior(program, hyperparameters))
        for program in PROGRAMS
        if all(v31.program_values(program)[edge] == 1 for edge in BURDEN_EDGES)
    )
    return float((absent_mass / present_mass) / (prior_absent / prior_present))


def material_reduction_readout(
    world: ReductionWorld,
    posterior: ReductionPosterior,
    thresholds: MaterialReductionThresholds,
) -> Mapping[str, Any]:
    current_slices = list(_context_slices(world, 1))
    stability = []
    for offset in range(thresholds.stability_observations):
        prefix = current_slices[: len(current_slices) - offset]
        local = _score_context(prefix, v31.DEFAULT_HYPERPARAMETERS)
        mass = max(local.edge_probabilities[edge] for edge in BURDEN_EDGES)
        bf = burden_absent_present_bf(local)
        stability.append(
            local.active_mode_probability >= thresholds.mode_retained
            and mass <= thresholds.burden_edge_mass_max
            and bf >= thresholds.absent_present_bf_min
        )
    neutral = append_neutral_observation(world)
    neutral_posterior = score_world(neutral)
    neutral_error = max(
        abs(a - b)
        for a, b in zip(
            posterior.current.probabilities,
            neutral_posterior.current.probabilities,
        )
    )
    bf = burden_absent_present_bf(posterior.current)
    material = (
        posterior.current.active_mode_probability >= thresholds.mode_retained
        and posterior.burden_edge_mass <= thresholds.burden_edge_mass_max
        and bf >= thresholds.absent_present_bf_min
        and all(stability)
        and neutral_error <= thresholds.neutral_tolerance
    )
    return MappingProxyType(
        {
            "material": bool(material),
            "mode_retained": posterior.current.active_mode_probability,
            "burden_edge_mass": posterior.burden_edge_mass,
            "absent_present_bf": bf,
            "stable": bool(all(stability)),
            "neutral_survival_error": neutral_error,
            "old_graph_probability": posterior.old_graph_probability,
        }
    )


def first_material_time(
    world: ReductionWorld, thresholds: MaterialReductionThresholds
) -> int | None:
    current = list(_context_slices(world, 1))
    consecutive = 0
    for length in range(thresholds.stability_observations, len(current) + 1):
        local = _score_context(
            current[:length], v31.DEFAULT_HYPERPARAMETERS
        )
        mass = max(local.edge_probabilities[edge] for edge in BURDEN_EDGES)
        eligible = (
            local.active_mode_probability >= thresholds.mode_retained
            and mass <= thresholds.burden_edge_mass_max
            and burden_absent_present_bf(local)
            >= thresholds.absent_present_bf_min
        )
        consecutive = consecutive + 1 if eligible else 0
        if consecutive >= thresholds.stability_observations:
            return length
    return None


def generate_recovery_world(
    seed: int,
    *,
    length: int = 64,
    hyperparameters: v31.V31Hyperparameters = v31.DEFAULT_HYPERPARAMETERS,
    released_block: tuple[int, int] | None = None,
) -> ReductionWorld:
    require_trace_sink("v33.generate_recovery_world", seed=int(seed))
    keys: list[tuple[str, int, str, int | str]] = []
    truth = {}
    for index, field in enumerate(("active_mode",) + EDGE_NAMES):
        probability = v31._binary_prior(
            1, hyperparameters.code_length_scale
        )
        truth[field] = int(
            _rng(
                seed,
                f"recovery:structure:{field}",
                index,
                released_block,
                keys,
            ).random()
            < probability
        )
    structure = v31.make_structure(
        truth.pop("active_mode"), **truth
    )
    values = v31.program_values(structure)
    concentration = hyperparameters.concentration

    def beta_rows(name: str, rows: int) -> tuple[float, ...]:
        return tuple(
            float(
                _rng(
                    seed,
                    f"recovery:theta:{name}",
                    row,
                    released_block,
                    keys,
                ).beta(concentration, concentration)
            )
            for row in range(rows)
        )

    theta_mode = beta_rows("mode", 1)
    theta_root = beta_rows("root", 2 if values["M1_G"] else 1)
    theta_world = beta_rows("world", 2 if values["G_W"] else 1)
    theta_policy = beta_rows("policy", 2 if values["G_A"] else 1)
    y_edges = tuple(values[name] for name in ("G_Y", "W_Y", "doA_Y"))
    theta_outcome = beta_rows("outcome", 1 << sum(y_edges))
    slices = []
    for time in range(length):
        mode = (
            _bernoulli(
                seed,
                "recovery:mode",
                time,
                theta_mode[0],
                released_block,
                keys,
            )
            if values["active_mode"]
            else 0
        )
        root = _bernoulli(
            seed,
            "recovery:root",
            time,
            theta_root[mode if values["M1_G"] else 0],
            released_block,
            keys,
        )
        world = _bernoulli(
            seed,
            "recovery:world",
            time,
            theta_world[root if values["G_W"] else 0],
            released_block,
            keys,
        )
        policy = _bernoulli(
            seed,
            "recovery:policy",
            time,
            theta_policy[root if values["G_A"] else 0],
            released_block,
            keys,
        )
        action = time % 2
        parent_values = (root, world, action)
        row = 0
        bit = 0
        for present, parent in zip(y_edges, parent_values):
            if present:
                row |= int(parent) << bit
                bit += 1
        outcome = _bernoulli(
            seed,
            "recovery:outcome",
            time,
            theta_outcome[row],
            released_block,
            keys,
        )
        slices.append(
            ReductionSlice(
                time,
                1,
                mode,
                root,
                world,
                policy,
                action,
                outcome,
                "recovery",
            )
        )
    provisional = ReductionWorld(
        seed,
        None,
        formed_structure(),
        structure,
        tuple(slices),
        0.0,
        tuple(keys),
    )
    exact = _program_log_joint(
        provisional.slices, structure, hyperparameters
    )
    return ReductionWorld(
        provisional.seed,
        provisional.config,
        provisional.historical_structure,
        provisional.current_truth_structure,
        provisional.slices,
        float(exact),
        provisional.rng_keys,
    )
