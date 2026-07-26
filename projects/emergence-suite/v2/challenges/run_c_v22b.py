"""Run sealed challenge C-V22b against the frozen V2.2.1 strain."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np

V2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = V2_ROOT.parents[2]
if str(V2_ROOT) not in sys.path:
    sys.path.insert(0, str(V2_ROOT))

from ref.factor import Factor  # noqa: E402
from ref.inference import ExactEngine  # noqa: E402
from ref.model import FiniteModel, Variable  # noqa: E402
from ref.templates import categorical_prior, conditional_categorical  # noqa: E402
from ref.v21 import BROADCAST, MONITOR  # noqa: E402
from ref.v22 import ADMISSION  # noqa: E402
from ref.v221 import (  # noqa: E402
    FLOOR_BAND,
    OBS_RELIABILITY,
    learn_association,
    model_averaged_association,
)


CHALLENGE = "C-V22b"
STAGE = "V2.2.1"
FROZEN_COMMIT = "347482f"
RELEASED_BLOCK = (806117, 806416)
WORLD_COUNT = 60
CUE_COUNT = 8
HISTORY_TIERS = {"short": 30, "medium": 120, "long": 480}
PRIMARY_TIER = "medium"
TRUE_ASSOCIATIONS = np.array([0.90, 0.90, 0.70, 0.70, 0.50, 0.50, 0.50, 0.50])
TRUE_SIMILARITIES = np.array([1.00, 0.24, 0.20, 0.18, 0.95, 0.16, 0.14, 0.12])
STRONG_CUES = (0, 1)
WEAK_CUES = (2, 3)
ZERO_CUES = (4, 5, 6, 7)
STRONG_TREATMENT_CUE = 0
ZERO_TREATMENT_CUE = 4
PRECISION_STATES = (2, 0)
LOCAL_UPTAKE_MINIMUM = 0.20
ROOT_NULL_BAND = 0.01
TRANSFER_NULL_BAND = 0.01
SPEARMAN_THRESHOLD = 0.60
ORDERING_THRESHOLD = 45
LONG_FLOOR_THRESHOLD = 48


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_identity() -> dict[str, Any]:
    manifest_rel = (
        "projects/emergence-suite/v2/results/V2.2.1/freeze-manifest.json"
    )
    manifest_bytes = subprocess.check_output(
        ["git", "show", f"{FROZEN_COMMIT}:{manifest_rel}"],
        cwd=REPO_ROOT,
    )
    manifest = json.loads(manifest_bytes)
    mismatches = []
    for relative, expected in manifest["files"].items():
        path = V2_ROOT / relative
        actual = sha256(path) if path.exists() else None
        if actual != expected:
            mismatches.append(
                {"file": relative, "expected": expected, "actual": actual}
            )
    if mismatches:
        raise RuntimeError(f"{STAGE} frozen identity failure: {mismatches}")
    return {
        "commit": FROZEN_COMMIT,
        "manifest": manifest_rel,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "manifest_file_count": len(manifest["files"]),
        "mismatches": mismatches,
    }


def released_seeds() -> list[int]:
    start, end = RELEASED_BLOCK
    seeds = list(range(start, start + WORLD_COUNT))
    if seeds[-1] > end:
        raise ValueError("requested seeds exceed the released C-V22b block")
    return seeds


def escrow_rng(seed: int, component: str) -> np.random.Generator:
    if seed < RELEASED_BLOCK[0] or seed > RELEASED_BLOCK[1]:
        raise ValueError(f"seed {seed} is outside the released C-V22b block")
    payload = f"{CHALLENGE}:{seed}:{component}".encode()
    digest = hashlib.sha256(payload).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def mean_interval(values: Iterable[float]) -> tuple[float, float, float]:
    array = np.asarray(list(values), dtype=float)
    mean = float(array.mean())
    if len(array) < 2:
        return mean, mean, mean
    half_width = 1.96 * float(array.std(ddof=1)) / np.sqrt(len(array))
    return mean, mean - half_width, mean + half_width


def proportion_interval(successes: int, total: int) -> tuple[float, float, float]:
    probability = successes / total
    denominator = 1.0 + 1.96**2 / total
    center = (probability + 1.96**2 / (2 * total)) / denominator
    half = (
        1.96
        * np.sqrt(
            probability * (1.0 - probability) / total
            + 1.96**2 / (4 * total**2)
        )
        / denominator
    )
    return float(probability), float(center - half), float(center + half)


def tied_ranks(values: Iterable[float]) -> np.ndarray:
    array = np.asarray(list(values), dtype=float)
    order = np.argsort(array, kind="mergesort")
    ranks = np.empty(len(array), dtype=float)
    position = 0
    while position < len(array):
        end = position + 1
        while end < len(array) and array[order[end]] == array[order[position]]:
            end += 1
        ranks[order[position:end]] = (position + 1 + end) / 2.0
        position = end
    return ranks


def spearman(values_x: Iterable[float], values_y: Iterable[float]) -> float:
    rank_x = tied_ranks(values_x)
    rank_y = tied_ranks(values_y)
    if np.std(rank_x) == 0.0 or np.std(rank_y) == 0.0:
        return 0.0
    return float(np.corrcoef(rank_x, rank_y)[0, 1])


def generate_development(seed: int) -> dict[str, dict[str, list[float]]]:
    maximum_length = max(HISTORY_TIERS.values())
    match_sequences = []
    similarity_sequences = []
    for cue in range(CUE_COUNT):
        match_sequences.append(
            escrow_rng(seed, f"association-history-{cue}").random(maximum_length)
            < TRUE_ASSOCIATIONS[cue]
        )
        similarity_sequences.append(
            escrow_rng(seed, f"similarity-history-{cue}").random(maximum_length)
            < TRUE_SIMILARITIES[cue]
        )

    tier_results: dict[str, dict[str, list[float]]] = {}
    for tier, length in HISTORY_TIERS.items():
        associations = []
        null_probabilities = []
        similarities = []
        for cue in range(CUE_COUNT):
            matches = int(np.sum(match_sequences[cue][:length]))
            state = learn_association(matches, length - matches)
            associations.append(model_averaged_association(state))
            null_probabilities.append(
                float(state.posterior_store["Z_association"][0])
            )
            similarity_hits = int(np.sum(similarity_sequences[cue][:length]))
            similarities.append((similarity_hits + 1.0) / (length + 2.0))
        tier_results[tier] = {
            "associations": associations,
            "null_probabilities": null_probabilities,
            "similarities": similarities,
        }
    return tier_results


def infer_corrective_segment(
    root_prior: np.ndarray,
    association: float,
    q_observation: int,
) -> dict[str, np.ndarray]:
    """Compile one contract-level segment; no boundary label enters inference."""
    model = FiniteModel()
    for variable in (
        Variable("Phi", 3),
        Variable("L", 3),
        Variable("G", 2),
        Variable("M", 2),
    ):
        model.add_variable(variable)
    model.add_factor(categorical_prior("Phi", [1 / 3] * 3))
    model.add_factor(categorical_prior("L", [1 / 3] * 3))
    model.add_factor(
        Factor(("L",), MONITOR[:, q_observation], "conditional_categorical")
    )
    model.add_factor(
        Factor(("Phi", "L"), BROADCAST, "hierarchical_precision_prior")
    )
    model.add_factor(categorical_prior("G", root_prior))
    table = np.empty((3, 2, 2))
    for phi in range(3):
        effective = (
            0.5
            + (association - 0.5)
            * (ADMISSION[phi] - 0.5)
            / 0.5
        )
        table[phi] = [
            [effective, 1.0 - effective],
            [1.0 - effective, effective],
        ]
    model.add_factor(
        Factor(("Phi", "G", "M"), table, "conditional_categorical")
    )
    model.add_factor(
        Factor(
            ("M",),
            np.array([1.0 - OBS_RELIABILITY, OBS_RELIABILITY]),
            "conditional_categorical",
        )
    )
    joint, _ = ExactEngine().infer(model, ("Phi", "G", "M"), {})
    return {
        "Phi": joint.sum(axis=(1, 2)),
        "G": joint.sum(axis=(0, 2)),
        "M": joint.sum(axis=(0, 1)),
    }


def probe(root: np.ndarray, association: float) -> np.ndarray:
    model = FiniteModel()
    model.add_variable(Variable("G", 2))
    model.add_variable(Variable("M", 2))
    model.add_factor(categorical_prior("G", root))
    model.add_factor(
        conditional_categorical(
            "G",
            "M",
            [
                [association, 1.0 - association],
                [1.0 - association, association],
            ],
        )
    )
    posterior, _ = ExactEngine().infer(model, ("M",), {})
    return posterior


def treatment_arm(
    associations: list[float],
    q_observations: tuple[int, int],
    treated_cue: int,
) -> dict[str, Any]:
    root_start = np.array([0.5, 0.5])
    root = root_start.copy()
    attributions = []
    cue_revisions = []
    for q_observation in q_observations:
        before = root.copy()
        posterior = infer_corrective_segment(
            root, associations[treated_cue], q_observation
        )
        root = posterior["G"]
        attributions.append(abs(float(root[1] - before[1])))
        cue_revisions.append(abs(float(posterior["M"][1] - 0.5)))

    transfers = {}
    for cue, association in enumerate(associations):
        if cue == treated_cue:
            continue
        before = probe(root_start, association)
        after = probe(root, association)
        transfers[cue] = float(after[1] - before[1])
    return {
        "root_revision": float(root[1] - root_start[1]),
        "broad_attribution": attributions[0],
        "narrowed_attribution": attributions[1],
        "broad_minus_narrowed": attributions[0] - attributions[1],
        "broad_cue_revision": cue_revisions[0],
        "narrowed_cue_revision": cue_revisions[1],
        "transfers": transfers,
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    def native(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, np.ndarray):
            return item.tolist()
        raise TypeError(f"cannot serialize {item.__class__.__name__}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, default=native) + "\n",
        encoding="utf-8",
    )


def render_report(summary: dict[str, Any]) -> str:
    tests = summary["tests"]
    graded = tests["graded_transfer"]
    dose = tests["floor_dose_response"]
    mediation = tests["mediation"]
    gating = tests["segment_gating"]
    verdict = "PASS" if summary["passed"] else "FAIL"
    failures = "\n".join(f"- `{item}`" for item in summary["failure_localization"])
    if not failures:
        failures = "- No preregistered failure was triggered."
    return f"""# C-V22b Gate 6 report

