"""V3.0 bounded exact context-indexed sparse-graph grammar.

The public V3.0 fixture has two generic parameter blocks.  Complete grammar
programs are numerous, but their prior and likelihood decompose by field.
`score_world` therefore sums every finite field support exactly and returns
the exact joint structure posterior in factored form.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np

from .rng import component_key, component_rng


EDGES = ("M1_G", "M2_G", "M3_G", "G_W", "G_A", "G_Y", "W_Y", "doA_Y")
SCOPES = ("shared_global", "cue_specific", "context_specific", "mode_specific")
DYNAMICS = (
    "static",
    "discrete_recurrent_context",
    "ordered_random_walk",
    "one_way_change",
)
BLOCKS = ("cue_emission", "outcome_emission")
ANALYSIS_LABELS = frozenset(
    {
        "formed",
        "part",
        "protector",
        "exile",
        "burden",
        "unburdened",
        "grow",
        "split",
        "prune",
        "T",
        "D",
        "P",
    }
)


@dataclass(frozen=True)
class GrammarBounds:
    context_slots: int = 3
    mode_slots: int = 3
    cue_count: int = 3

    def __post_init__(self) -> None:
        if not 1 <= self.context_slots <= 3:
            raise ValueError("context_slots must be in [1, 3]")
        if not 1 <= self.mode_slots <= 3:
            raise ValueError("mode_slots must be in [1, 3]")
        if not 1 <= self.cue_count <= 8:
            raise ValueError("cue_count must be in [1, 8]")


@dataclass(frozen=True)
class GrammarStructure:
    active_modes: int
    active_contexts: int
    edges: tuple[int, ...]
    scopes: tuple[str, ...]
    dynamics: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.edges) != len(EDGES) or any(v not in (0, 1) for v in self.edges):
            raise ValueError("edges must be an eight-bit mask")
        if len(self.scopes) != len(BLOCKS) or any(v not in SCOPES for v in self.scopes):
            raise ValueError("one valid scope is required for each block")
        if len(self.dynamics) != len(BLOCKS) or any(
            v not in DYNAMICS for v in self.dynamics
        ):
            raise ValueError("one valid dynamics value is required for each block")


@dataclass(frozen=True)
class TypedObservation:
    field: str
    index: int
    value: int
    missing: bool = False


@dataclass(frozen=True)
class GrammarWorld:
    seed: int
    bounds: GrammarBounds
    structure: GrammarStructure
    observations: tuple[TypedObservation, ...]
    interventions: tuple[int, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructurePosterior:
    field_probabilities: Mapping[str, tuple[float, ...]]
    supports: Mapping[str, tuple[Any, ...]]
    log_evidence: float
    world_log_probability: float

    def probability(self, field: str, value: Any) -> float:
        support = self.supports[field]
        return self.field_probabilities[field][support.index(value)]

    def argmax(self, field: str) -> Any:
        probs = self.field_probabilities[field]
        return self.supports[field][int(np.argmax(probs))]


@dataclass(frozen=True)
class GrammarHyperparameters:
    diagnostic_reliability: float = 0.86
    concentration: float = 0.5
    code_length_scale: float = 1.0

    def __post_init__(self) -> None:
        if not 0.5 < self.diagnostic_reliability < 1.0:
            raise ValueError("diagnostic_reliability must be in (0.5, 1)")
        if self.concentration <= 0 or self.code_length_scale <= 0:
            raise ValueError("positive concentration and code length scale required")


DEFAULT_HYPERPARAMETERS = GrammarHyperparameters()


def field_supports(bounds: GrammarBounds) -> Mapping[str, tuple[Any, ...]]:
    fields: dict[str, tuple[Any, ...]] = {
        "active_modes": tuple(range(bounds.mode_slots + 1)),
        "active_contexts": tuple(range(1, bounds.context_slots + 1)),
    }
    fields.update({f"edge:{edge}": (0, 1) for edge in EDGES})
    fields.update({f"scope:{block}": SCOPES for block in BLOCKS})
    fields.update({f"dynamics:{block}": DYNAMICS for block in BLOCKS})
    return MappingProxyType(fields)


def code_length(field: str, value: Any) -> float:
    """Frozen prefix-code cost in bits for one grammar field."""
    if field == "active_modes":
        return 1.0 + float(value)
    if field == "active_contexts":
        return 1.0 + float(value) - 1.0
    if field.startswith("edge:"):
        return 1.0 + float(value)
    if field.startswith("scope:"):
        return 1.0 if value == "shared_global" else 3.0
    if field.startswith("dynamics:"):
        return 1.0 if value == "static" else 3.0
    raise KeyError(field)


def field_prior(
    field: str,
    support: Sequence[Any],
    hyperparameters: GrammarHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> np.ndarray:
    lengths = np.asarray([code_length(field, value) for value in support], dtype=float)
    weights = np.exp2(-hyperparameters.code_length_scale * lengths)
    return weights / weights.sum()


def structure_space_size(bounds: GrammarBounds = GrammarBounds()) -> int:
    size = 1
    for support in field_supports(bounds).values():
        size *= len(support)
    return int(size)


def structure_log_prior(
    structure: GrammarStructure,
    bounds: GrammarBounds,
    hyperparameters: GrammarHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    total = 0.0
    for field, value in structure_values(structure).items():
        support = field_supports(bounds)[field]
        total += math.log(field_prior(field, support, hyperparameters)[support.index(value)])
    return total


def structure_values(structure: GrammarStructure) -> Mapping[str, Any]:
    values: dict[str, Any] = {
        "active_modes": structure.active_modes,
        "active_contexts": structure.active_contexts,
    }
    values.update({f"edge:{name}": value for name, value in zip(EDGES, structure.edges)})
    values.update(
        {f"scope:{name}": value for name, value in zip(BLOCKS, structure.scopes)}
    )
    values.update(
        {
            f"dynamics:{name}": value
            for name, value in zip(BLOCKS, structure.dynamics)
        }
    )
    return MappingProxyType(values)


def _categorical_row(truth_index: int, cardinality: int, reliability: float) -> np.ndarray:
    if cardinality == 1:
        return np.ones(1)
    row = np.full(cardinality, (1.0 - reliability) / (cardinality - 1), dtype=float)
    row[truth_index] = reliability
    return row


def _sample_structure(
    seed: int,
    bounds: GrammarBounds,
    hyperparameters: GrammarHyperparameters,
    released_block: tuple[int, int] | None,
) -> tuple[GrammarStructure, list[tuple[str, int, str, int | str]]]:
    keys: list[tuple[str, int, str, int | str]] = []
    values: dict[str, Any] = {}
    for index, (field, support) in enumerate(field_supports(bounds).items()):
        keys.append(component_key(seed, f"structure:{field}", index))
        rng = component_rng(
            seed,
            f"structure:{field}",
            time_or_event=index,
            released_block=released_block,
        )
        probabilities = field_prior(field, support, hyperparameters)
        values[field] = support[int(rng.choice(len(support), p=probabilities))]
    return (
        GrammarStructure(
            active_modes=int(values["active_modes"]),
            active_contexts=int(values["active_contexts"]),
            edges=tuple(int(values[f"edge:{edge}"]) for edge in EDGES),
            scopes=tuple(str(values[f"scope:{block}"]) for block in BLOCKS),
            dynamics=tuple(str(values[f"dynamics:{block}"]) for block in BLOCKS),
        ),
        keys,
    )


def generate_world(
    seed: int,
    *,
    length: int = 12,
    bounds: GrammarBounds = GrammarBounds(),
    missingness: float = 0.0,
    hyperparameters: GrammarHyperparameters = DEFAULT_HYPERPARAMETERS,
    structure: GrammarStructure | None = None,
    released_block: tuple[int, int] | None = None,
) -> GrammarWorld:
    """Sample a world from exactly the prior and likelihood used by scoring."""
    if length < 1:
        raise ValueError("length must be positive")
    if not 0.0 <= missingness < 1.0:
        raise ValueError("missingness must be in [0, 1)")
    if structure is None:
        structure, keys = _sample_structure(
            seed, bounds, hyperparameters, released_block
        )
    else:
        keys = []
    true_values = structure_values(structure)
    observations: list[TypedObservation] = []
    log_probability = structure_log_prior(structure, bounds, hyperparameters)
    for field_index, (field, support) in enumerate(field_supports(bounds).items()):
        truth_index = support.index(true_values[field])
        row = _categorical_row(
            truth_index, len(support), hyperparameters.diagnostic_reliability
        )
        for time in range(length):
            event = field_index * length + time
            obs_key = component_key(seed, f"observation:{field}", time)
            miss_key = component_key(seed, f"missing:{field}", time)
            keys.extend((obs_key, miss_key))
            obs_rng = component_rng(
                seed,
                f"observation:{field}",
                time_or_event=time,
                released_block=released_block,
            )
            miss_rng = component_rng(
                seed,
                f"missing:{field}",
                time_or_event=time,
                released_block=released_block,
            )
            value = int(obs_rng.choice(len(support), p=row))
            missing = bool(miss_rng.random() < missingness)
            observations.append(TypedObservation(field, event, value, missing))
            if not missing:
                log_probability += math.log(float(row[value]))
    # Interventions are custody-visible but deliberately absent from likelihood.
    interventions = tuple(time % 3 for time in range(length))
    return GrammarWorld(
        seed=int(seed),
        bounds=bounds,
        structure=structure,
        observations=tuple(observations),
        interventions=interventions,
        exact_log_probability=float(log_probability),
        rng_keys=tuple(keys),
    )


def score_world(
    world: GrammarWorld,
    *,
    hyperparameters: GrammarHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> StructurePosterior:
    if any(label in ANALYSIS_LABELS for label in world.analysis_labels):
        raise ValueError("analysis labels may not reach inference")
    probabilities: dict[str, tuple[float, ...]] = {}
    supports = field_supports(world.bounds)
    log_evidence = 0.0
    for field, support in supports.items():
        log_weights = np.log(field_prior(field, support, hyperparameters))
        observations = [
            observation
            for observation in world.observations
            if observation.field == field and not observation.missing
        ]
        for candidate_index in range(len(support)):
            row = _categorical_row(
                candidate_index,
                len(support),
                hyperparameters.diagnostic_reliability,
            )
            log_weights[candidate_index] += sum(
                math.log(float(row[observation.value]))
                for observation in observations
            )
        maximum = float(np.max(log_weights))
        normalizer = maximum + math.log(float(np.exp(log_weights - maximum).sum()))
        probabilities[field] = tuple(float(v) for v in np.exp(log_weights - normalizer))
        log_evidence += normalizer
    return StructurePosterior(
        field_probabilities=MappingProxyType(probabilities),
        supports=supports,
        log_evidence=float(log_evidence),
        world_log_probability=world.exact_log_probability,
    )


def full_program_prior_sum(bounds: GrammarBounds = GrammarBounds()) -> float:
    """Exact factorized sum over all complete bounded grammar programs."""
    result = 1.0
    for field, support in field_supports(bounds).items():
        result *= float(field_prior(field, support).sum())
    return result


def local_log_scores(
    world: GrammarWorld,
    structure: GrammarStructure,
    hyperparameters: GrammarHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> Mapping[str, float]:
    values = structure_values(structure)
    result: dict[str, float] = {}
    for field, support in field_supports(world.bounds).items():
        candidate = support.index(values[field])
        row = _categorical_row(
            candidate, len(support), hyperparameters.diagnostic_reliability
        )
        result[field] = math.log(
            float(field_prior(field, support, hyperparameters)[candidate])
        ) + sum(
            math.log(float(row[o.value]))
            for o in world.observations
            if o.field == field and not o.missing
        )
    return MappingProxyType(result)


def dormant_slot_likelihood(
    world: GrammarWorld, slot_kind: str, slot_index: int
) -> float:
    """Likelihood contribution of an unused slot; exactly one by construction."""
    active = (
        world.structure.active_modes
        if slot_kind == "mode"
        else world.structure.active_contexts
    )
    if slot_index <= active:
        raise ValueError("requested slot is active")
    return 1.0


def edge_conditional_probability(
    edge_present: bool, parent: int, child: int
) -> float:
    """Small normalized fixture used to prove edge-absence independence."""
    if not edge_present:
        return 0.5
    return 0.8 if parent == child else 0.2


def compile_scope(
    scope: str, *, cue: int, context: int, mode: int
) -> tuple[str, int | None]:
    if scope == "shared_global":
        return scope, None
    if scope == "cue_specific":
        return scope, int(cue)
    if scope == "context_specific":
        return scope, int(context)
    if scope == "mode_specific":
        return scope, int(mode)
    raise ValueError("unknown scope")


def transition_matrix(dynamics: str, states: int = 3) -> np.ndarray:
    if states < 2:
        raise ValueError("states must be at least two")
    if dynamics == "static":
        return np.eye(states)
    if dynamics == "discrete_recurrent_context":
        matrix = np.full((states, states), 0.15 / (states - 1))
        np.fill_diagonal(matrix, 0.85)
        return matrix
    if dynamics == "ordered_random_walk":
        matrix = np.zeros((states, states))
        for i in range(states):
            targets = sorted(set((max(0, i - 1), i, min(states - 1, i + 1))))
            for target in targets:
                matrix[i, target] = 1.0 / len(targets)
        return matrix
    if dynamics == "one_way_change":
        matrix = np.zeros((states, states))
        for i in range(states):
            if i == states - 1:
                matrix[i, i] = 1.0
            else:
                matrix[i, i] = 0.8
                matrix[i, i + 1] = 0.2
        return matrix
    raise ValueError("unknown dynamics")


def delete_production(world: GrammarWorld, production: str) -> GrammarWorld:
    """Return a lesion fixture with only the named production evidence removed."""
    if production == "mode_slots":
        prefixes = ("active_modes",)
    elif production == "context_slots":
        prefixes = ("active_contexts",)
    elif production == "edges":
        prefixes = ("edge:",)
    elif production == "scopes":
        prefixes = ("scope:",)
    elif production == "dynamics":
        prefixes = ("dynamics:",)
    else:
        raise ValueError("unknown production")
    observations = tuple(
        observation
        for observation in world.observations
        if not any(observation.field.startswith(prefix) for prefix in prefixes)
    )
    return GrammarWorld(
        world.seed,
        world.bounds,
        world.structure,
        observations,
        world.interventions,
        world.exact_log_probability,
        world.rng_keys,
        world.analysis_labels,
    )


def enumerate_programs(bounds: GrammarBounds) -> Sequence[GrammarStructure]:
    """Materialize programs only for deliberately reduced oracle fixtures."""
    programs = []
    supports = field_supports(bounds)
    for values in itertools.product(*supports.values()):
        mapping = dict(zip(supports, values))
        programs.append(
            GrammarStructure(
                int(mapping["active_modes"]),
                int(mapping["active_contexts"]),
                tuple(int(mapping[f"edge:{edge}"]) for edge in EDGES),
                tuple(str(mapping[f"scope:{block}"]) for block in BLOCKS),
                tuple(str(mapping[f"dynamics:{block}"]) for block in BLOCKS),
            )
        )
    return tuple(programs)
