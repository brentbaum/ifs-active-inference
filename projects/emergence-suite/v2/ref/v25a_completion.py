"""V2.5a master-spec configural-coupling reference.

The completion layer is a finite exact model over five atomic channels.
Independent and coupled candidates share identical one-channel marginals.
Only a normalized joint episode can carry evidence about the exact
spike-and-slab structural variable.  All reported effects are posterior
quantities or pure readouts; presentation labels never enter inference.
"""

from __future__ import annotations

import functools
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Iterable, Sequence

import numpy as np

from .audit import ProtocolState, audit_one_posterior
from .rng import component_rng


ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = json.loads(
    (ROOT / "protocols" / "v2.5a-completion-parameters.json").read_text()
)
CHANNELS = ("S", "W", "Pi", "Y", "C")
ATOMS = tuple(itertools.product((0, 1), repeat=len(CHANNELS)))
ATOM_ARRAY = np.asarray(ATOMS, dtype=int)
KAPPA_GRID = tuple(float(x) for x in PARAMETERS["kappa_grid"])
KAPPA_PRIOR = np.asarray(PARAMETERS["kappa_prior"], dtype=float)
STRUCTURE_PRIOR = np.asarray(
    [
        PARAMETERS["candidate_prior"]["independent"],
        PARAMETERS["candidate_prior"]["coupled"],
    ],
    dtype=float,
)
ROOT_PRIOR = np.asarray(PARAMETERS["root_prior"], dtype=float)
TOLERANCE = float(PARAMETERS["semantic_tolerance"])
EPOCH_B_DEVELOPMENT_BLOCK = (1_000_000, 1_899_999)