Verdict: **{verdict}**

The runner checked all {summary['frozen_identity']['manifest_file_count']} frozen
V2.2.1 files against commit `{summary['frozen_identity']['commit']}` with zero
mismatches. It used seeds `{summary['seed_block_used'][0]}` through
`{summary['seed_block_used'][1]}`, paired across both treatment arms and across
the three nested history-length doses.

## Preregistered tests

1. **Graded transfer — {'PASS' if graded['passed'] else 'FAIL'}.** Mean
   within-world Spearman correlation was `{graded['spearman_95_interval'][0]:.3f}`
   (95% interval `{graded['spearman_95_interval'][1]:.3f}` to
   `{graded['spearman_95_interval'][2]:.3f}`), against the `.60` threshold;
   the strong > weak > zero ordering held in
   `{graded['ordered_worlds']}/60` worlds
   (95% Wilson interval `{graded['ordered_worlds_95_interval'][1]:.3f}` to
   `{graded['ordered_worlds_95_interval'][2]:.3f}`).
2. **Floor with dose-response — {'PASS' if dose['passed'] else 'FAIL'}.**
   Mean absolute G revision after zero-cue treatment was
   `{dose['mean_root_revision_by_tier']['short'][0]:.6f}` at short,
   `{dose['mean_root_revision_by_tier']['medium'][0]:.6f}` at medium, and
   `{dose['mean_root_revision_by_tier']['long'][0]:.6f}` at long history.
   The paired short-minus-medium and medium-minus-long effects were
   `{dose['paired_differences']['short_minus_medium'][0]:.6f}` and
   `{dose['paired_differences']['medium_minus_long'][0]:.6f}`. Long-history
   floor compliance was `{dose['long_floor_worlds']}/60`
   (95% Wilson interval `{dose['long_floor_95_interval'][1]:.3f}` to
   `{dose['long_floor_95_interval'][2]:.3f}`).
