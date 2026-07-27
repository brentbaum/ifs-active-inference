"""Independent C-V232-F constitution summation path.

This module imports nothing from ``ref`` and duplicates the frozen predictive
calculation from the public parameter block using scalar loops.
"""

from __future__ import annotations

import json
import math
from pathlib import Path


PARAMETER_PATH = (
    Path(__file__).resolve().parents[1]
    / "protocols"
    / "v2.3.2-formation-parameters.json"
)
PARAMETERS = json.loads(PARAMETER_PATH.read_text(encoding="utf-8"))
LABELS = tuple(PARAMETERS["candidate_labels"])
SUPPORT = tuple(
    (self_value, outcome, localization)
    for self_value in (0, 1)
    for outcome in (0, 1)
    for localization in (0, 1, 2)
)


def _logit(value: float) -> float:
    return math.log(value / (1.0 - value))


def _sharpen(value: float, scale: float) -> float:
    return 1.0 / (1.0 + math.exp(-scale * _logit(value)))


def independent_row(
    candidate: str,
    configuration: dict[str, object],
) -> list[float]:
    if not bool(configuration["event"]):
        return [
            0.25 if localization == 2 else 0.0
            for _, _, localization in SUPPORT
        ]
    scale = float(
        PARAMETERS["precision_scale"][str(configuration["precision"])]
    )
    ps = _sharpen(
        float(PARAMETERS["self_probability"][candidate]), scale
    )
    if candidate == "D":
        outcome_key = (
            "D_real" if bool(configuration["real_danger"]) else "D_apparent"
        )
    else:
        outcome_key = candidate
    py = _sharpen(
        float(
            PARAMETERS["outcome_probability"][outcome_key][
                f"{configuration['control']}_control"
            ]
        ),
        scale,
    )
    collapsed = configuration["broadcast"] == "collapsed"
    px = (
        None
        if collapsed
        else _sharpen(
            float(PARAMETERS["localization_probability"][candidate]),
            scale,
        )
    )
    coupling = (
        float(PARAMETERS["configural_log_coupling"][candidate]) * scale
    )
    weights = []
    for self_value, outcome, localization in SUPPORT:
        if px is None:
            if localization != 2:
                weights.append(0.0)
                continue
            localization_mass = 1.0
        else:
            if localization == 2:
                weights.append(0.0)
                continue
            localization_mass = px if localization else 1.0 - px
        weights.append(
            (ps if self_value else 1.0 - ps)
            * (py if outcome else 1.0 - py)
            * localization_mass
            * math.exp(coupling * self_value * outcome)
        )
    total = sum(weights)
    return [weight / total for weight in weights]


def independent_log_joint(
    observations: list[tuple[int, int, int]],
    configurations: list[dict[str, object]],
    masks: list[bool],
) -> list[float]:
    values = [
        math.log(float(probability))
        for probability in PARAMETERS["candidate_prior"]
    ]
    for observation, configuration, masked in zip(
        observations, configurations, masks
    ):
        if masked:
            continue
        observation_index = SUPPORT.index(observation)
        for candidate_index, candidate in enumerate(LABELS):
            row = independent_row(candidate, configuration)
            values[candidate_index] += math.log(row[observation_index])
    return values