@dataclass(frozen=True)
class Episode:
    cue: int
    context: int
    values: tuple[int | None, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(CHANNELS):
            raise ValueError("episode must contain five atomic channels")
        if any(value not in (0, 1, None) for value in self.values):
            raise ValueError("episode channels are binary or missing")


@dataclass(frozen=True)
class ConfiguralWorld:
    seed: int
    truth_structure: str
    truth_kappa: float
    truth_root: int
    context_regime: str
    episodes: tuple[Episode, ...]


@dataclass(frozen=True)
class ConfiguralScore:
    q_structure: np.ndarray
    q_root: np.ndarray
    q_interaction: np.ndarray
    q_kappa_given_coupled: np.ndarray
    joint_log_evidence: float
    marginal_log_evidence: float
    log_evidence_by_structure: np.ndarray
    atomic_budget_joint: float
    atomic_budget_marginal: float
    interaction_log_contribution: float
    per_slice_log_bf: tuple[float, ...]
    heldout_joint_log_predictive: float | None
    state: ProtocolState


def _logsumexp(values: np.ndarray) -> float:
    array = np.asarray(values, dtype=float)
    maximum = float(np.max(array))
    return maximum + math.log(float(np.exp(array - maximum).sum()))


def _softmax(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    shifted = array - float(np.max(array))
    weights = np.exp(shifted)
    return weights / weights.sum()


def _development_rng(seed: int, component: str) -> np.random.Generator:
    """Use only the master spec's public Epoch-B development namespace."""
    return component_rng(
        seed, component, released_block=EPOCH_B_DEVELOPMENT_BLOCK
    )


def channel_marginals(cue: int, context: int) -> tuple[float, ...]:
    """Frozen one-channel P(value=1) coordinates.

    These are deliberately independent of H_cfg, kappa, and G.  Context and
    cue can alter atomic evidence without leaking structural or root evidence
    into the marginal presentation.
    """
    template = int(cue) % 4
    ctx = int(context)
    return (
        (0.28, 0.42, 0.58, 0.72)[template],
        0.35 + 0.30 * ctx,
        (0.40, 0.55, 0.45, 0.60)[template],
        0.30 + 0.35 * ctx,
        (0.46, 0.54, 0.50, 0.58)[template],
    )


def product_table(marginals: Sequence[float]) -> np.ndarray:
    probabilities = np.ones(len(ATOMS), dtype=float)
    for axis, probability in enumerate(marginals):
        probabilities *= np.where(
            ATOM_ARRAY[:, axis] == 1, probability, 1.0 - probability
        )
    return probabilities / probabilities.sum()


def _interaction_sign(root: int) -> np.ndarray:
    parity = np.where(ATOM_ARRAY.sum(axis=1) % 2 == 0, 1.0, -1.0)
    return parity if int(root) == 1 else -parity


@functools.lru_cache(maxsize=None)
def joint_table(
    cue: int, context: int, root: int, kappa: float
) -> np.ndarray:
    """Normalized joint table with exact frozen one-channel marginals."""
    marginals = channel_marginals(cue, context)
    base = product_table(marginals)
    if float(kappa) == 0.0:
        output = base
    else:
        output = base * np.exp(float(kappa) * _interaction_sign(root))
        output /= output.sum()
        tolerance = float(PARAMETERS["ipf_tolerance"])
        for _ in range(int(PARAMETERS["ipf_max_iterations"])):
            for axis, target_one in enumerate(marginals):
                mask = ATOM_ARRAY[:, axis] == 1
                current_one = float(output[mask].sum())
                output[mask] *= target_one / current_one
                current_zero = float(output[~mask].sum())
                output[~mask] *= (1.0 - target_one) / current_zero
                output /= output.sum()
            errors = [
                abs(float(output[ATOM_ARRAY[:, axis] == 1].sum()) - target)
                for axis, target in enumerate(marginals)
            ]
            if max(errors) <= tolerance:
                break
        else:
            raise RuntimeError("IPF did not converge")
    output = np.asarray(output / output.sum(), dtype=float)
    output.setflags(write=False)
    return output


def table_marginals(table: np.ndarray) -> np.ndarray:
    return np.asarray(
        [
            float(np.asarray(table)[ATOM_ARRAY[:, axis] == 1].sum())
            for axis in range(len(CHANNELS))
        ]
    )


def _episode_probability(table: np.ndarray, values: Sequence[int | None]) -> float:
    mask = np.ones(len(ATOMS), dtype=bool)
    for axis, value in enumerate(values):
        if value is not None:
            mask &= ATOM_ARRAY[:, axis] == int(value)
    return float(np.asarray(table)[mask].sum())


def atomic_probability(
    cue: int, context: int, values: Sequence[int | None]
) -> float:
    marginals = channel_marginals(cue, context)
    result = 1.0
    for probability, value in zip(marginals, values):
        if value is not None:
            result *= probability if value == 1 else 1.0 - probability
    return float(result)


def context_path(length: int, regime: str) -> tuple[int, ...]:
    if regime == "single":
        return (0,) * int(length)
    if regime == "return":
        block = max(2, int(length) // 6)
        return tuple((index // block) % 2 for index in range(int(length)))
    raise ValueError("unknown context regime")


def generate_world(
    seed: int,
    *,
    truth_structure: str,
    interaction: str,
    context_regime: str,
    length: int,
    cue_count: int = 3,
    missingness: float | None = None,
) -> ConfiguralWorld:
    """Generate from every exact candidate using deterministic streams."""
    if truth_structure not in {"independent", "coupled"}:
        raise ValueError("unknown structure")
    if interaction not in PARAMETERS["interaction_labels"]:
        raise ValueError("unknown interaction label")
    kappa = (
        0.0
        if truth_structure == "independent"
        else float(PARAMETERS["interaction_labels"][interaction])
    )
    missing = float(
        PARAMETERS["primary_missingness"]
        if missingness is None
        else missingness
    )
    root = int(_development_rng(seed, "v25a-completion-root").integers(0, 2))
    offset = int(
        _development_rng(seed, "v25a-completion-cue-offset").integers(0, cue_count)
    )
    episodes: list[Episode] = []
    for time, context in enumerate(context_path(length, context_regime)):
        cue = (time + offset) % int(cue_count)
        table = joint_table(cue, context, root, kappa)
        rng = _development_rng(seed, f"v25a-completion-episode-{time}")
        atom = ATOMS[int(rng.choice(len(ATOMS), p=table))]
        values: list[int | None] = [int(value) for value in atom]
        for axis in range(len(values)):
            if rng.random() < missing:
                values[axis] = None
        episodes.append(Episode(cue, context, tuple(values)))
    return ConfiguralWorld(
        seed=int(seed),
        truth_structure=truth_structure,
        truth_kappa=kappa,
        truth_root=root,
        context_regime=context_regime,
        episodes=tuple(episodes),
    )


def _component_log_likelihood(
    episodes: Sequence[Episode], root: int, kappa: float, presentation: str
) -> tuple[float, tuple[float, ...]]:
    increments: list[float] = []
    for episode in episodes:
        if presentation == "joint":
            probability = _episode_probability(
                joint_table(episode.cue, episode.context, root, kappa),
                episode.values,
            )
        elif presentation == "marginal":
            probability = atomic_probability(
                episode.cue, episode.context, episode.values
            )
        else:
            raise ValueError("presentation must be joint or marginal")
        increments.append(math.log(probability))
    return float(sum(increments)), tuple(increments)


def score(
    episodes: Iterable[Episode],
    *,
    presentation: str,
    heldout: Iterable[Episode] | None = None,
) -> ConfiguralScore:
    sequence = tuple(episodes)
    # Components are (H=independent,k=0,G=0/1), then slab kappa x G.
    components: list[tuple[int, float, int, float]] = []
    for root in (0, 1):
        components.append((0, 0.0, root, STRUCTURE_PRIOR[0] * ROOT_PRIOR[root]))
    for index, kappa in enumerate(KAPPA_GRID):
        for root in (0, 1):
            components.append(
                (
                    1,
                    kappa,
                    root,
                    STRUCTURE_PRIOR[1] * KAPPA_PRIOR[index] * ROOT_PRIOR[root],
                )
            )
    component_logs = []
    component_slices = []
    for _, kappa, root, prior in components:
        total, slices = _component_log_likelihood(
            sequence, root, kappa, presentation
        )
        component_logs.append(math.log(prior) + total)
        component_slices.append(slices)
    log_joint = np.asarray(component_logs)
    q_components = _softmax(log_joint)
    evidence = _logsumexp(log_joint)
    q_structure = np.asarray(
        [
            sum(q for q, component in zip(q_components, components) if component[0] == h)
            for h in (0, 1)
        ]
    )
    q_root = np.asarray(
        [
            sum(q for q, component in zip(q_components, components) if component[2] == g)
            for g in (0, 1)
        ]
    )
    coupled_mass = float(q_structure[1])
    q_kappa = np.asarray(
        [
            sum(
                q
                for q, component in zip(q_components, components)
                if component[0] == 1 and component[1] == kappa
            )
            / coupled_mass
            for kappa in KAPPA_GRID
        ]
    )
    q_interaction = np.concatenate(
        (np.asarray([q_structure[0]]), q_structure[1] * q_kappa)
    )
    independent_logs = log_joint[:2]
    coupled_logs = log_joint[2:]
    log_by_structure = np.asarray(
        [
            _logsumexp(independent_logs) - math.log(STRUCTURE_PRIOR[0]),
            _logsumexp(coupled_logs) - math.log(STRUCTURE_PRIOR[1]),
        ]
    )
    per_slice_log_bf = []
    q0 = np.asarray([0.5, 0.5])
    q1 = np.full(2 * len(KAPPA_GRID), 1.0 / (2 * len(KAPPA_GRID)))
    for time in range(len(sequence)):
        pred0 = sum(
            q0[index] * math.exp(component_slices[index][time])
            for index in range(2)
        )
        pred1 = sum(
            q1[index] * math.exp(component_slices[index + 2][time])
            for index in range(len(q1))
        )
        per_slice_log_bf.append(math.log(pred1) - math.log(pred0))
        q0 *= np.asarray(
            [math.exp(component_slices[index][time]) for index in range(2)]
        )
        q0 /= q0.sum()
        q1 *= np.asarray(
            [
                math.exp(component_slices[index + 2][time])
                for index in range(len(q1))
            ]
        )
        q1 /= q1.sum()

    atomic_budget = float(
        sum(
            math.log(
                atomic_probability(ep.cue, ep.context, ep.values)
            )
            for ep in sequence
        )
    )
    marginal_component_logs = np.log(
        np.asarray([component[3] for component in components])
    ) + atomic_budget
    marginal_evidence = _logsumexp(marginal_component_logs)
    heldout_score = None
    if heldout is not None:
        heldout_sequence = tuple(heldout)
        heldout_component_ll = np.asarray(
            [
                _component_log_likelihood(
                    heldout_sequence, root, kappa, presentation
                )[0]
                for _, kappa, root, _ in components
            ]
        )
        heldout_score = _logsumexp(
            np.log(q_components) + heldout_component_ll
        )
    state = ProtocolState(
        posterior_store={
            "H_cfg": q_structure.copy(),
            "G": q_root.copy(),
        },
        parameter_posterior_store={"kappa": q_interaction.copy()},
        evidence_store={
            "independent": math.exp(max(float(log_by_structure[0]), -700.0)),
            "coupled": math.exp(max(float(log_by_structure[1]), -700.0)),
        },
        metadata=MappingProxyType(
            {"stage": "V2.5a-completion", "presentation": presentation}
        ),
    )
    audit_one_posterior(state)
    return ConfiguralScore(
        q_structure=q_structure,
        q_root=q_root,
        q_interaction=q_interaction,
        q_kappa_given_coupled=q_kappa,
        joint_log_evidence=float(evidence),
        marginal_log_evidence=float(marginal_evidence),
        log_evidence_by_structure=log_by_structure,
        atomic_budget_joint=atomic_budget,
        atomic_budget_marginal=atomic_budget,
        interaction_log_contribution=float(evidence - marginal_evidence),
        per_slice_log_bf=tuple(per_slice_log_bf),
        heldout_joint_log_predictive=heldout_score,
        state=state,
    )


def root_change(result: ConfiguralScore) -> float:
    return float(result.q_root[1] - ROOT_PRIOR[1])


def untreated_transfer(result: ConfiguralScore, *, association: float | None = None) -> float:
    strength = float(
        PARAMETERS["association_strength"] if association is None else association
    )
    return strength * root_change(result)


def shuffled_episodes(
    episodes: Sequence[Episode], seed: int
) -> tuple[Episode, ...]:
    """Destroy episode membership within frozen cue/context coordinates.

    Conditioning the permutation on the coordinates used by the marginal
    tables preserves the exact atomic null.  A global permutation would mix
    distinct cue/context marginals and manufacture a new dependence.
    """
    sequence = tuple(episodes)
    output = [list(episode.values) for episode in sequence]
    groups: dict[tuple[int, int], list[int]] = {}
    for index, episode in enumerate(sequence):
        groups.setdefault((episode.cue, episode.context), []).append(index)
    for (cue, context), indices in sorted(groups.items()):
        for axis in range(len(CHANNELS)):
            values = [sequence[index].values[axis] for index in indices]
            order = _development_rng(
                seed,
                f"v25a-completion-shuffle-{cue}-{context}-{axis}",
            ).permutation(len(indices))
            for target, source in zip(indices, order):
                output[target][axis] = values[int(source)]
    return tuple(
        Episode(episode.cue, episode.context, tuple(values))
        for episode, values in zip(sequence, output)
    )


def lesion_interaction(episodes: Iterable[Episode]) -> ConfiguralScore:
    return score(episodes, presentation="marginal")


def nearest_reachable_match(
    target: float, trajectory: Sequence[float], cap: int
) -> dict[str, float | int | bool]:
    """Lattice-aware shortest nearest-prefix matching readout."""
    values = np.asarray(tuple(trajectory)[: int(cap)], dtype=float)
    if len(values) == 0:
        return {
            "target_kl": float(target),
            "matched_index": 0,
            "matched_kl": 0.0,
            "absolute_error": abs(float(target)),
            "local_lattice_gap": 0.0,
            "censored": True,
        }
    errors = np.abs(values - float(target))
    index = int(np.flatnonzero(errors == errors.min())[0])
    neighbors = []
    if index > 0:
        neighbors.append(abs(float(values[index] - values[index - 1])))
    if index + 1 < len(values):
        neighbors.append(abs(float(values[index + 1] - values[index])))
    return {
        "target_kl": float(target),
        "matched_index": index + 1,
        "matched_kl": float(values[index]),
        "absolute_error": float(errors[index]),
        "local_lattice_gap": float(min(neighbors) if neighbors else 0.0),
        "censored": False,
    }


def finite_information_bound() -> dict[str, float]:
    minimum = 1.0
    maximum = 0.0
    for cue in range(4):
        for context in (0, 1):
            for root in (0, 1):
                for kappa in (0.0,) + KAPPA_GRID:
                    table = joint_table(cue, context, root, kappa)
                    minimum = min(minimum, float(table.min()))
                    maximum = max(maximum, float(table.max()))
    bound = math.log(maximum / minimum)
    return {
        "B_max_v25a_configural": bound,
        "implied_binary_probability_change_bound": math.tanh(bound / 4.0),
    }
