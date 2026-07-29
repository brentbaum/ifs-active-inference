"""Independent Cartesian probability oracle for V2.G0.

This module does not call the production compiler, production path scorer, or
production log-probability implementation.
"""

from __future__ import annotations

import itertools
import json
import math
from typing import Any, Mapping, Sequence


def _restriction(path: Sequence[Any], rule: Mapping[str, Any]) -> bool:
    changes = [i for i in range(1, len(path)) if path[i] != path[i - 1]]
    if rule.get("at_least_one_switch") and not changes:
        return False
    if rule.get("old_context_recurrence"):
        if not changes or path[0] not in path[changes[0] + 1 :]:
            return False
    for state, count in rule.get("minimum_visits", {}).items():
        if path.count(state) < int(count):
            return False
    window = rule.get("onset_window")
    if window is not None:
        if not changes:
            return bool(rule.get("allow_no_change", False))
        if len(changes) != 1 or not int(window[0]) <= changes[0] <= int(window[1]):
            return False
    return True


def _finite_mass(spec: Mapping[str, Any], observed: Sequence[Any]) -> float:
    kind = spec["kind"]
    length = int(spec["length"])
    if len(observed) != length:
        return 0.0
    if kind == "static":
        values = spec.get("values", [spec.get("value")])
        probabilities = spec.get("probabilities", [1.0])
        raw = sum(
            float(probability)
            for value, probability in zip(values, probabilities)
            if list(observed) == [value] * length
        )
        normalizer = sum(map(float, probabilities))
        return raw / normalizer
    if kind in {"iid", "masked_observation"}:
        if kind == "masked_observation":
            p = float(spec["availability"])
            values, probabilities = [False, True], [1.0 - p, p]
        else:
            values, probabilities = spec["values"], spec["probabilities"]
        candidates = itertools.product(values, repeat=length)

        def raw(path: Sequence[Any]) -> float:
            return math.prod(
                float(probabilities[values.index(value)]) for value in path
            )

    else:
        states = list(spec["states"])
        initial = list(map(float, spec["initial"]))
        candidates = itertools.product(states, repeat=length)

        def raw(path: Sequence[Any]) -> float:
            result = initial[states.index(path[0])]
            for index in range(1, length):
                if kind == "action_contingent":
                    action = str(spec["actions"][index - 1])
                    rows = spec["transitions_by_action"][action]
                else:
                    rows = spec["transition"]
                result *= float(
                    rows[str(path[index - 1])][states.index(path[index])]
                )
            return result

    retained = [
        (tuple(path), raw(tuple(path)))
        for path in candidates
        if _restriction(tuple(path), spec.get("restriction", {}))
    ]
    normalizer = math.fsum(probability for _, probability in retained)
    target = tuple(observed)
    probability = math.fsum(
        value for path, value in retained if path == target
    )
    return probability / normalizer if normalizer else 0.0


def _process_mass(
    spec: Mapping[str, Any],
    observed: Any,
    mixture_component: str | None = None,
) -> float:
    kind = spec["kind"]
    if kind in {
        "static",
        "iid",
        "markov",
        "ordered_drift",
        "recurrent_context",
        "action_contingent",
        "masked_observation",
    }:
        if kind == "iid" and spec.get("distribution") == "uniform":
            low, high = map(float, spec["bounds"])
            if (
                len(observed) != int(spec["length"])
                or any(value < low or value > high for value in observed)
            ):
                return 0.0
            return (high - low) ** -len(observed)
        return _finite_mass(spec, observed)
    if kind == "change_point":
        onset = observed["onset"]
        expected = [
            spec["before"]
            if onset == "no_change" or index < int(onset)
            else spec["after"]
            for index in range(int(spec["length"]))
        ]
        if observed["path"] != expected:
            return 0.0
        window = spec.get("onset_window")

        def allowed(value: Any) -> bool:
            return (
                value == "no_change"
                and spec.get("allow_no_change", True)
                or isinstance(value, int)
                and (window is None or int(window[0]) <= value <= int(window[1]))
            )

        normalizer = math.fsum(
            float(probability)
            for value, probability in spec["onset_probabilities"].items()
            if allowed(value)
        )
        if onset not in spec["onset_probabilities"] or not allowed(onset):
            return 0.0
        return float(spec["onset_probabilities"][onset]) / normalizer
    if kind == "joint_episode":
        lookup = {
            json.dumps(item, sort_keys=True): float(probability)
            for item, probability in zip(
                spec["episodes"], spec["probabilities"]
            )
        }
        result = 1.0
        for item in observed:
            result *= lookup.get(json.dumps(item, sort_keys=True), 0.0)
        return result
    if kind == "partner_process":
        latent_spec = {
            "kind": "markov",
            "length": spec["length"],
            "states": spec["states"],
            "initial": spec["initial"],
            "transition": spec["transition"],
            "restriction": spec.get("restriction", {}),
        }
        result = _finite_mass(latent_spec, observed["latent"])
        for index, state in enumerate(observed["latent"]):
            for channel, emission in spec["emissions"][str(state)].items():
                value = observed["channels"][channel][index]
                if value not in emission["values"]:
                    return 0.0
                result *= float(
                    emission["probabilities"][emission["values"].index(value)]
                )
        return result
    if kind == "joint_policy_outcome":
        if observed["policies"] != spec["policies"]:
            return 0.0
        result = 1.0
        for policy, value in zip(spec["policies"], observed["outcomes"]):
            key = json.dumps(list(policy), separators=(",", ":"))
            distribution = spec["outcomes_by_policy"][key]
            if value not in distribution["values"]:
                return 0.0
            result *= float(
                distribution["probabilities"][
                    distribution["values"].index(value)
                ]
            )
        return result
    if kind == "mixture":
        names = [str(item["name"]) for item in spec["components"]]
        if mixture_component not in names:
            return 0.0
        index = names.index(mixture_component)
        return float(spec["weights"][index]) * _process_mass(
            spec["components"][index], observed
        )
    if kind == "shared_latent":
        if any(
            item != observed["latent"] for item in observed["targets"].values()
        ):
            return 0.0
        return _process_mass(spec["latent"], observed["latent"])
    raise ValueError(f"unknown process kind {kind!r}")


def independent_world_log_prob(
    world_spec: Mapping[str, Any], truth_trace: Any
) -> float:
    truth = truth_trace.truth_trace
    mixture_components = truth_trace.mixture_components
    total = 0.0
    for process in world_spec["processes"]:
        probability = _process_mass(
            process,
            truth[process["name"]],
            mixture_components.get(process["name"]),
        )
        if probability <= 0.0:
            return -math.inf
        total += math.log(probability)
    return float(total)
