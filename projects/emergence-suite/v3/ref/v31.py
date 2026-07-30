"""V3.1 GROW: exact graph formation, efficacy, and availability.

There is no formation menu.  The posterior ranges over ordinary productions
from the V3.0 grammar: one optional mode and six generic edges.  The familiar
transient/danger/part distinctions are pure sums over regions of that graph
posterior.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from .grammar import GrammarBounds, GrammarStructure


STAGE_VERSION = "V3.1"
DEVELOPMENT_BLOCK = (3_100_000, 3_129_999)
EDGE_NAMES = ("M1_G", "G_W", "G_A", "G_Y", "W_Y", "doA_Y")
Y_EDGE_NAMES = ("G_Y", "W_Y", "doA_Y")
V31_BOUNDS = GrammarBounds(context_slots=2, mode_slots=1, cue_count=3)


@dataclass(frozen=True)
class FormationConfig:
    adversity: str
    control: str
    precision: str
    danger: str
    action: str
    availability: str
    length: int = 48

    def __post_init__(self) -> None:
        valid = {
            "adversity": {"none", "acute", "repeated"},
            "control": {"low", "high"},
            "precision": {"narrow", "broad"},
            "danger": {"safe", "real"},
            "action": {"irrelevant", "effective"},
            "availability": {"full", "censored"},
        }
        for field, support in valid.items():
            if getattr(self, field) not in support:
                raise ValueError(f"invalid {field}")
        if self.length < 1:
            raise ValueError("length must be positive")


@dataclass(frozen=True)
class FormationSlice:
    time: int
    event: int
    mode: int
    root: int
    world: int
    policy_proposal: int
    action: int
    outcome_true: int
    outcome_observed: int | None
    mode_observed: bool
    root_observed: bool


@dataclass(frozen=True)
class FormationWorld:
    seed: int
    config: FormationConfig | None
    structure: GrammarStructure
    slices: tuple[FormationSlice, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class FormationPosterior:
    programs: tuple[GrammarStructure, ...]
    probabilities: tuple[float, ...]
    log_evidence: float
    edge_probabilities: Mapping[str, float]
    active_mode_probability: float
    transient_probability: float
    danger_probability: float
    part_probability: float
    efficacy_probability: float
    delta_i: float
    burden_mass: float

    def structure_posterior(self, structure: GrammarStructure) -> float:
        return self.probabilities[self.programs.index(structure)]


@dataclass(frozen=True)
class V31Hyperparameters:
    concentration: float = 0.5
    code_length_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.concentration <= 0 or self.code_length_scale <= 0:
            raise ValueError("hyperparameters must be positive")


DEFAULT_HYPERPARAMETERS = V31Hyperparameters()


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    start, end = block
    if not start <= seed <= end:
        raise ValueError("seed is outside the authorized V3.1 block")
    key = (STAGE_VERSION, int(seed), str(component), event)
    keys.append(key)
    digest = hashlib.sha256(repr(key).encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _edge_vector(values: Mapping[str, int]) -> tuple[int, ...]:
    return (
        int(values.get("M1_G", 0)),
        0,
        0,
        int(values.get("G_W", 0)),
        int(values.get("G_A", 0)),
        int(values.get("G_Y", 0)),
        int(values.get("W_Y", 0)),
        int(values.get("doA_Y", 0)),
    )


def make_structure(active_mode: int, **edges: int) -> GrammarStructure:
    return GrammarStructure(
        active_modes=int(active_mode),
        active_contexts=2,
        edges=_edge_vector(edges),
        scopes=("shared_global", "shared_global"),
        dynamics=("static", "static"),
    )


def program_values(structure: GrammarStructure) -> Mapping[str, int]:
    return MappingProxyType(
        {
            "active_mode": int(structure.active_modes > 0),
            "M1_G": structure.edges[0],
            "G_W": structure.edges[3],
            "G_A": structure.edges[4],
            "G_Y": structure.edges[5],
            "W_Y": structure.edges[6],
            "doA_Y": structure.edges[7],
        }
    )


def enumerate_programs() -> tuple[GrammarStructure, ...]:
    return tuple(
        make_structure(active_mode, **dict(zip(EDGE_NAMES, bits)))
        for active_mode in (0, 1)
        for bits in itertools.product((0, 1), repeat=len(EDGE_NAMES))
    )


PROGRAMS = enumerate_programs()


def _binary_prior(value: int, scale: float) -> float:
    absent = 2.0 ** (-scale)
    present = 2.0 ** (-2.0 * scale)
    return (present if value else absent) / (absent + present)


def structure_log_prior(
    structure: GrammarStructure,
    hyperparameters: V31Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    return math.fsum(
        math.log(_binary_prior(value, hyperparameters.code_length_scale))
        for value in program_values(structure).values()
    )


def _log_beta(a: float, b: float) -> float:
    return math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)


def beta_bernoulli_log_marginal(
    rows: Iterable[tuple[int, int]], concentration: float = 0.5
) -> float:
    return math.fsum(
        _log_beta(zeros + concentration, ones + concentration)
        - _log_beta(concentration, concentration)
        for zeros, ones in rows
    )


def _counts(
    slices: Sequence[FormationSlice],
    child: str,
    parents: tuple[str, ...],
    *,
    sever_precision: bool = False,
    reveal_censored: bool = False,
) -> tuple[tuple[int, int], ...]:
    parent_rows = 1 << len(parents)
    counts = [[0, 0] for _ in range(parent_rows)]
    for item in slices:
        if child == "mode":
            if not item.mode_observed and not sever_precision:
                continue
            if sever_precision and item.time % 2:
                continue
            value = item.mode
        elif child == "root":
            if not item.root_observed and not sever_precision:
                continue
            if sever_precision and item.time % 2:
                continue
            value = item.root
        elif child == "world":
            value = item.world
        elif child == "policy_proposal":
            value = item.policy_proposal
        elif child == "outcome":
            if item.outcome_observed is None and not reveal_censored:
                continue
            value = (
                item.outcome_true
                if item.outcome_observed is None
                else item.outcome_observed
            )
        else:
            raise KeyError(child)
        parent_index = 0
        for bit, parent in enumerate(parents):
            parent_value = {
                "mode": item.mode,
                "root": item.root,
                "world": item.world,
                "action": int(item.action == 1),
            }[parent]
            parent_index |= int(parent_value) << bit
        counts[parent_index][int(value)] += 1
    return tuple((row[0], row[1]) for row in counts)


def _mode_log_score(
    slices: Sequence[FormationSlice],
    active: int,
    concentration: float,
    sever_precision: bool,
    mask_channel: bool = False,
) -> float:
    if mask_channel:
        return 0.0
    observed = [
        item.mode
        for item in slices
        if (item.mode_observed or sever_precision)
        and (not sever_precision or item.time % 2 == 0)
    ]
    if active == 0:
        return 0.0 if not any(observed) else -math.inf
    return beta_bernoulli_log_marginal(
        ((observed.count(0), observed.count(1)),), concentration
    )


def _program_log_joint(
    world: FormationWorld,
    structure: GrammarStructure,
    hyperparameters: V31Hyperparameters,
    lesions: frozenset[str],
) -> float:
    values = program_values(structure)
    if "mode_slot" in lesions and values["active_mode"]:
        return -math.inf
    if "identity_edges" in lesions and any(
        values[name] for name in ("M1_G", "G_W", "G_A", "G_Y")
    ):
        return -math.inf
    if "action_edge" in lesions and values["doA_Y"]:
        return -math.inf
    concentration = hyperparameters.concentration
    sever_precision = "recursive_precision" in lesions
    reveal_censored = "availability_control" in lesions
    total = structure_log_prior(structure, hyperparameters)
    total += _mode_log_score(
        world.slices,
        values["active_mode"],
        concentration,
        sever_precision,
        mask_channel="mode_slot" in lesions,
    )
    total += beta_bernoulli_log_marginal(
        _counts(
            world.slices,
            "root",
            ("mode",) if values["M1_G"] else (),
            sever_precision=sever_precision,
        ),
        concentration,
    )
    total += beta_bernoulli_log_marginal(
        _counts(
            world.slices,
            "world",
            ("root",) if values["G_W"] else (),
        ),
        concentration,
    )
    total += beta_bernoulli_log_marginal(
        _counts(
            world.slices,
            "policy_proposal",
            ("root",) if values["G_A"] else (),
        ),
        concentration,
    )
    y_parents = tuple(
        parent
        for edge, parent in (
            ("G_Y", "root"),
            ("W_Y", "world"),
            ("doA_Y", "action"),
        )
        if values[edge]
    )
    total += beta_bernoulli_log_marginal(
        _counts(
            world.slices,
            "outcome",
            y_parents,
            reveal_censored=reveal_censored,
        ),
        concentration,
    )
    return total


def _part_condition(values: Mapping[str, int]) -> bool:
    identity_predictions = sum(values[name] for name in ("G_W", "G_A", "G_Y"))
    return bool(
        values["active_mode"] and values["M1_G"] and identity_predictions >= 2
    )


def _posterior_mutual_information(
    world: FormationWorld,
    concentration: float,
) -> float:
    g_counts = _counts(world.slices, "root", ())
    total_g = sum(g_counts[0])
    p_g = np.asarray(
        [
            (g_counts[0][0] + concentration) / (total_g + 2 * concentration),
            (g_counts[0][1] + concentration) / (total_g + 2 * concentration),
        ]
    )
    conditional = np.empty((2, 2))
    rows = _counts(world.slices, "world", ("root",))
    for root in (0, 1):
        total = sum(rows[root])
        conditional[root] = [
            (rows[root][value] + concentration)
            / (total + 2 * concentration)
            for value in (0, 1)
        ]
    joint = p_g[:, None] * conditional
    p_w = joint.sum(axis=0)
    result = 0.0
    for root in (0, 1):
        for world_value in (0, 1):
            probability = joint[root, world_value]
            result += probability * math.log(
                probability / (p_g[root] * p_w[world_value])
            )
    return result


def score_world(
    world: FormationWorld,
    *,
    hyperparameters: V31Hyperparameters = DEFAULT_HYPERPARAMETERS,
    lesions: frozenset[str] = frozenset(),
) -> FormationPosterior:
    if world.analysis_labels:
        raise ValueError("analysis labels may not reach V3.1 inference")
    log_weights = np.asarray(
        [
            _program_log_joint(world, program, hyperparameters, lesions)
            for program in PROGRAMS
        ],
        dtype=float,
    )
    maximum = float(np.max(log_weights))
    log_evidence = maximum + math.log(float(np.exp(log_weights - maximum).sum()))
    probabilities = np.exp(log_weights - log_evidence)
    edges = {
        edge: float(
            sum(
                probability
                for program, probability in zip(PROGRAMS, probabilities)
                if program_values(program)[edge]
            )
        )
        for edge in EDGE_NAMES
    }
    active_mode = float(
        sum(
            probability
            for program, probability in zip(PROGRAMS, probabilities)
            if program_values(program)["active_mode"]
        )
    )
    part = float(
        sum(
            probability
            for program, probability in zip(PROGRAMS, probabilities)
            if _part_condition(program_values(program))
        )
    )
    danger = float(
        sum(
            probability
            for program, probability in zip(PROGRAMS, probabilities)
            if program_values(program)["W_Y"]
            and not _part_condition(program_values(program))
        )
    )
    transient = float(
        sum(
            probability
            for program, probability in zip(PROGRAMS, probabilities)
            if not program_values(program)["W_Y"]
            and not _part_condition(program_values(program))
        )
    )
    delta_i = edges["G_W"] * _posterior_mutual_information(
        world, hyperparameters.concentration
    )
    return FormationPosterior(
        programs=PROGRAMS,
        probabilities=tuple(float(value) for value in probabilities),
        log_evidence=log_evidence,
        edge_probabilities=MappingProxyType(edges),
        active_mode_probability=active_mode,
        transient_probability=transient,
        danger_probability=danger,
        part_probability=part,
        efficacy_probability=edges["doA_Y"],
        delta_i=float(delta_i),
        burden_mass=float(sum(edges[name] for name in ("G_W", "G_A", "G_Y"))),
    )


def transfer_readout(
    posterior: FormationPosterior,
    *,
    root_evidence_strength: float = 1.0,
    fixed_identity: bool = False,
) -> float:
    if fixed_identity:
        return 0.0
    return float(
        root_evidence_strength
        * posterior.edge_probabilities["M1_G"]
        * max(
            posterior.edge_probabilities["G_W"],
            posterior.edge_probabilities["G_Y"],
        )
    )


def outcome_edge_log_bf(
    world: FormationWorld,
    edge: str,
    *,
    hyperparameters: V31Hyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    """Pure local-score readout for one outcome-parent production."""
    if edge not in Y_EDGE_NAMES:
        raise ValueError("edge must be an outcome parent")
    parent = {"G_Y": "root", "W_Y": "world", "doA_Y": "action"}[edge]
    present = beta_bernoulli_log_marginal(
        _counts(world.slices, "outcome", (parent,)),
        hyperparameters.concentration,
    )
    absent = beta_bernoulli_log_marginal(
        _counts(world.slices, "outcome", ()),
        hyperparameters.concentration,
    )
    return float(
        present
        - absent
        + math.log(_binary_prior(1, hyperparameters.code_length_scale))
        - math.log(_binary_prior(0, hyperparameters.code_length_scale))
    )


def truth_structure(config: FormationConfig) -> GrammarStructure:
    identity_bearing = (
        config.adversity == "repeated"
        and config.control == "low"
        and config.precision == "broad"
    )
    return make_structure(
        int(identity_bearing),
        M1_G=int(identity_bearing),
        G_W=int(identity_bearing),
        G_A=int(identity_bearing),
        G_Y=int(identity_bearing),
        W_Y=int(config.danger == "real"),
        doA_Y=int(config.action == "effective"),
    )


def _event(config: FormationConfig, time: int) -> int:
    if config.adversity == "none":
        return 0
    if config.adversity == "acute":
        return int(time == max(1, config.length // 3))
    return int(time % 4 in (1, 2))


def _bernoulli(
    seed: int,
    component: str,
    event: int,
    probability: float,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    return int(_rng(seed, component, event, released_block, keys).random() < probability)


def generate_world(
    seed: int,
    config: FormationConfig,
    *,
    released_block: tuple[int, int] | None = None,
) -> FormationWorld:
    """Generate an open developmental world with no analysis classification."""
    keys: list[tuple[str, int, str, int | str]] = []
    structure = truth_structure(config)
    truth = program_values(structure)
    slices = []
    for time in range(config.length):
        event = _event(config, time)
        mode_probability = (
            0.85 if truth["active_mode"] and event else 0.08
            if truth["active_mode"]
            else 0.0
        )
        mode = _bernoulli(
            seed, "mode", time, mode_probability, released_block, keys
        )
        root_probability = (
            0.88 if truth["M1_G"] and mode else 0.12 if truth["M1_G"] else 0.2
        )
        root = _bernoulli(
            seed, "root", time, root_probability, released_block, keys
        )
        if truth["G_W"]:
            world_probability = 0.86 if root else 0.14
        elif config.danger == "real":
            world_probability = 0.82 if event else 0.25
        else:
            world_probability = 0.12
        world_value = _bernoulli(
            seed, "world", time, world_probability, released_block, keys
        )
        proposal_probability = (
            0.86 if truth["G_A"] and root else 0.14 if truth["G_A"] else 0.35
        )
        proposal = _bernoulli(
            seed, "policy-proposal", time, proposal_probability, released_block, keys
        )
        if config.control == "high":
            action = time % 2
        else:
            action = 1 if time % 5 else 0
        logit = -2.0
        if truth["G_Y"] and root:
            logit += 2.2
        if truth["W_Y"] and world_value:
            logit += 2.8
        if truth["doA_Y"] and action == 1:
            logit -= 2.4
        outcome_probability = 1.0 / (1.0 + math.exp(-logit))
        outcome = _bernoulli(
            seed, "outcome", time, outcome_probability, released_block, keys
        )
        censored = config.availability == "censored" and action == 1
        mode_observed = config.precision == "broad" or time % 3 == 0
        root_observed = config.precision == "broad" or time % 3 == 0
        slices.append(
            FormationSlice(
                time,
                event,
                mode,
                root,
                world_value,
                proposal,
                action,
                outcome,
                None if censored else outcome,
                mode_observed,
                root_observed,
            )
        )
    world = FormationWorld(
        int(seed),
        config,
        structure,
        tuple(slices),
        0.0,
        tuple(keys),
    )
    exact = _program_log_joint(
        world, structure, DEFAULT_HYPERPARAMETERS, frozenset()
    )
    return FormationWorld(
        world.seed,
        world.config,
        world.structure,
        world.slices,
        float(exact),
        world.rng_keys,
    )


def _sample_beta_rows(
    seed: int,
    component: str,
    rows: int,
    concentration: float,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[float, ...]:
    values = []
    for row in range(rows):
        rng = _rng(seed, component, row, released_block, keys)
        values.append(float(rng.beta(concentration, concentration)))
    return tuple(values)


def generate_recovery_world(
    seed: int,
    *,
    length: int = 64,
    hyperparameters: V31Hyperparameters = DEFAULT_HYPERPARAMETERS,
    released_block: tuple[int, int] | None = None,
) -> FormationWorld:
    """Sample structure and CPTs from the exact scorer prior."""
    keys: list[tuple[str, int, str, int | str]] = []
    truth_bits = {}
    for index, field in enumerate(("active_mode",) + EDGE_NAMES):
        rng = _rng(seed, f"structure:{field}", index, released_block, keys)
        probability = _binary_prior(1, hyperparameters.code_length_scale)
        truth_bits[field] = int(rng.random() < probability)
    structure = make_structure(
        truth_bits.pop("active_mode"), **truth_bits
    )
    values = program_values(structure)
    concentration = hyperparameters.concentration
    theta_mode = _sample_beta_rows(
        seed, "theta:mode", 1, concentration, released_block, keys
    )
    theta_root = _sample_beta_rows(
        seed,
        "theta:root",
        2 if values["M1_G"] else 1,
        concentration,
        released_block,
        keys,
    )
    theta_world = _sample_beta_rows(
        seed,
        "theta:world",
        2 if values["G_W"] else 1,
        concentration,
        released_block,
        keys,
    )
    theta_policy = _sample_beta_rows(
        seed,
        "theta:policy",
        2 if values["G_A"] else 1,
        concentration,
        released_block,
        keys,
    )
    y_edges = [values[name] for name in Y_EDGE_NAMES]
    theta_outcome = _sample_beta_rows(
        seed,
        "theta:outcome",
        1 << sum(y_edges),
        concentration,
        released_block,
        keys,
    )
    slices = []
    for time in range(length):
        mode = (
            _bernoulli(
                seed, "recovery:mode", time, theta_mode[0], released_block, keys
            )
            if values["active_mode"]
            else 0
        )
        root_row = mode if values["M1_G"] else 0
        root = _bernoulli(
            seed,
            "recovery:root",
            time,
            theta_root[root_row],
            released_block,
            keys,
        )
        world_row = root if values["G_W"] else 0
        world_value = _bernoulli(
            seed,
            "recovery:world",
            time,
            theta_world[world_row],
            released_block,
            keys,
        )
        policy_row = root if values["G_A"] else 0
        proposal = _bernoulli(
            seed,
            "recovery:policy",
            time,
            theta_policy[policy_row],
            released_block,
            keys,
        )
        action = time % 2
        parent_values = (root, world_value, action)
        outcome_row = 0
        bit = 0
        for present, parent_value in zip(y_edges, parent_values):
            if present:
                outcome_row |= int(parent_value) << bit
                bit += 1
        outcome = _bernoulli(
            seed,
            "recovery:outcome",
            time,
            theta_outcome[outcome_row],
            released_block,
            keys,
        )
        slices.append(
            FormationSlice(
                time,
                0,
                mode,
                root,
                world_value,
                proposal,
                action,
                outcome,
                outcome,
                True,
                True,
            )
        )
    world = FormationWorld(
        seed,
        None,
        structure,
        tuple(slices),
        0.0,
        tuple(keys),
    )
    exact = _program_log_joint(world, structure, hyperparameters, frozenset())
    return FormationWorld(
        seed,
        None,
        structure,
        world.slices,
        float(exact),
        world.rng_keys,
    )


def prefix_world(world: FormationWorld, length: int) -> FormationWorld:
    slices = world.slices[:length]
    partial = FormationWorld(
        world.seed,
        world.config,
        world.structure,
        slices,
        0.0,
        world.rng_keys,
    )
    return FormationWorld(
        partial.seed,
        partial.config,
        partial.structure,
        partial.slices,
        _program_log_joint(
            partial, partial.structure, DEFAULT_HYPERPARAMETERS, frozenset()
        ),
        partial.rng_keys,
    )


def append_safe_observations(
    world: FormationWorld, count: int = 12
) -> FormationWorld:
    slices = list(world.slices)
    start = len(slices)
    for offset in range(count):
        time = start + offset
        slices.append(
            FormationSlice(
                time,
                0,
                0,
                0,
                offset % 2,
                0,
                offset % 2,
                0,
                0,
                True,
                True,
            )
        )
    result = FormationWorld(
        world.seed,
        world.config,
        world.structure,
        tuple(slices),
        0.0,
        world.rng_keys,
    )
    return FormationWorld(
        result.seed,
        result.config,
        result.structure,
        result.slices,
        _program_log_joint(
            result, result.structure, DEFAULT_HYPERPARAMETERS, frozenset()
        ),
        result.rng_keys,
    )
