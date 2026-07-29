"""Public V2.G0 development fixtures and composition cells."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def world(*processes: dict[str, Any], name: str = "public-fixture") -> dict[str, Any]:
    return {
        "stage_version": "V2.G0",
        "name": name,
        "processes": [deepcopy(process) for process in processes],
    }


def protocol(
    *channels: dict[str, Any],
    actions: tuple[Any, ...] = (),
    name: str = "public-protocol",
) -> dict[str, Any]:
    return {
        "stage_version": "V2.G0",
        "name": name,
        "actions": list(actions),
        "observation_channels": [deepcopy(channel) for channel in channels],
    }


def static(name: str = "static", scope: tuple[str, ...] = ("latent:s",)) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "static",
        "scope": list(scope),
        "length": 6,
        "values": ["low", "high"],
        "probabilities": [0.4, 0.6],
    }


def iid(name: str = "iid", scope: tuple[str, ...] = ("cue:0",)) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "iid",
        "scope": list(scope),
        "length": 6,
        "distribution": "categorical",
        "values": [0, 1],
        "probabilities": [0.35, 0.65],
    }


def markov(name: str = "markov", scope: tuple[str, ...] = ("latent:m",)) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "markov",
        "scope": list(scope),
        "length": 6,
        "states": ["a", "b"],
        "initial": [0.55, 0.45],
        "transition": {"a": [0.8, 0.2], "b": [0.3, 0.7]},
    }


def ordered_drift(
    name: str = "drift", scope: tuple[str, ...] = ("cue:1", "cue:2")
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "ordered_drift",
        "scope": list(scope),
        "length": 6,
        "states": [0, 1, 2],
        "initial": [0.7, 0.2, 0.1],
        "transition": {
            "0": [0.75, 0.25, 0.0],
            "1": [0.15, 0.7, 0.15],
            "2": [0.0, 0.25, 0.75],
        },
    }


def change_point(
    name: str = "change", scope: tuple[str, ...] = ("latent:regime",)
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "change_point",
        "scope": list(scope),
        "length": 10,
        "before": "old",
        "after": "new",
        "onset_probabilities": {
            "no_change": 0.1,
            1: 0.1,
            2: 0.1,
            3: 0.1,
            4: 0.1,
            5: 0.1,
            6: 0.1,
            7: 0.1,
            8: 0.1,
            9: 0.1,
        },
        "onset_window": [2, 7],
        "allow_no_change": False,
    }


def recurrent_context(
    name: str = "context", scope: tuple[str, ...] = ("latent:context",)
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "recurrent_context",
        "scope": list(scope),
        "length": 8,
        "states": ["old", "new"],
        "initial": [0.8, 0.2],
        "transition": {"old": [0.72, 0.28], "new": [0.36, 0.64]},
        "restriction": {
            "at_least_one_switch": True,
            "old_context_recurrence": True,
            "minimum_visits": {"old": 2, "new": 1},
        },
    }


def action_contingent(
    name: str = "availability",
    scope: tuple[str, ...] = ("latent:availability",),
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "action_contingent",
        "scope": list(scope),
        "length": 6,
        "states": [False, True],
        "initial": [0.5, 0.5],
        "actions": ["wait", "ask", "ask", "wait", "ask"],
        "transitions_by_action": {
            "wait": {"False": [0.85, 0.15], "True": [0.35, 0.65]},
            "ask": {"False": [0.3, 0.7], "True": [0.1, 0.9]},
        },
    }


def masked_observation(
    name: str = "mask", scope: tuple[str, ...] = ("nuisance:mask",)
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "masked_observation",
        "scope": list(scope),
        "length": 6,
        "availability": 0.75,
        "candidate_common": True,
    }


def joint_episode(
    name: str = "episode", scope: tuple[str, ...] = ("observation:joint",)
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "joint_episode",
        "scope": list(scope),
        "length": 6,
        "channels": ["outcome", "marker"],
        "episodes": [
            {"outcome": 0, "marker": "then"},
            {"outcome": 1, "marker": "now"},
        ],
        "probabilities": [0.45, 0.55],
    }


def partner_process(
    name: str = "partner", scope: tuple[str, ...] = ("latent:partner",)
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "partner_process",
        "scope": list(scope),
        "length": 6,
        "states": ["near", "far"],
        "initial": [0.6, 0.4],
        "transition": {"near": [0.8, 0.2], "far": [0.3, 0.7]},
        "emissions": {
            "near": {
                "support": {"values": [0, 1], "probabilities": [0.15, 0.85]},
                "signal": {"values": ["cold", "warm"], "probabilities": [0.2, 0.8]},
            },
            "far": {
                "support": {"values": [0, 1], "probabilities": [0.8, 0.2]},
                "signal": {"values": ["cold", "warm"], "probabilities": [0.75, 0.25]},
            },
        },
    }


def joint_policy_outcome(
    name: str = "joint-outcome",
    scope: tuple[str, ...] = ("observation:joint-policy",),
) -> dict[str, Any]:
    return {
        "name": name,
        "kind": "joint_policy_outcome",
        "scope": list(scope),
        "length": 3,
        "policies": [["wait", "ask"], ["ask", "ask"], ["leave", "wait"]],
        "outcomes_by_policy": {
            '["wait","ask"]': {"values": ["safe", "unsafe"], "probabilities": [0.7, 0.3]},
            '["ask","ask"]': {"values": ["safe", "unsafe"], "probabilities": [0.9, 0.1]},
            '["leave","wait"]': {"values": ["safe", "unsafe"], "probabilities": [0.55, 0.45]},
        },
    }


def mixture() -> dict[str, Any]:
    first = markov("stable-component", ("cue:mixed",))
    second = ordered_drift("drift-component", ("cue:mixed",))
    return {
        "name": "mixed-process",
        "kind": "mixture",
        "scope": ["cue:mixed"],
        "weights": [0.4, 0.6],
        "components": [first, second],
    }


def shared_latent() -> dict[str, Any]:
    return {
        "name": "shared-context",
        "kind": "shared_latent",
        "scope": ["cue:left", "cue:right"],
        "latent": markov("shared-source", ("latent:shared",)),
        "targets": ["cue:left", "cue:right"],
    }


RECOVERY_FAMILIES = (
    static,
    iid,
    markov,
    ordered_drift,
    change_point,
    recurrent_context,
    action_contingent,
    masked_observation,
    joint_episode,
    partner_process,
)


def composition_cells() -> dict[str, tuple[dict[str, Any], dict[str, Any]]]:
    action_process = action_contingent()
    return {
        "subset_drift": (
            world(ordered_drift(), name="subset-drift"),
            protocol(
                {"name": "drift", "source_process": "drift"},
                name="subset-drift-protocol",
            ),
        ),
        "constrained_change_point": (
            world(change_point(), name="constrained-change-point"),
            protocol(
                {"name": "regime", "source_process": "change", "path": ["path"]},
                name="change-point-protocol",
            ),
        ),
        "recurrence_guaranteed_context_split": (
            world(recurrent_context(), name="recurrent-context"),
            protocol(
                {"name": "context", "source_process": "context"},
                name="recurrent-protocol",
            ),
        ),
        "mixed_subset_drift_plus_recurrent_split": (
            world(
                ordered_drift(),
                recurrent_context(),
                name="mixed-drift-context",
            ),
            protocol(
                {"name": "drift", "source_process": "drift"},
                {"name": "context", "source_process": "context"},
                name="mixed-protocol",
            ),
        ),
        "family_parameterized_bridge": (
            world(ordered_drift(), name="bridge-drift-family"),
            protocol(
                {"name": "drift", "source_process": "drift"},
                name="bridge-protocol",
            ),
        ),
        "partner_switch_plus_action_contingent_availability": (
            world(
                partner_process(),
                action_process,
                name="partner-action-availability",
            ),
            protocol(
                {
                    "name": "support",
                    "source_process": "partner",
                    "path": ["channels", "support"],
                },
                {
                    "name": "availability",
                    "source_process": "availability",
                },
                actions=tuple(action_process["actions"]),
                name="partner-action-protocol",
            ),
        ),
    }