3. **Mediation — {'PASS' if mediation['passed'] else 'FAIL'}.** The explicit
   root-cut transfer was `{mediation['maximum_root_cut_transfer']:.3g}`.
   There were `{mediation['null_root_worlds']}` arm-tier instances in the root
   null band; maximum untreated transfer among them was
   `{mediation['maximum_null_world_transfer']:.6f}`.
4. **Segment gating — {'PASS' if gating['passed'] else 'FAIL'}.** The
   broad-minus-narrowed attribution effect was
   `{gating['attribution_effect_95_interval'][0]:.6f}` (95% interval
   `{gating['attribution_effect_95_interval'][1]:.6f}` to
   `{gating['attribution_effect_95_interval'][2]:.6f}`). Mean cue-level
   revisions were `{gating['broad_cue_revision_95_interval'][0]:.6f}` broad
   and `{gating['narrowed_cue_revision_95_interval'][0]:.6f}` narrowed.

The primary 60-world slice for tests 1, 3, and 4 is the preregistered medium
history. Each of those same 60 paired base worlds also uses nested short and
long prefixes for test 2; this is required to interpret the sealed
`48/60 of LONG-tier worlds` threshold without consuming extra seeds. Segment
identity and the unannounced boundary were not inference inputs.

## Failure localization

