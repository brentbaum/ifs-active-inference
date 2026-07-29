"""V2.G0 typed compositional world grammar.

This is apparatus code.  It constructs finite stochastic worlds and records
their exact probability and RNG custody; it contains no psychological state
or scientific-model inference.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


STAGE_VERSION = "V2.G0"
DEVELOPMENT_SEEDS = (1_000_000, 1_009_999)
DIAGNOSIS_SEEDS = (1_010_000, 1_019_999)
SEALED_ESCROW = (2_000_000, 2_000_499)
RELEASED_BLOCKS_PATH = (
    Path(__file__).resolve().parents[1]
    / "protocols"
    / "v2.g0-released-blocks.json"
)
PROCESS_KINDS = frozenset(
    {
        "static",
        "iid",
        "markov",
        "ordered_drift",
        "change_point",
        "recurrent_context",
        "action_contingent",
        "masked_observation",
        "joint_episode",
        "partner_process",
        "joint_policy_outcome",
        "mixture",
        "shared_latent",
    }
)
FINITE_PATH_KINDS = frozenset(
    {
        "static",
        "iid",
        "markov",
        "ordered_drift",
        "recurrent_context",
        "action_contingent",
        "masked_observation",
    }
)


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _canonical_hash(value: Any) -> str:
    def canonical(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): canonical(child)
                for key, child in sorted(
                    item.items(), key=lambda pair: str(pair[0])
                )
            }
        if isinstance(item, (tuple, list)):
            return [canonical(child) for child in item]
        if isinstance(item, np.generic):
            return item.item()
        return item

    payload = json.dumps(
        canonical(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def component_rng_key(
    seed: int, component_namespace: str, time_or_event_index: int | str
) -> tuple[str, int, str, int | str]:
    """Return the mandatory four-part Epoch-B RNG key."""
    return (STAGE_VERSION, int(seed), str(component_namespace), time_or_event_index)


def _rng(key: tuple[str, int, str, int | str]) -> np.random.Generator:
    digest = hashlib.sha256(
        json.dumps(list(key), separators=(",", ":")).encode("utf-8")
    ).digest()
    return np.random.default_rng(int.from_bytes(digest[:16], "big"))


def _released_blocks(path: Path | None = None) -> tuple[tuple[int, int], ...]:
    authorization_path = RELEASED_BLOCKS_PATH if path is None else path
    record = json.loads(authorization_path.read_text(encoding="utf-8"))
    if record.get("stage") != STAGE_VERSION or record.get("version") != 1:
        raise ValueError("invalid V2.G0 released-blocks authorization record")
    raw_blocks = record.get("released_blocks")
    if not isinstance(raw_blocks, list):
        raise ValueError("released_blocks must be a list")
    blocks = []
    for entry in raw_blocks:
        if not isinstance(entry, Mapping):
            raise ValueError("released block entry must be a mapping")
        start, end = int(entry["start"]), int(entry["end"])
        purpose = entry.get("purpose")
        within_diagnosis = (
            DIAGNOSIS_SEEDS[0] <= start <= end <= DIAGNOSIS_SEEDS[1]
            and purpose == "diagnosis"
        )
        within_escrow = (
            SEALED_ESCROW[0] <= start <= end <= SEALED_ESCROW[1]
            and purpose == "sealed"
        )
        if not (within_diagnosis or within_escrow):
            raise ValueError(
                "released block must be contained in the V2.G0 diagnosis "
                "or sealed range with the matching purpose"
            )
        if not entry.get("release_id") or not entry.get("authorization_commit"):
            raise ValueError(
                "released block requires release_id and authorization_commit"
            )
        blocks.append((start, end))
    return tuple(blocks)


def _validate_seed(seed: int) -> None:
    if DEVELOPMENT_SEEDS[0] <= seed <= DEVELOPMENT_SEEDS[1]:
        return
    if any(start <= seed <= end for start, end in _released_blocks()):
        return
    if DIAGNOSIS_SEEDS[0] <= seed <= DIAGNOSIS_SEEDS[1]:
        raise ValueError(
            "diagnosis-reserved seed is not in the committed release record"
        )
    if SEALED_ESCROW[0] <= seed <= SEALED_ESCROW[1]:
        raise ValueError(
            "sealed C-V2G0 escrow is not in the committed release record"
        )
    raise ValueError(
        f"V2.G0 seed must be a development seed or explicitly released; got {seed}"
    )


def _probabilities(
    values: Sequence[Any], probabilities: Sequence[float], label: str
) -> tuple[tuple[Any, ...], tuple[float, ...]]:
    support = tuple(values)
    probs = tuple(float(value) for value in probabilities)
    if not support or len(support) != len(probs):
        raise ValueError(f"{label} support/probability length mismatch")
    if any((not math.isfinite(value) or value < 0.0) for value in probs):
        raise ValueError(f"{label} probabilities must be finite and nonnegative")
    if not math.isclose(sum(probs), 1.0, abs_tol=1e-12):
        raise ValueError(f"{label} probabilities must sum to one")
    return support, probs


def _matrix(
    states: Sequence[Any], rows: Mapping[str, Sequence[float]], label: str
) -> tuple[tuple[float, ...], ...]:
    result = []
    for state in states:
        if str(state) not in rows:
            raise ValueError(f"{label} missing transition row for {state!r}")
        _, row = _probabilities(states, rows[str(state)], f"{label}[{state!r}]")
        result.append(row)
    return tuple(result)


def _restriction_holds(path: Sequence[Any], restriction: Mapping[str, Any]) -> bool:
    if not restriction:
        return True
    switches = [
        index for index in range(1, len(path)) if path[index] != path[index - 1]
    ]
    if restriction.get("at_least_one_switch") and not switches:
        return False
    if restriction.get("old_context_recurrence"):
        if not switches:
            return False
        first = path[0]
        if not any(value == first for value in path[switches[0] + 1 :]):
            return False
    for state, minimum in restriction.get("minimum_visits", {}).items():
        if sum(value == state for value in path) < int(minimum):
            return False
    onset_window = restriction.get("onset_window")
    if onset_window is not None:
        if not switches:
            return bool(restriction.get("allow_no_change", False))
        if len(switches) != 1:
            return False
        start, end = map(int, onset_window)
        if not start <= switches[0] <= end:
            return False
    return True


def _unconditioned_path_distribution(
    spec: Mapping[str, Any],
) -> tuple[tuple[tuple[Any, ...], float], ...]:
    kind = spec["kind"]
    length = int(spec["length"])
    if length < 1:
        raise ValueError("process length must be positive")

    if kind == "static":
        values, probs = _probabilities(
            spec.get("values", [spec.get("value")]),
            spec.get("probabilities", [1.0]),
            "static",
        )
        return tuple(((value,) * length, probability) for value, probability in zip(values, probs))

    if kind in {"iid", "masked_observation"}:
        if kind == "masked_observation":
            availability = float(spec["availability"])
            values, probs = _probabilities(
                [False, True], [1.0 - availability, availability], kind
            )
        else:
            if spec.get("distribution", "categorical") != "categorical":
                raise ValueError("continuous iid processes do not have finite paths")
            values, probs = _probabilities(
                spec["values"], spec["probabilities"], kind
            )
        paths = []
        for path in itertools.product(values, repeat=length):
            probability = math.prod(probs[values.index(value)] for value in path)
            paths.append((tuple(path), probability))
        return tuple(paths)

    if kind in {
        "markov",
        "ordered_drift",
        "recurrent_context",
        "action_contingent",
    }:
        states, initial = _probabilities(
            spec["states"], spec["initial"], f"{kind}.initial"
        )
        if kind == "ordered_drift":
            if list(states) != sorted(states):
                raise ValueError("ordered_drift states must be in declared order")
            transition = _matrix(states, spec["transition"], kind)
        elif kind == "action_contingent":
            actions = tuple(spec["actions"])
            if len(actions) != max(length - 1, 0):
                raise ValueError("action_contingent requires length-1 actions")
            matrices = {
                str(action): _matrix(states, rows, f"{kind}.{action}")
                for action, rows in spec["transitions_by_action"].items()
            }
            if any(str(action) not in matrices for action in actions):
                raise ValueError("action has no declared transition")
            transition = None
        else:
            transition = _matrix(states, spec["transition"], kind)
        paths = []
        for path in itertools.product(states, repeat=length):
            probability = initial[states.index(path[0])]
            for index in range(1, length):
                matrix = (
                    matrices[str(actions[index - 1])]
                    if kind == "action_contingent"
                    else transition
                )
                probability *= matrix[states.index(path[index - 1])][
                    states.index(path[index])
                ]
            if probability > 0.0:
                paths.append((tuple(path), probability))
        return tuple(paths)

    raise ValueError(f"{kind!r} is not a finite path process")


def _conditioned_paths(
    spec: Mapping[str, Any],
) -> tuple[tuple[tuple[Any, ...], float], float]:
    distribution = _unconditioned_path_distribution(spec)
    restriction = spec.get("restriction", {})
    retained = tuple(
        (path, probability)
        for path, probability in distribution
        if _restriction_holds(path, restriction)
    )
    normalizer = math.fsum(probability for _, probability in retained)
    if not math.isfinite(normalizer) or normalizer <= 0.0:
        raise ValueError("path restriction has zero or invalid normalizer")
    return retained, normalizer


@dataclass(frozen=True, slots=True)
class CompiledProcess:
    name: str
    kind: str
    scope: tuple[str, ...]
    spec: Mapping[str, Any]
    restriction_normalizer: float
    finite_paths: tuple[tuple[tuple[Any, ...], float], ...]


@dataclass(frozen=True, slots=True)
class CompiledWorld:
    stage_version: str
    spec: Mapping[str, Any]
    processes: tuple[CompiledProcess, ...]
    world_spec_hash: str
    process_scopes: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True, slots=True)
class WorldTrace:
    world_spec_hash: str
    protocol_spec_hash: str | None
    process_scopes: Mapping[str, tuple[str, ...]]
    process_kinds: Mapping[str, str]
    truth_trace: Mapping[str, Any]
    observation_trace: tuple[Any, ...]
    interventions: tuple[Any, ...]
    component_rng_keys: tuple[tuple[str, int, str, int | str], ...]
    exact_world_log_probability: float
    output_schema_hash: str
    restriction_normalizers: Mapping[str, float]
    mixture_components: Mapping[str, str]


def _compile_process(raw: Mapping[str, Any]) -> CompiledProcess:
    spec = _plain(raw)
    name = str(spec.get("name", ""))
    kind = str(spec.get("kind", ""))
    scope = tuple(str(value) for value in spec.get("scope", ()))
    if not name or kind not in PROCESS_KINDS or not scope:
        raise ValueError("every process requires a name, supported kind, and scope")
    if len(set(scope)) != len(scope):
        raise ValueError(f"duplicate scope entry in process {name!r}")

    paths: tuple[tuple[tuple[Any, ...], float], ...] = ()
    normalizer = 1.0
    if kind in FINITE_PATH_KINDS:
        if kind == "iid" and spec.get("distribution", "categorical") == "uniform":
            low, high = map(float, spec["bounds"])
            if not math.isfinite(low + high) or high <= low:
                raise ValueError("bounded continuous iid requires finite low < high")
            if spec.get("restriction"):
                raise ValueError("continuous iid does not support finite path restrictions")
        else:
            paths, normalizer = _conditioned_paths(spec)
    elif kind == "change_point":
        length = int(spec["length"])
        if length < 1:
            raise ValueError("change_point length must be positive")
        onset_values = tuple(spec["onset_probabilities"])
        allowed = set(range(1, length)) | {"no_change"}
        if not set(onset_values).issubset(allowed):
            raise ValueError("change_point onset is outside sequence support")
        _, probabilities = _probabilities(
            onset_values,
            [spec["onset_probabilities"][value] for value in onset_values],
            "change_point.onset",
        )
        window = spec.get("onset_window")
        retained = [
            probability
            for value, probability in zip(onset_values, probabilities)
            if value == "no_change"
            and spec.get("allow_no_change", True)
            or isinstance(value, int)
            and (window is None or int(window[0]) <= value <= int(window[1]))
        ]
        normalizer = math.fsum(retained)
        if normalizer <= 0.0:
            raise ValueError("change_point onset restriction has zero mass")
    elif kind == "joint_episode":
        _probabilities(spec["episodes"], spec["probabilities"], kind)
    elif kind == "partner_process":
        latent = {
            "name": f"{name}::latent",
            "kind": "markov",
            "scope": [f"{name}::latent"],
            "length": spec["length"],
            "states": spec["states"],
            "initial": spec["initial"],
            "transition": spec["transition"],
            "restriction": spec.get("restriction", {}),
        }
        paths, normalizer = _conditioned_paths(latent)
        for state in spec["states"]:
            channels = spec["emissions"][str(state)]
            for channel, emission in channels.items():
                _probabilities(
                    emission["values"],
                    emission["probabilities"],
                    f"{kind}.{state}.{channel}",
                )
    elif kind == "joint_policy_outcome":
        policies = tuple(tuple(value) for value in spec["policies"])
        if len(policies) != int(spec["length"]):
            raise ValueError("joint_policy_outcome requires one policy per event")
        for policy in policies:
            key = json.dumps(list(policy), separators=(",", ":"))
            outcome = spec["outcomes_by_policy"].get(key)
            if outcome is None:
                raise ValueError(f"no outcome distribution for policy {policy!r}")
            _probabilities(outcome["values"], outcome["probabilities"], kind)
    elif kind == "mixture":
        components = spec["components"]
        names = [str(item["name"]) for item in components]
        _probabilities(names, spec["weights"], "mixture")
        compiled_components = [_compile_process(item) for item in components]
        if any(item.scope != scope for item in compiled_components):
            raise ValueError("mixture components must share the declared mixture scope")
    elif kind == "shared_latent":
        source = _compile_process(spec["latent"])
        if source.kind in {"mixture", "shared_latent"}:
            raise ValueError("nested shared-latent composition is not supported")
        paths = source.finite_paths
        normalizer = source.restriction_normalizer

    return CompiledProcess(
        name=name,
        kind=kind,
        scope=scope,
        spec=MappingProxyType(spec),
        restriction_normalizer=float(normalizer),
        finite_paths=paths,
    )


def compile_world(world_spec: Mapping[str, Any]) -> CompiledWorld:
    """Validate and compile a typed declarative world specification."""
    spec = _plain(world_spec)
    if spec.get("stage_version") != STAGE_VERSION:
        raise ValueError(f"world stage_version must be {STAGE_VERSION}")
    raw_processes = spec.get("processes")
    if not isinstance(raw_processes, list) or not raw_processes:
        raise ValueError("world requires a nonempty process list")
    processes = tuple(_compile_process(item) for item in raw_processes)
    names = [process.name for process in processes]
    if len(names) != len(set(names)):
        raise ValueError("process names must be unique")

    occupied: dict[str, str] = {}
    for process in processes:
        if process.kind == "shared_latent":
            continue
        for member in process.scope:
            if member in occupied:
                raise ValueError(
                    f"product scopes overlap at {member!r}: "
                    f"{occupied[member]!r} and {process.name!r}"
                )
            occupied[member] = process.name
    process_scopes = MappingProxyType(
        {process.name: process.scope for process in processes}
    )
    return CompiledWorld(
        stage_version=STAGE_VERSION,
        spec=MappingProxyType(spec),
        processes=processes,
        world_spec_hash=_canonical_hash(spec),
        process_scopes=process_scopes,
    )


def _choice_index(
    probabilities: Sequence[float],
    seed: int,
    namespace: str,
    event: int | str,
    keys: list[tuple[str, int, str, int | str]],
) -> int:
    key = component_rng_key(seed, namespace, event)
    keys.append(key)
    total = math.fsum(probabilities)
    normalized = np.asarray(probabilities, dtype=float) / total
    return int(_rng(key).choice(len(normalized), p=normalized))


def _sample_compiled_process(
    process: CompiledProcess,
    seed: int,
    keys: list[tuple[str, int, str, int | str]],
) -> tuple[Any, float, str | None]:
    spec = process.spec
    namespace = process.name
    kind = process.kind

    if kind in FINITE_PATH_KINDS and process.finite_paths:
        probabilities = [value for _, value in process.finite_paths]
        index = _choice_index(probabilities, seed, namespace, "conditioned_path", keys)
        path, probability = process.finite_paths[index]
        return list(path), math.log(probability / process.restriction_normalizer), None

    if kind == "iid" and spec.get("distribution") == "uniform":
        low, high = map(float, spec["bounds"])
        values = []
        for index in range(int(spec["length"])):
            key = component_rng_key(seed, namespace, index)
            keys.append(key)
            values.append(float(_rng(key).uniform(low, high)))
        return values, -int(spec["length"]) * math.log(high - low), None

    if kind == "change_point":
        onset_values = []
        probabilities = []
        window = spec.get("onset_window")
        for value, probability in spec["onset_probabilities"].items():
            keep = (
                value == "no_change"
                and spec.get("allow_no_change", True)
                or isinstance(value, int)
                and (window is None or int(window[0]) <= value <= int(window[1]))
            )
            if keep:
                onset_values.append(value)
                probabilities.append(float(probability))
        selected = _choice_index(
            probabilities, seed, namespace, "onset", keys
        )
        onset = onset_values[selected]
        path = [
            spec["before"]
            if onset == "no_change" or index < int(onset)
            else spec["after"]
            for index in range(int(spec["length"]))
        ]
        return (
            {"onset": onset, "path": path},
            math.log(probabilities[selected] / process.restriction_normalizer),
            None,
        )

    if kind == "joint_episode":
        episodes, probabilities = _probabilities(
            spec["episodes"], spec["probabilities"], kind
        )
        values = []
        log_probability = 0.0
        for index in range(int(spec["length"])):
            selected = _choice_index(
                probabilities, seed, namespace, index, keys
            )
            values.append(_plain(episodes[selected]))
            log_probability += math.log(probabilities[selected])
        return values, log_probability, None

    if kind == "partner_process":
        path_probabilities = [value for _, value in process.finite_paths]
        selected = _choice_index(
            path_probabilities, seed, f"{namespace}::latent", "conditioned_path", keys
        )
        latent, probability = process.finite_paths[selected]
        emissions: dict[str, list[Any]] = {
            channel: []
            for channel in spec["emissions"][str(latent[0])]
        }
        log_probability = math.log(probability / process.restriction_normalizer)
        for index, state in enumerate(latent):
            for channel, emission in spec["emissions"][str(state)].items():
                values, probabilities = _probabilities(
                    emission["values"], emission["probabilities"], channel
                )
                chosen = _choice_index(
                    probabilities,
                    seed,
                    f"{namespace}::emission::{channel}",
                    index,
                    keys,
                )
                emissions[channel].append(values[chosen])
                log_probability += math.log(probabilities[chosen])
        return (
            {"latent": list(latent), "channels": emissions},
            log_probability,
            None,
        )

    if kind == "joint_policy_outcome":
        outcomes = []
        log_probability = 0.0
        for index, policy in enumerate(spec["policies"]):
            key_name = json.dumps(list(policy), separators=(",", ":"))
            distribution = spec["outcomes_by_policy"][key_name]
            values, probabilities = _probabilities(
                distribution["values"], distribution["probabilities"], kind
            )
            chosen = _choice_index(
                probabilities, seed, namespace, index, keys
            )
            outcomes.append(values[chosen])
            log_probability += math.log(probabilities[chosen])
        return (
            {"policies": _plain(spec["policies"]), "outcomes": outcomes},
            log_probability,
            None,
        )

    if kind == "mixture":
        components = [_compile_process(item) for item in spec["components"]]
        names = [component.name for component in components]
        _, weights = _probabilities(names, spec["weights"], "mixture")
        chosen = _choice_index(weights, seed, namespace, "mixture", keys)
        value, component_log_probability, _ = _sample_compiled_process(
            components[chosen], seed, keys
        )
        return value, math.log(weights[chosen]) + component_log_probability, names[chosen]

    if kind == "shared_latent":
        latent = _compile_process(spec["latent"])
        value, log_probability, _ = _sample_compiled_process(latent, seed, keys)
        return (
            {
                "latent": value,
                "targets": {
                    target: value for target in spec.get("targets", process.scope)
                },
            },
            log_probability,
            None,
        )

    raise AssertionError(f"unhandled compiled process kind {kind!r}")


def _output_schema_hash(
    truth: Mapping[str, Any],
    process_scopes: Mapping[str, tuple[str, ...]],
    process_kinds: Mapping[str, str],
) -> str:
    def shape(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: shape(item) for key, item in sorted(value.items())}
        if isinstance(value, (list, tuple)):
            return {"type": "sequence", "length": len(value)}
        return type(value).__name__

    return _canonical_hash(
        {
            "truth": shape(truth),
            "process_scopes": _plain(process_scopes),
            "process_kinds": _plain(process_kinds),
        }
    )


def sample_world(compiled_world: CompiledWorld, seed: int) -> WorldTrace:
    """Sample a compiled world exactly with component-specific Epoch-B RNG."""
    _validate_seed(seed)
    if not isinstance(compiled_world, CompiledWorld):
        raise TypeError("sample_world requires a CompiledWorld")
    keys: list[tuple[str, int, str, int | str]] = []
    truth: dict[str, Any] = {}
    mixture_components: dict[str, str] = {}
    log_probability = 0.0
    for process in compiled_world.processes:
        value, increment, component = _sample_compiled_process(process, seed, keys)
        truth[process.name] = value
        log_probability += increment
        if component is not None:
            mixture_components[process.name] = component
    kinds = MappingProxyType(
        {process.name: process.kind for process in compiled_world.processes}
    )
    return WorldTrace(
        world_spec_hash=compiled_world.world_spec_hash,
        protocol_spec_hash=None,
        process_scopes=compiled_world.process_scopes,
        process_kinds=kinds,
        truth_trace=MappingProxyType(truth),
        observation_trace=(),
        interventions=(),
        component_rng_keys=tuple(keys),
        exact_world_log_probability=float(log_probability),
        output_schema_hash=_output_schema_hash(
            truth, compiled_world.process_scopes, kinds
        ),
        restriction_normalizers=MappingProxyType(
            {
                process.name: process.restriction_normalizer
                for process in compiled_world.processes
            }
        ),
        mixture_components=MappingProxyType(mixture_components),
    )


def _finite_path_log_probability(
    process: CompiledProcess, value: Sequence[Any]
) -> float:
    target = tuple(value)
    for path, probability in process.finite_paths:
        if path == target:
            return math.log(probability / process.restriction_normalizer)
    return -math.inf


def _process_log_probability(process: CompiledProcess, value: Any) -> float:
    spec = process.spec
    kind = process.kind
    if kind in FINITE_PATH_KINDS and process.finite_paths:
        return _finite_path_log_probability(process, value)
    if kind == "iid" and spec.get("distribution") == "uniform":
        low, high = map(float, spec["bounds"])
        values = tuple(float(item) for item in value)
        if len(values) != int(spec["length"]) or any(
            item < low or item > high for item in values
        ):
            return -math.inf
        return -len(values) * math.log(high - low)
    if kind == "change_point":
        onset = value["onset"]
        probability = spec["onset_probabilities"].get(onset)
        if probability is None:
            return -math.inf
        expected = [
            spec["before"]
            if onset == "no_change" or index < int(onset)
            else spec["after"]
            for index in range(int(spec["length"]))
        ]
        if value["path"] != expected:
            return -math.inf
        return math.log(float(probability) / process.restriction_normalizer)
    if kind == "joint_episode":
        episodes, probabilities = _probabilities(
            spec["episodes"], spec["probabilities"], kind
        )
        lookup = {
            json.dumps(_plain(item), sort_keys=True): probability
            for item, probability in zip(episodes, probabilities)
        }
        try:
            return math.fsum(
                math.log(lookup[json.dumps(_plain(item), sort_keys=True)])
                for item in value
            )
        except KeyError:
            return -math.inf
    if kind == "partner_process":
        latent = tuple(value["latent"])
        latent_probability = _finite_path_log_probability(process, latent)
        if not math.isfinite(latent_probability):
            return -math.inf
        total = latent_probability
        for index, state in enumerate(latent):
            for channel, emission in spec["emissions"][str(state)].items():
                values, probabilities = _probabilities(
                    emission["values"], emission["probabilities"], channel
                )
                observed = value["channels"][channel][index]
                if observed not in values:
                    return -math.inf
                total += math.log(probabilities[values.index(observed)])
        return total
    if kind == "joint_policy_outcome":
        if _plain(value["policies"]) != _plain(spec["policies"]):
            return -math.inf
        total = 0.0
        for policy, observed in zip(spec["policies"], value["outcomes"]):
            key = json.dumps(list(policy), separators=(",", ":"))
            distribution = spec["outcomes_by_policy"][key]
            values, probabilities = _probabilities(
                distribution["values"], distribution["probabilities"], kind
            )
            if observed not in values:
                return -math.inf
            total += math.log(probabilities[values.index(observed)])
        return total
    if kind == "mixture":
        raise ValueError("mixture log probability requires recorded component")
    if kind == "shared_latent":
        latent = _compile_process(spec["latent"])
        if any(
            item != value["latent"] for item in value["targets"].values()
        ):
            return -math.inf
        return _process_log_probability(latent, value["latent"])
    raise AssertionError(kind)


def log_prob_world(compiled_world: CompiledWorld, truth_trace: Any) -> float:
    """Return the exact normalized density/mass of a truth trace."""
    if isinstance(truth_trace, WorldTrace):
        trace = truth_trace
        truth = trace.truth_trace
        components = trace.mixture_components
    else:
        trace = None
        truth = truth_trace
        components = {}
    if set(truth) != {process.name for process in compiled_world.processes}:
        return -math.inf
    total = 0.0
    for process in compiled_world.processes:
        if process.kind == "mixture":
            component_name = components.get(process.name)
            component_specs = process.spec["components"]
            names = [str(item["name"]) for item in component_specs]
            if component_name not in names:
                return -math.inf
            _, weights = _probabilities(
                names, process.spec["weights"], "mixture"
            )
            component = _compile_process(
                component_specs[names.index(component_name)]
            )
            increment = math.log(weights[names.index(component_name)])
            increment += _process_log_probability(component, truth[process.name])
        else:
            increment = _process_log_probability(process, truth[process.name])
        if not math.isfinite(increment):
            return -math.inf
        total += increment
    if trace is not None and trace.world_spec_hash != compiled_world.world_spec_hash:
        return -math.inf
    return float(total)


def independent_world_log_prob(
    world_spec: Mapping[str, Any], truth_trace: WorldTrace
) -> float:
    """Dispatch to the separately authored Cartesian probability oracle."""
    from .world_ir_oracle import independent_world_log_prob as oracle

    return oracle(world_spec, truth_trace)


def public_normalizer(process_spec: Mapping[str, Any]) -> float:
    """Publish the exact restriction normalizer for a process declaration."""
    return _compile_process(process_spec).restriction_normalizer
