"""V3.2 SPLIT: exact temporal scope, redescription, and retention.

The scientific posterior ranges over ordinary context-count, parameter-scope,
and temporal-dynamics productions.  Static, cue-local, recurrent-context,
drift, and one-way-change descriptions are pure posterior-region readouts.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Sequence

import numpy as np


STAGE_VERSION = "V3.2"
DEVELOPMENT_BLOCK = (3_200_000, 3_229_999)
BLOCKS = ("cue_emission", "outcome_emission")
SCOPES = ("shared_global", "cue_specific", "context_specific")
DYNAMICS = (
    "static",
    "discrete_recurrent_context",
    "ordered_random_walk",
    "one_way_change",
)
ANALYSIS_LABELS = frozenset(
    {
        "split",
        "redescribed",
        "then",
        "now",
        "static_family",
        "cue_local_family",
        "recurrent_family",
        "drift_family",
        "change_family",
    }
)


@dataclass(frozen=True)
class TemporalStructure:
    active_contexts: int
    scopes: tuple[str, str]
    dynamics: tuple[str, str]

    def __post_init__(self) -> None:
        if self.active_contexts not in (1, 2, 3):
            raise ValueError("active_contexts must be in [1, 3]")
        if len(self.scopes) != 2 or any(scope not in SCOPES for scope in self.scopes):
            raise ValueError("two valid generic scopes are required")
        if len(self.dynamics) != 2 or any(
            dynamics not in DYNAMICS for dynamics in self.dynamics
        ):
            raise ValueError("two valid generic dynamics are required")


@dataclass(frozen=True)
class TemporalHyperparameters:
    diagnostic_reliability: float = 0.74
    code_length_scale: float = 1.0
    emission_floor: float = 0.08

    def __post_init__(self) -> None:
        if not 0.5 < self.diagnostic_reliability < 1.0:
            raise ValueError("diagnostic_reliability must be in (0.5, 1)")
        if self.code_length_scale <= 0:
            raise ValueError("code_length_scale must be positive")
        if not 0.0 < self.emission_floor < 0.25:
            raise ValueError("emission_floor must be in (0, .25)")


DEFAULT_HYPERPARAMETERS = TemporalHyperparameters()


@dataclass(frozen=True)
class TemporalSlice:
    time: int
    cue: int
    context: int
    block: str
    value: int
    root_value: int
    active_context_token: int
    scope_token: int
    dynamics_token: int
    missing: bool = False


@dataclass(frozen=True)
class TemporalWorld:
    seed: int
    structure: TemporalStructure
    length: int
    cue_count: int
    slices: tuple[TemporalSlice, ...]
    exact_log_probability: float
    rng_keys: tuple[tuple[str, int, str, int | str], ...]
    analysis_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class TemporalPosterior:
    programs: tuple[TemporalStructure, ...]
    probabilities: tuple[float, ...]
    log_evidence: float
    active_context_probabilities: tuple[float, float, float]
    scope_probabilities: Mapping[str, Mapping[str, float]]
    dynamics_probabilities: Mapping[str, Mapping[str, float]]
    parameter_means: Mapping[str, Mapping[str, float]]
    root_means: Mapping[int, float]

    def structure_probability(self, structure: TemporalStructure) -> float:
        return self.probabilities[self.programs.index(structure)]

    def scope_probability(self, block: str, scope: str) -> float:
        return self.scope_probabilities[block][scope]

    def dynamics_probability(self, block: str, dynamics: str) -> float:
        return self.dynamics_probabilities[block][dynamics]

    def parameter_mean(self, block: str, context: int, cue: int) -> float:
        return self.parameter_means[block][f"context:{context}:cue:{cue}"]


def enumerate_programs() -> tuple[TemporalStructure, ...]:
    return tuple(
        TemporalStructure(active, scopes, dynamics)
        for active in (1, 2, 3)
        for scopes in itertools.product(SCOPES, repeat=2)
        for dynamics in itertools.product(DYNAMICS, repeat=2)
    )


PROGRAMS = enumerate_programs()


def structure_space_size() -> int:
    return len(PROGRAMS)


def _cost(value: Any) -> float:
    if isinstance(value, int):
        return float(value)
    if value in {"shared_global", "static"}:
        return 1.0
    return 3.0


def _prior(
    support: Sequence[Any],
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> np.ndarray:
    weights = np.exp2(
        -hyperparameters.code_length_scale
        * np.asarray([_cost(value) for value in support], dtype=float)
    )
    return weights / weights.sum()


def structure_log_prior(
    structure: TemporalStructure,
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    values = (
        structure.active_contexts,
        *structure.scopes,
        *structure.dynamics,
    )
    supports = ((1, 2, 3), SCOPES, SCOPES, DYNAMICS, DYNAMICS)
    return math.fsum(
        math.log(float(_prior(support, hyperparameters)[support.index(value)]))
        for support, value in zip(supports, values)
    )


def full_prior_sum(
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    return float(
        _prior((1, 2, 3), hyperparameters).sum()
        * _prior(SCOPES, hyperparameters).sum() ** 2
        * _prior(DYNAMICS, hyperparameters).sum() ** 2
    )


def _rng(
    seed: int,
    component: str,
    event: int | str,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> np.random.Generator:
    block = DEVELOPMENT_BLOCK if released_block is None else released_block
    start, end = block
    if not start <= int(seed) <= end:
        raise ValueError("seed is outside the authorized V3.2 block")
    key = (STAGE_VERSION, int(seed), str(component), event)
    keys.append(key)
    digest = hashlib.sha256(repr(key).encode("utf-8")).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _categorical_probability(
    observed: int, truth: int, cardinality: int, reliability: float
) -> float:
    if observed == truth:
        return reliability
    return (1.0 - reliability) / (cardinality - 1)


def _scope_probability(scope: str, cue: int, context: int) -> float:
    if scope == "shared_global":
        return 0.5
    if scope == "cue_specific":
        return 0.22 if cue % 2 == 0 else 0.78
    return (0.18, 0.82, 0.5)[context]


def _dynamics_probability(
    dynamics: str, time: int, length: int, context: int
) -> float:
    if dynamics == "static":
        return 0.5
    if dynamics == "discrete_recurrent_context":
        return (0.2, 0.8, 0.5)[context]
    if dynamics == "ordered_random_walk":
        fraction = time / max(1, length - 1)
        return 0.18 + 0.64 * fraction
    return 0.18 if time < length // 2 else 0.82


def emission_probability(
    scope: str,
    dynamics: str,
    *,
    cue: int,
    context: int,
    time: int,
    length: int,
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    scope_probability = _scope_probability(scope, cue, context)
    dynamics_probability = _dynamics_probability(
        dynamics, time, length, context
    )
    combined = 0.5 + (scope_probability - 0.5) + (
        dynamics_probability - 0.5
    )
    floor = hyperparameters.emission_floor
    return float(np.clip(combined, floor, 1.0 - floor))


def context_path(
    structure: TemporalStructure, length: int, evidence_style: str = "natural"
) -> tuple[int, ...]:
    if evidence_style not in {"natural", "witnessing", "shuffled", "single_regime"}:
        raise ValueError("unknown evidence style")
    if evidence_style == "single_regime" or structure.active_contexts == 1:
        return (0,) * length
    if evidence_style == "witnessing":
        boundary = max(1, length // 3)
        return tuple(0 if time < boundary else 1 for time in range(length))
    if "discrete_recurrent_context" in structure.dynamics:
        return tuple((time // 4) % structure.active_contexts for time in range(length))
    if "one_way_change" in structure.dynamics:
        return tuple(
            0 if time < length // 2 else min(1, structure.active_contexts - 1)
            for time in range(length)
        )
    return tuple(time % structure.active_contexts for time in range(length))


def _sample_structure(
    seed: int,
    hyperparameters: TemporalHyperparameters,
    released_block: tuple[int, int] | None,
    keys: list[tuple[str, int, str, int | str]],
) -> TemporalStructure:
    supports: tuple[Sequence[Any], ...] = (
        (1, 2, 3),
        SCOPES,
        SCOPES,
        DYNAMICS,
        DYNAMICS,
    )
    components = (
        "active_contexts",
        "scope:cue_emission",
        "scope:outcome_emission",
        "dynamics:cue_emission",
        "dynamics:outcome_emission",
    )
    values = []
    for index, (support, component) in enumerate(zip(supports, components)):
        rng = _rng(seed, f"structure:{component}", index, released_block, keys)
        values.append(
            support[int(rng.choice(len(support), p=_prior(support, hyperparameters)))]
        )
    return TemporalStructure(
        int(values[0]),
        (str(values[1]), str(values[2])),
        (str(values[3]), str(values[4])),
    )


def generate_world(
    seed: int,
    *,
    structure: TemporalStructure | None = None,
    length: int = 48,
    cue_count: int = 3,
    missingness: float = 0.0,
    evidence_style: str = "natural",
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
    released_block: tuple[int, int] | None = None,
) -> TemporalWorld:
    if length < 2 or cue_count < 2:
        raise ValueError("length and cue_count are below V3.2 bounds")
    if not 0.0 <= missingness < 1.0:
        raise ValueError("missingness must be in [0, 1)")
    keys: list[tuple[str, int, str, int | str]] = []
    if structure is None:
        structure = _sample_structure(
            seed, hyperparameters, released_block, keys
        )
    path = context_path(structure, length, evidence_style)
    slices = []
    log_probability = structure_log_prior(structure, hyperparameters)
    for time, context in enumerate(path):
        for cue in range(cue_count):
            for block_index, block in enumerate(BLOCKS):
                event = time * cue_count * len(BLOCKS) + cue * len(BLOCKS) + block_index
                scope = structure.scopes[block_index]
                dynamics = structure.dynamics[block_index]
                probability = emission_probability(
                    scope,
                    dynamics,
                    cue=cue,
                    context=context,
                    time=time,
                    length=length,
                    hyperparameters=hyperparameters,
                )
                value_rng = _rng(seed, f"value:{block}", event, released_block, keys)
                root_rng = _rng(seed, f"root:{block}", event, released_block, keys)
                active_rng = _rng(seed, f"token:active:{block}", event, released_block, keys)
                scope_rng = _rng(seed, f"token:scope:{block}", event, released_block, keys)
                dynamics_rng = _rng(
                    seed, f"token:dynamics:{block}", event, released_block, keys
                )
                missing_rng = _rng(seed, f"missing:{block}", event, released_block, keys)
                value = int(value_rng.random() < probability)
                root_probability = (
                    _scope_probability(scope, cue, context)
                    if scope == "context_specific"
                    else 0.5
                )
                root_value = int(root_rng.random() < root_probability)
                active_truth = structure.active_contexts - 1
                scope_truth = SCOPES.index(scope)
                dynamics_truth = DYNAMICS.index(dynamics)
                reliability = hyperparameters.diagnostic_reliability
                active_row = np.asarray(
                    [
                        _categorical_probability(i, active_truth, 3, reliability)
                        for i in range(3)
                    ]
                )
                diagnostic = time == 0 and cue == 0
                scope_row = np.asarray(
                    [
                        (
                            _categorical_probability(i, scope_truth, 3, reliability)
                            if diagnostic
                            else 1.0 / 3.0
                        )
                        for i in range(3)
                    ]
                )
                dynamics_row = np.asarray(
                    [
                        (
                            _categorical_probability(
                                i, dynamics_truth, 4, reliability
                            )
                            if diagnostic
                            else 1.0 / 4.0
                        )
                        for i in range(4)
                    ]
                )
                active_token = int(active_rng.choice(3, p=active_row))
                scope_token = int(scope_rng.choice(3, p=scope_row))
                dynamics_token = int(dynamics_rng.choice(4, p=dynamics_row))
                missing = bool(missing_rng.random() < missingness)
                slices.append(
                    TemporalSlice(
                        time,
                        cue,
                        context,
                        block,
                        value,
                        root_value,
                        active_token,
                        scope_token,
                        dynamics_token,
                        missing,
                    )
                )
                if not missing:
                    log_probability += math.log(
                        probability if value else 1.0 - probability
                    )
                    log_probability += math.log(
                        root_probability if root_value else 1.0 - root_probability
                    )
                    log_probability += math.log(active_row[active_token])
                    log_probability += math.log(scope_row[scope_token])
                    log_probability += math.log(dynamics_row[dynamics_token])
    return TemporalWorld(
        int(seed),
        structure,
        int(length),
        int(cue_count),
        tuple(slices),
        float(log_probability),
        tuple(keys),
    )


def _candidate_log_likelihood(
    world: TemporalWorld,
    active_contexts: int,
    block: str,
    scope: str,
    dynamics: str,
    hyperparameters: TemporalHyperparameters,
    *,
    mask_active_channel: bool = False,
    mask_scope_channel: bool = False,
    mask_dynamics_channel: bool = False,
) -> float:
    block_index = BLOCKS.index(block)
    reliability = hyperparameters.diagnostic_reliability
    total = 0.0
    for item in world.slices:
        if item.block != block or item.missing:
            continue
        probability = emission_probability(
            scope,
            dynamics,
            cue=item.cue,
            context=item.context,
            time=item.time,
            length=world.length,
            hyperparameters=hyperparameters,
        )
        total += math.log(probability if item.value else 1.0 - probability)
        root_probability = (
            _scope_probability(scope, item.cue, item.context)
            if scope == "context_specific"
            else 0.5
        )
        total += math.log(
            root_probability if item.root_value else 1.0 - root_probability
        )
        if not mask_active_channel:
            total += math.log(
                _categorical_probability(
                    item.active_context_token,
                    active_contexts - 1,
                    3,
                    reliability,
                )
            )
        diagnostic_reliability = (
            reliability if item.time == 0 and item.cue == 0 else 1.0 / 3.0
        )
        if not mask_scope_channel:
            total += math.log(
                (
                    _categorical_probability(
                        item.scope_token,
                        SCOPES.index(scope),
                        3,
                        diagnostic_reliability,
                    )
                    if item.time == 0 and item.cue == 0
                    else 1.0 / 3.0
                )
            )
        if not mask_dynamics_channel:
            total += math.log(
                (
                    _categorical_probability(
                        item.dynamics_token,
                        DYNAMICS.index(dynamics),
                        4,
                        reliability,
                    )
                    if item.time == 0 and item.cue == 0
                    else 1.0 / 4.0
                )
            )
    return total


def _parameter_means(world: TemporalWorld) -> Mapping[str, Mapping[str, float]]:
    result: dict[str, Mapping[str, float]] = {}
    for block in BLOCKS:
        values: dict[str, float] = {}
        for context in range(3):
            for cue in range(world.cue_count):
                observed = [
                    item.value
                    for item in world.slices
                    if item.block == block
                    and item.context == context
                    and item.cue == cue
                    and not item.missing
                ]
                values[f"context:{context}:cue:{cue}"] = (
                    (sum(observed) + 0.5) / (len(observed) + 1.0)
                )
        result[block] = MappingProxyType(values)
    return MappingProxyType(result)


def _root_means(world: TemporalWorld) -> Mapping[int, float]:
    values = {}
    for context in range(3):
        observed = [
            item.root_value
            for item in world.slices
            if item.context == context and not item.missing
        ]
        values[context] = (sum(observed) + 0.5) / (len(observed) + 1.0)
    return MappingProxyType(values)


def score_world(
    world: TemporalWorld,
    *,
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
    restrictions: Mapping[str, tuple[Any, ...]] | None = None,
    masked_channels: frozenset[str] = frozenset(),
) -> TemporalPosterior:
    if any(label in ANALYSIS_LABELS for label in world.analysis_labels):
        raise ValueError("analysis labels may not reach V3.2 inference")
    restrictions = {} if restrictions is None else dict(restrictions)
    active_support = restrictions.get("active_contexts", (1, 2, 3))
    scope_supports = {
        block: restrictions.get(f"scope:{block}", SCOPES) for block in BLOCKS
    }
    dynamics_supports = {
        block: restrictions.get(f"dynamics:{block}", DYNAMICS) for block in BLOCKS
    }
    active_scores = {}
    for active in active_support:
        prior = _prior((1, 2, 3), hyperparameters)[active - 1]
        score = math.log(float(prior))
        for block in BLOCKS:
            score += _candidate_log_likelihood(
                world,
                active,
                block,
                "shared_global",
                "static",
                hyperparameters,
                mask_active_channel="active_contexts" in masked_channels,
                mask_scope_channel=True,
                mask_dynamics_channel=True,
            )
            # Remove value/root terms inserted by the helper; retain only tokens.
            score -= _candidate_log_likelihood(
                world,
                active,
                block,
                "shared_global",
                "static",
                hyperparameters,
                mask_active_channel=True,
                mask_scope_channel=True,
                mask_dynamics_channel=True,
            )
        active_scores[active] = score
    block_scores: dict[str, dict[tuple[str, str], float]] = {}
    for block in BLOCKS:
        scores = {}
        for scope in scope_supports[block]:
            for dynamics in dynamics_supports[block]:
                score = math.log(
                    float(_prior(SCOPES, hyperparameters)[SCOPES.index(scope)])
                )
                score += math.log(
                    float(
                        _prior(DYNAMICS, hyperparameters)[
                            DYNAMICS.index(dynamics)
                        ]
                    )
                )
                score += _candidate_log_likelihood(
                    world,
                    1,
                    block,
                    scope,
                    dynamics,
                    hyperparameters,
                    mask_active_channel=True,
                    mask_scope_channel=f"scope:{block}" in masked_channels,
                    mask_dynamics_channel=f"dynamics:{block}" in masked_channels,
                )
                scores[(scope, dynamics)] = score
        block_scores[block] = scores

    active_normalizer = _logsumexp(tuple(active_scores.values()))
    block_normalizers = {
        block: _logsumexp(tuple(scores.values()))
        for block, scores in block_scores.items()
    }
    programs = []
    log_weights = []
    for active in active_support:
        for cue_key in block_scores[BLOCKS[0]]:
            for outcome_key in block_scores[BLOCKS[1]]:
                programs.append(
                    TemporalStructure(
                        int(active),
                        (cue_key[0], outcome_key[0]),
                        (cue_key[1], outcome_key[1]),
                    )
                )
                log_weights.append(
                    active_scores[active]
                    + block_scores[BLOCKS[0]][cue_key]
                    + block_scores[BLOCKS[1]][outcome_key]
                )
    normalizer = _logsumexp(tuple(log_weights))
    probabilities = tuple(math.exp(value - normalizer) for value in log_weights)
    active_probabilities = tuple(
        math.exp(active_scores.get(active, -math.inf) - active_normalizer)
        for active in (1, 2, 3)
    )
    scope_probabilities = {}
    dynamics_probabilities = {}
    for block, scores in block_scores.items():
        block_normalizer = block_normalizers[block]
        scope_probabilities[block] = MappingProxyType(
            {
                scope: math.fsum(
                    math.exp(score - block_normalizer)
                    for (candidate_scope, _), score in scores.items()
                    if candidate_scope == scope
                )
                for scope in SCOPES
            }
        )
        dynamics_probabilities[block] = MappingProxyType(
            {
                dynamics: math.fsum(
                    math.exp(score - block_normalizer)
                    for (_, candidate_dynamics), score in scores.items()
                    if candidate_dynamics == dynamics
                )
                for dynamics in DYNAMICS
            }
        )
    return TemporalPosterior(
        tuple(programs),
        probabilities,
        float(normalizer),
        active_probabilities,
        MappingProxyType(scope_probabilities),
        MappingProxyType(dynamics_probabilities),
        _parameter_means(world),
        _root_means(world),
    )


def _logsumexp(values: Sequence[float]) -> float:
    maximum = max(values)
    return maximum + math.log(math.fsum(math.exp(value - maximum) for value in values))


def region_probabilities(
    posterior: TemporalPosterior, block: str = "cue_emission"
) -> Mapping[str, float]:
    scope = posterior.scope_probabilities[block]
    dynamics = posterior.dynamics_probabilities[block]
    return MappingProxyType(
        {
            "static": scope["shared_global"] * dynamics["static"],
            "cue_local": scope["cue_specific"] * dynamics["static"],
            "recurrent_context": (
                scope["context_specific"]
                * dynamics["discrete_recurrent_context"]
            ),
            "continuous_drift": dynamics["ordered_random_walk"],
            "one_way_change": dynamics["one_way_change"],
        }
    )


def scope_bayes_factor(
    posterior: TemporalPosterior,
    block: str,
    numerator: str = "context_specific",
    denominator: str = "shared_global",
    hyperparameters: TemporalHyperparameters = DEFAULT_HYPERPARAMETERS,
) -> float:
    probabilities = posterior.scope_probabilities[block]
    prior = _prior(SCOPES, hyperparameters)
    posterior_odds = probabilities[numerator] / probabilities[denominator]
    prior_odds = prior[SCOPES.index(numerator)] / prior[SCOPES.index(denominator)]
    return float(posterior_odds / prior_odds)


def redescription_readouts(
    posterior: TemporalPosterior,
    *,
    block: str = "cue_emission",
    material_probability: float = 0.8,
    material_bf: float = 4.0,
) -> Mapping[str, Any]:
    context_probability = posterior.scope_probability(block, "context_specific")
    recurrence_probability = posterior.dynamics_probability(
        block, "discrete_recurrent_context"
    )
    bayes_factor = scope_bayes_factor(posterior, block)
    raw = context_probability == max(posterior.scope_probabilities[block].values())
    material = (
        context_probability >= material_probability
        and bayes_factor >= material_bf
        and posterior.active_context_probabilities[1]
        + posterior.active_context_probabilities[2]
        >= material_probability
    )
    return MappingProxyType(
        {
            "raw": bool(raw),
            "material": bool(material),
            "selective": bool(material and recurrence_probability >= material_probability),
            "context_probability": float(context_probability),
            "recurrence_probability": float(recurrence_probability),
            "scope_bayes_factor": float(bayes_factor),
        }
    )


def historical_prediction(
    posterior: TemporalPosterior, block: str, context: int, cue: int
) -> float:
    return posterior.parameter_mean(block, context, cue)


def present_context_transfer(
    posterior: TemporalPosterior,
    *,
    context: int,
    association_strength: float = 1.0,
    fixed_g: bool = False,
) -> float:
    if fixed_g or association_strength == 0.0:
        return 0.0
    context_probability = posterior.scope_probability(
        "cue_emission", "context_specific"
    )
    root_revision = abs(posterior.root_means[context] - 0.5)
    return float(context_probability * association_strength * root_revision)


def masked_slice_log_bf(
    world: TemporalWorld,
    before: int,
    after: int,
    structure_a: TemporalStructure,
    structure_b: TemporalStructure,
) -> float:
    selected = [
        item for item in world.slices if before <= item.time < after and item.missing
    ]
    if not selected:
        return 0.0
    return 0.0