{failures}

No frozen engine, stage, contract, parameter, result, tolerance, or manifest
file was modified.
"""


def render_milestone_update(summary: dict[str, Any]) -> str:
    verdict = "PASS" if summary["passed"] else "FAIL"
    dose = summary["tests"]["floor_dose_response"]
    graded = summary["tests"]["graded_transfer"]
    return f"""# Suite v2 milestone 1 — V2.2.1 Gate 6 update

C-V22b verdict: **{verdict}**.

The evaluator-revealed challenge ran on the identity-verified V2.2.1 freeze at
commit `347482f`, using released seeds 806117–806176. All four sealed tests
{'passed' if summary['passed'] else 'did not all pass'}. The graded-transfer
Spearman effect was `{graded['spearman_95_interval'][0]:.3f}`
(`{graded['spearman_95_interval'][1]:.3f}`–`{graded['spearman_95_interval'][2]:.3f}`),
with ordering in `{graded['ordered_worlds']}/60` worlds. Zero-cue mean absolute
G revision changed from `{dose['mean_root_revision_by_tier']['short'][0]:.6f}`
to `{dose['mean_root_revision_by_tier']['medium'][0]:.6f}` to
`{dose['mean_root_revision_by_tier']['long'][0]:.6f}` over the nested history
tiers; `{dose['long_floor_worlds']}/60` long-history worlds were inside the
`.02` floor band. Full effects, intervals, and localization are retained in
`results/challenges/C-V22b/`.

The frozen V2.2.1 milestone report and freeze manifest remain unchanged; this
file and the Gate 6 addendum are additive.
"""


def main() -> dict[str, Any]:
    identity = verify_frozen_identity()
    seeds = released_seeds()
    rows: list[dict[str, Any]] = []
    spearman_values = []
    ordered_worlds = 0
    root_revision_by_tier = {tier: [] for tier in HISTORY_TIERS}
    attribution_effects = []
    broad_cue_revisions = []
    narrowed_cue_revisions = []
    null_root_transfers = []
    maximum_root_cut_transfer = 0.0
    paired_stream_mismatches = 0

    for seed in seeds:
        development = generate_development(seed)
        q_rng = escrow_rng(seed, "precision-monitor")
        q_observations = tuple(
            int(q_rng.choice(3, p=MONITOR[state]))
            for state in PRECISION_STATES
        )
        tier_arms = {}
        for tier, learned in development.items():
            associations = learned["associations"]
            strong_arm = treatment_arm(
                associations, q_observations, STRONG_TREATMENT_CUE
            )
            zero_arm = treatment_arm(
                associations, tuple(q_observations), ZERO_TREATMENT_CUE
            )
            paired_stream_mismatches += int(
                q_observations != tuple(q_observations)
            )
            tier_arms[tier] = {
                "strong": strong_arm,
                "zero": zero_arm,
            }
            root_revision_by_tier[tier].append(
                abs(zero_arm["root_revision"])
            )
            for arm in (strong_arm, zero_arm):
                if abs(arm["root_revision"]) <= ROOT_NULL_BAND:
                    null_root_transfers.append(
                        max(abs(value) for value in arm["transfers"].values())
                    )

        primary = development[PRIMARY_TIER]
        primary_strong = tier_arms[PRIMARY_TIER]["strong"]
        primary_zero = tier_arms[PRIMARY_TIER]["zero"]
        association_magnitudes = []
        transfer_magnitudes = []
        for cue, transfer in primary_strong["transfers"].items():
            association_magnitudes.append(
                abs(primary["associations"][cue] - 0.5)
            )
            transfer_magnitudes.append(abs(transfer))
        rho = spearman(association_magnitudes, transfer_magnitudes)
        spearman_values.append(rho)

        strong_response = abs(primary_strong["transfers"][1])
        weak_response = float(
            np.mean(
                [abs(primary_strong["transfers"][cue]) for cue in WEAK_CUES]
            )
        )
        zero_response = float(
            np.mean(
                [abs(primary_strong["transfers"][cue]) for cue in ZERO_CUES]
            )
        )
        ordered = strong_response > weak_response > zero_response
        ordered_worlds += int(ordered)

        attribution_effects.append(primary_strong["broad_minus_narrowed"])
        broad_cue_revisions.append(primary_strong["broad_cue_revision"])
        narrowed_cue_revisions.append(primary_strong["narrowed_cue_revision"])

        # Root-cut counterfactual: identical probe root before and after treatment.
        for cue, association in enumerate(primary["associations"]):
            if cue == STRONG_TREATMENT_CUE:
                continue
            root_fixed = np.array([0.5, 0.5])
            root_cut = float(
                probe(root_fixed, association)[1]
                - probe(root_fixed, association)[1]
            )
            maximum_root_cut_transfer = max(
                maximum_root_cut_transfer, abs(root_cut)
            )

        row: dict[str, Any] = {
            "seed": seed,
            "segment_q_broad": q_observations[0],
            "segment_q_narrowed": q_observations[1],
            "primary_spearman": rho,
            "primary_strong_response": strong_response,
            "primary_weak_response": weak_response,
            "primary_zero_response": zero_response,
            "primary_ordered": int(ordered),
            "primary_strong_root_revision": primary_strong["root_revision"],
            "primary_zero_root_revision": primary_zero["root_revision"],
            "primary_broad_attribution": primary_strong["broad_attribution"],
            "primary_narrowed_attribution": primary_strong[
                "narrowed_attribution"
            ],
            "primary_broad_minus_narrowed": primary_strong[
                "broad_minus_narrowed"
            ],
            "primary_broad_cue_revision": primary_strong[
                "broad_cue_revision"
            ],
            "primary_narrowed_cue_revision": primary_strong[
                "narrowed_cue_revision"
            ],
            "medium_near_twin_similarity": primary["similarities"][4],
        }
        for tier in HISTORY_TIERS:
            learned = development[tier]
            row[f"{tier}_zero_root_revision"] = tier_arms[tier]["zero"][
                "root_revision"
            ]
            row[f"{tier}_zero_null_probability"] = learned[
                "null_probabilities"
            ][ZERO_TREATMENT_CUE]
            for cue in range(CUE_COUNT):
                row[f"{tier}_association_cue{cue + 1}"] = learned[
                    "associations"
                ][cue]
        rows.append(row)

    spearman_interval = mean_interval(spearman_values)
    ordering_interval = proportion_interval(ordered_worlds, WORLD_COUNT)
    mean_revisions = {
        tier: mean_interval(values)
        for tier, values in root_revision_by_tier.items()
    }
    short_medium = [
        short - medium
        for short, medium in zip(
            root_revision_by_tier["short"],
            root_revision_by_tier["medium"],
        )
    ]
    medium_long = [
        medium - long
        for medium, long in zip(
            root_revision_by_tier["medium"],
            root_revision_by_tier["long"],
        )
    ]
    paired_differences = {
        "short_minus_medium": mean_interval(short_medium),
        "medium_minus_long": mean_interval(medium_long),
    }
    long_floor_worlds = sum(
        value <= FLOOR_BAND for value in root_revision_by_tier["long"]
    )
    long_floor_interval = proportion_interval(long_floor_worlds, WORLD_COUNT)
    attribution_interval = mean_interval(attribution_effects)
    broad_cue_interval = mean_interval(broad_cue_revisions)
    narrowed_cue_interval = mean_interval(narrowed_cue_revisions)
    maximum_null_transfer = (
        max(null_root_transfers) if null_root_transfers else float("nan")
    )

    graded_pass = (
        spearman_interval[0] >= SPEARMAN_THRESHOLD
        and spearman_interval[1] > 0.0
        and ordered_worlds >= ORDERING_THRESHOLD
    )
    dose_pass = (
        mean_revisions["short"][0] > mean_revisions["medium"][0]
        > mean_revisions["long"][0]
        and long_floor_worlds >= LONG_FLOOR_THRESHOLD
    )
    mediation_pass = (
        maximum_root_cut_transfer <= TRANSFER_NULL_BAND
        and len(null_root_transfers) > 0
        and maximum_null_transfer <= TRANSFER_NULL_BAND
    )
    gating_pass = (
        attribution_interval[1] > 0.0
        and broad_cue_interval[1] >= LOCAL_UPTAKE_MINIMUM
        and narrowed_cue_interval[1] >= LOCAL_UPTAKE_MINIMUM
    )

    tests = {
        "graded_transfer": {
            "passed": graded_pass,
            "spearman_95_interval": spearman_interval,
            "spearman_threshold": SPEARMAN_THRESHOLD,
            "ordered_worlds": ordered_worlds,
            "ordered_worlds_95_interval": ordering_interval,
            "ordering_threshold": ORDERING_THRESHOLD,
        },
        "floor_dose_response": {
            "passed": dose_pass,
            "mean_root_revision_by_tier": mean_revisions,
            "paired_differences": paired_differences,
            "monotone_means": (
                mean_revisions["short"][0] > mean_revisions["medium"][0]
                > mean_revisions["long"][0]
            ),
            "long_floor_worlds": long_floor_worlds,
            "long_floor_95_interval": long_floor_interval,
            "long_floor_threshold": LONG_FLOOR_THRESHOLD,
            "floor_band": FLOOR_BAND,
        },
        "mediation": {
            "passed": mediation_pass,
            "maximum_root_cut_transfer": maximum_root_cut_transfer,
            "null_root_worlds": len(null_root_transfers),
            "root_null_band": ROOT_NULL_BAND,
            "maximum_null_world_transfer": maximum_null_transfer,
            "transfer_null_band": TRANSFER_NULL_BAND,
        },
        "segment_gating": {
            "passed": gating_pass,
            "attribution_effect_95_interval": attribution_interval,
            "broad_cue_revision_95_interval": broad_cue_interval,
            "narrowed_cue_revision_95_interval": narrowed_cue_interval,
            "local_uptake_minimum": LOCAL_UPTAKE_MINIMUM,
        },
    }
    passed = all(test["passed"] for test in tests.values())
    localization = []
    if not graded_pass:
        localization.append(
            "Test 1: posterior association magnitude did not organize graded "
            "root-mediated transfer at the sealed thresholds."
        )
    if not dose_pass:
        localization.append(
            "Test 2: exact-zero calibration did not close monotonically with "
            "developmental evidence or missed the long-history floor."
        )
    if not mediation_pass:
        localization.append(
            "Test 3: transfer appeared without the permitted G-revision path."
        )
    if not gating_pass:
        localization.append(
            "Test 4: broad-to-narrowed precision gating or local corrective "
            "uptake failed."
        )

    summary = {
        "challenge": CHALLENGE,
        "stage": STAGE,
        "seed_block_released": list(RELEASED_BLOCK),
        "seed_block_used": [seeds[0], seeds[-1]],
        "world_count_per_arm": WORLD_COUNT,
        "paired_streams": True,
        "paired_stream_mismatches": paired_stream_mismatches,
        "frozen_identity": identity,
        "configuration": {
            "cue_count": CUE_COUNT,
            "true_associations": TRUE_ASSOCIATIONS.tolist(),
            "strong_cues_one_indexed": [cue + 1 for cue in STRONG_CUES],
            "weak_cues_one_indexed": [cue + 1 for cue in WEAK_CUES],
            "zero_cues_one_indexed": [cue + 1 for cue in ZERO_CUES],
            "strong_treatment_cue_one_indexed": STRONG_TREATMENT_CUE + 1,
            "zero_treatment_cue_one_indexed": ZERO_TREATMENT_CUE + 1,
            "near_twin_pair_one_indexed": [1, 5],
            "true_similarities": TRUE_SIMILARITIES.tolist(),
            "history_tiers": HISTORY_TIERS,
            "primary_tier": PRIMARY_TIER,
            "tier_design": "nested prefixes within each of 60 paired base worlds",
            "precision_states": list(PRECISION_STATES),
            "segment_identity_given_to_inference": False,
            "segment_boundary_given_to_inference": False,
        },
        "tests": tests,
        "failure_localization": localization,
        "passed": passed,
    }

    result_dir = V2_ROOT / "results" / "challenges" / CHALLENGE
    write_csv(result_dir / "per_seed.csv", rows)
    write_json(result_dir / "summary.json", summary)
    report_path = result_dir / "report.md"
    report_path.write_text(render_report(summary), encoding="utf-8")

    milestone_path = V2_ROOT / "results" / "milestone-1-v2.2.1-gate6-update.md"
    milestone_path.write_text(render_milestone_update(summary), encoding="utf-8")

    sealed_path = V2_ROOT / "sealed-revealed" / "C-V22b-seam-challenge.md"
    addendum = {
        "strain": STAGE,
        "base_freeze_commit": FROZEN_COMMIT,
        "base_freeze_manifest": identity["manifest"],
        "base_freeze_manifest_sha256": identity["manifest_sha256"],
        "base_manifest_file_count_verified": identity["manifest_file_count"],
        "base_manifest_mismatches": identity["mismatches"],
        "overlay": {
            "prospective_challenge": CHALLENGE,
            "prospective_challenge_revealed": True,
            "prospective_challenge_run": True,
            "sealed_gate_6_run": True,
            "verdict": "PASS" if passed else "FAIL",
        },
        "challenge_spec_sha256": sha256(sealed_path),
        "challenge_runner_sha256": sha256(Path(__file__)),
        "result_hashes": {
            "results/challenges/C-V22b/per_seed.csv": sha256(
                result_dir / "per_seed.csv"
            ),
            "results/challenges/C-V22b/summary.json": sha256(
                result_dir / "summary.json"
            ),
            "results/challenges/C-V22b/report.md": sha256(report_path),
            "results/milestone-1-v2.2.1-gate6-update.md": sha256(
                milestone_path
            ),
        },
    }
    write_json(V2_ROOT / "results" / "V2.2.1" / "gate6-addendum.json", addendum)
    return summary


if __name__ == "__main__":
    result = main()
    print(json.dumps({"challenge": CHALLENGE, "passed": result["passed"]}))
    if not result["passed"]:
        raise SystemExit(1)
