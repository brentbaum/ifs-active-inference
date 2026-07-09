from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
EPS = 1e-12
MPLCONFIGDIR = ROOT / ".mplconfig"
MPLCONFIGDIR.mkdir(exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPLCONFIGDIR))

import matplotlib.pyplot as plt


@dataclass(frozen=True)
class Params:
    n_steps: int = 34
    gamma_l1_focused: float = 5.0
    gamma_l1_distracted: float = 0.65
    gamma_l2_high_meta: float = 1.5
    gamma_l2_low_meta: float = 0.85
    gamma_l2_min: float = 0.5
    gamma_l2_max: float = 8.0
    gamma_l2_lr: float = 0.0
    policy_horizon: int = 3
    refocus_cost: float = 5.0
    policy_precision: float = 8.0
    spontaneous_switch: float = 0.0
    seed: int = 11


def normalize(x: np.ndarray) -> np.ndarray:
    total = float(np.sum(x))
    if total <= EPS:
        return np.ones_like(x) / x.size
    return x / total


def softmax(x: np.ndarray, precision: float = 1.0) -> np.ndarray:
    z = precision * (x - np.max(x))
    exp_z = np.exp(z)
    return exp_z / np.sum(exp_z)


def sharpen_likelihood(base: np.ndarray, gamma: float) -> np.ndarray:
    """Column-normalized likelihood precision transform."""
    sharp = np.power(np.clip(base, EPS, 1.0), gamma)
    return sharp / np.sum(sharp, axis=0, keepdims=True)


def categorical_update(
    prior: np.ndarray,
    observation: int,
    base_likelihood: np.ndarray,
    gamma: float,
) -> np.ndarray:
    likelihood = sharpen_likelihood(base_likelihood, gamma)
    return normalize(likelihood[observation, :] * prior)


def oddball_sequence(n_steps: int, deviants: tuple[int, ...]) -> np.ndarray:
    seq = np.zeros(n_steps, dtype=int)
    for t in deviants:
        if 0 <= t < n_steps:
            seq[t] = 1
    return seq


def simulate_level1_precision(params: Params, precision: float) -> pd.DataFrame:
    base_a = np.array([[0.82, 0.18], [0.18, 0.82]], dtype=float)
    b = np.array([[0.90, 0.10], [0.10, 0.90]], dtype=float)
    observations = oddball_sequence(params.n_steps, (10, 20))
    q = np.array([0.90, 0.10], dtype=float)
    rows = []

    for t, obs in enumerate(observations):
        prior = normalize(b @ q)
        q = categorical_update(prior, int(obs), base_a, precision)
        rows.append(
            {
                "t": t,
                "observation_deviant": int(obs == 1),
                "q_standard": q[0],
                "q_deviant": q[1],
                "precision": precision,
            }
        )
    return pd.DataFrame(rows)


def policy_transition(policy: str) -> np.ndarray:
    if policy == "refocus":
        return np.array([[0.98, 0.92], [0.02, 0.08]], dtype=float)
    return np.array([[0.97, 0.04], [0.03, 0.96]], dtype=float)


def score_policy(q_attn: np.ndarray, policy: str, params: Params) -> float:
    preferences = np.array([0.985, 0.015], dtype=float)
    neg_log_pref = -np.log(preferences)
    q = q_attn.copy()
    score = 0.0
    b = policy_transition(policy)
    for depth in range(max(1, params.policy_horizon)):
        q = normalize(b @ q)
        discount = 1.0 / (1.0 + 0.15 * depth)
        score += discount * float(q @ neg_log_pref)
    if policy == "refocus":
        score += params.refocus_cost
    return score


def select_policy(q_attn: np.ndarray, params: Params) -> tuple[str, np.ndarray, dict[str, float]]:
    policies = ("maintain", "refocus")
    scores = {p: score_policy(q_attn, p, params) for p in policies}
    probs = softmax(-np.array([scores[p] for p in policies]), params.policy_precision)
    return policies[int(np.argmax(probs))], probs, scores


def simulate_attention_cycle(
    params: Params,
    meta_state: str = "high",
    distractors: tuple[int, ...] = (10,),
    adaptive_precision: bool = False,
) -> pd.DataFrame:
    rng = np.random.default_rng(params.seed)
    base_a2 = np.array([[0.78, 0.22], [0.22, 0.78]], dtype=float)
    base_a1 = np.array([[0.82, 0.18], [0.18, 0.82]], dtype=float)
    true_attn = 0
    q_attn = np.array([0.92, 0.08], dtype=float)
    q_perc = np.array([0.90, 0.10], dtype=float)
    gamma_target = (
        params.gamma_l2_high_meta if meta_state == "high" else params.gamma_l2_low_meta
    )
    gamma_l2 = gamma_target
    if adaptive_precision:
        gamma_l2 = params.gamma_l2_min if meta_state == "high" else params.gamma_l2_max
    observations_l1 = oddball_sequence(params.n_steps, distractors)
    rows = []

    for t in range(params.n_steps):
        forced = t in distractors
        if forced:
            true_attn = 1

        obs_attn = true_attn
        if rng.random() < params.spontaneous_switch:
            obs_attn = 1 - obs_attn

        prior_attn = normalize(policy_transition("maintain") @ q_attn)
        q_attn = categorical_update(prior_attn, int(obs_attn), base_a2, gamma_l2)

        gamma_l1 = (
            q_attn[0] * params.gamma_l1_focused
            + q_attn[1] * params.gamma_l1_distracted
        )
        prior_perc = normalize(np.array([[0.90, 0.10], [0.10, 0.90]]) @ q_perc)
        q_perc = categorical_update(prior_perc, int(observations_l1[t]), base_a1, gamma_l1)

        policy, policy_probs, scores = select_policy(q_attn, params)
        aware = bool(q_attn[1] >= 0.5)
        rows.append(
            {
                "t": t,
                "meta_state": meta_state,
                "true_attn": true_attn,
                "obs_attn": obs_attn,
                "q_focused": q_attn[0],
                "q_distracted": q_attn[1],
                "q_deviant": q_perc[1],
                "gamma_l1": gamma_l1,
                "gamma_l2": gamma_l2,
                "policy": policy,
                "p_refocus": policy_probs[1],
                "score_maintain": scores["maintain"],
                "score_refocus": scores["refocus"],
                "aware": aware,
                "forced_distractor": forced,
            }
        )

        if adaptive_precision:
            gamma_l2 = gamma_l2 + params.gamma_l2_lr * (gamma_target - gamma_l2)
            gamma_l2 = float(np.clip(gamma_l2, params.gamma_l2_min, params.gamma_l2_max))

        if policy == "refocus" and aware:
            true_attn = 0

    return pd.DataFrame(rows)


def dwell_times(df: pd.DataFrame, distractors: tuple[int, ...]) -> list[int]:
    dwell = []
    for start in distractors:
        after = df[df["t"] >= start]
        aware_rows = after[after["aware"]]
        if aware_rows.empty:
            dwell.append(int(df["t"].max() - start + 1))
        else:
            dwell.append(int(aware_rows.iloc[0]["t"] - start + 1))
    return dwell


def summarize_attention(df: pd.DataFrame, distractors: tuple[int, ...]) -> dict[str, float]:
    dwell = dwell_times(df, distractors)
    refocuses = int((df["policy"] == "refocus").sum())
    switches = int((df["policy"] != df["policy"].shift()).sum() - 1)
    return {
        "mean_dwell": float(np.mean(dwell)),
        "max_dwell": float(np.max(dwell)),
        "refocus_count": refocuses,
        "policy_switches": switches,
        "gamma_l2_min": float(df["gamma_l2"].min()),
        "gamma_l2_max": float(df["gamma_l2"].max()),
    }


def precision_oscillation_score(series: pd.Series) -> tuple[int, float]:
    delta = np.diff(series.to_numpy(dtype=float))
    meaningful = delta[np.abs(delta) > 1e-8]
    if meaningful.size < 3:
        return 0, 0.0
    sign_changes = int(np.sum(np.sign(meaningful[1:]) != np.sign(meaningful[:-1])))
    amplitude = float(np.max(series) - np.min(series))
    return sign_changes, amplitude


def run_stability_sweep() -> pd.DataFrame:
    rows = []
    base = Params(n_steps=42, seed=7)
    for gamma_min, gamma_max in [(0.3, 6.0), (0.5, 8.0), (0.8, 10.0), (0.2, 14.0)]:
        for lr in [0.0, 0.3, 0.8, 1.2, 1.8, 2.2, 2.8]:
            for horizon in [1, 3, 5, 8, 12]:
                params = replace(
                    base,
                    gamma_l2_min=gamma_min,
                    gamma_l2_max=gamma_max,
                    gamma_l2_high_meta=min(5.0, gamma_max),
                    gamma_l2_low_meta=max(0.85, gamma_min),
                    gamma_l2_lr=lr,
                    policy_horizon=horizon,
                )
                for meta in ["high", "low"]:
                    df = simulate_attention_cycle(
                        params,
                        meta_state=meta,
                        distractors=(10, 20, 30),
                        adaptive_precision=True,
                    )
                    summary = summarize_attention(df, (10, 20, 30))
                    sign_changes, amplitude = precision_oscillation_score(df["gamma_l2"])
                    dwell = dwell_times(df, (10, 20, 30))
                    stable = (
                        all(1 <= d <= 8 for d in dwell)
                        and summary["policy_switches"] <= 8
                        and sign_changes <= 2
                        and amplitude <= (gamma_max - gamma_min + 1e-9)
                    )
                    rows.append(
                        {
                            "meta_state": meta,
                            "gamma_min": gamma_min,
                            "gamma_max": gamma_max,
                            "gamma_l2_lr": lr,
                            "policy_horizon": horizon,
                            "stable": stable,
                            "dwell_times": ";".join(str(d) for d in dwell),
                            "precision_sign_changes": sign_changes,
                            "precision_amplitude": amplitude,
                            **summary,
                        }
                    )
    return pd.DataFrame(rows)


def plot_figure_6(high: pd.DataFrame, low: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.8), sharex=True, constrained_layout=True)
    for ax, df, title in [
        (axes[0], high, "high precision on A(1)"),
        (axes[1], low, "low precision on A(1)"),
    ]:
        heat = np.vstack([df["q_standard"], df["q_deviant"]])
        ax.imshow(heat, aspect="auto", cmap="Greys", vmin=0, vmax=1, interpolation="nearest")
        ax.plot(df["observation_deviant"] * 0.85 + 0.05, color="#d04a02", lw=1.8)
        ax.set_yticks([0, 1], ["standard", "deviant"])
        ax.set_title(title)
        ax.set_ylabel("posterior")
    axes[-1].set_xlabel("time")
    fig.suptitle("Paper Figure 6 analogue: perceptual precision controls evidence accumulation")
    fig.savefig(OUT / "paper_figure_6_precision_oddball.png", dpi=180)
    plt.close(fig)


def plot_figure_8(df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(4, 1, figsize=(10, 8), sharex=True, constrained_layout=True)
    t = df["t"]
    axes[0].step(t, df["true_attn"], where="post", color="black", label="true distracted")
    axes[0].plot(t, df["q_distracted"], color="#1f77b4", lw=2, label="q(Distracted)")
    axes[0].axvline(10, color="#d04a02", ls="--", lw=1)
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].legend(loc="upper right")
    axes[0].set_ylabel("level 2")

    axes[1].plot(t, df["gamma_l1"], color="#2ca02c", lw=2)
    axes[1].set_ylabel("A(1) precision")

    axes[2].plot(t, df["q_deviant"], color="#9467bd", lw=2)
    axes[2].set_ylabel("q deviant")
    axes[2].set_ylim(-0.05, 1.05)

    axes[3].plot(t, df["p_refocus"], color="#8c564b", lw=2, label="P(refocus)")
    axes[3].scatter(
        df.loc[df["policy"] == "refocus", "t"],
        np.ones((df["policy"] == "refocus").sum()),
        color="#d62728",
        s=24,
        label="selected",
    )
    axes[3].set_ylim(-0.05, 1.05)
    axes[3].set_xlabel("time")
    axes[3].set_ylabel("mental action")
    axes[3].legend(loc="upper right")
    fig.suptitle("Paper Figure 8 analogue: capture, awareness, and return by mental action")
    fig.savefig(OUT / "paper_figure_8_attention_capture_return.png", dpi=180)
    plt.close(fig)


def plot_figure_10(high: pd.DataFrame, low: pd.DataFrame) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(10, 7.2), sharex=True, constrained_layout=True)
    t = high["t"]
    for ax in axes:
        for d in [10, 20]:
            ax.axvline(d, color="#d04a02", ls="--", lw=1, alpha=0.8)

    axes[0].plot(t, high["q_distracted"], color="#1f77b4", lw=2, label="high meta-awareness")
    axes[0].plot(t, low["q_distracted"], color="#ff7f0e", lw=2, label="low meta-awareness")
    axes[0].set_ylim(-0.05, 1.05)
    axes[0].set_ylabel("q(Distracted)")
    axes[0].legend(loc="upper right")

    axes[1].plot(t, high["gamma_l2"], color="#1f77b4", lw=2)
    axes[1].plot(t, low["gamma_l2"], color="#ff7f0e", lw=2)
    axes[1].set_ylabel("A(2) precision")

    high_awake = high[high["aware"]]
    low_awake = low[low["aware"]]
    axes[2].plot(t, high["p_refocus"], color="#1f77b4", lw=2)
    axes[2].plot(t, low["p_refocus"], color="#ff7f0e", lw=2)
    axes[2].scatter(high_awake["t"], np.full(len(high_awake), 0.92), color="#1f77b4", s=18)
    axes[2].scatter(low_awake["t"], np.full(len(low_awake), 0.78), color="#ff7f0e", s=18)
    axes[2].set_ylim(-0.05, 1.05)
    axes[2].set_ylabel("P(refocus)")
    axes[2].set_xlabel("time")

    fig.suptitle("Paper Figure 10 analogue: meta-awareness shortens distracted dwell time")
    fig.savefig(OUT / "paper_figure_10_meta_awareness_dwell.png", dpi=180)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    params = Params()

    fig6_high = simulate_level1_precision(params, params.gamma_l1_focused)
    fig6_low = simulate_level1_precision(params, params.gamma_l1_distracted)
    fig8 = simulate_attention_cycle(params, meta_state="high", distractors=(10,))
    fig10_high = simulate_attention_cycle(params, meta_state="high", distractors=(10, 20))
    fig10_low = simulate_attention_cycle(params, meta_state="low", distractors=(10, 20))

    plot_figure_6(fig6_high, fig6_low)
    plot_figure_8(fig8)
    plot_figure_10(fig10_high, fig10_low)

    fig6_high.to_csv(OUT / "figure_6_high_precision_trace.csv", index=False)
    fig6_low.to_csv(OUT / "figure_6_low_precision_trace.csv", index=False)
    fig8.to_csv(OUT / "figure_8_trace.csv", index=False)
    fig10_high.to_csv(OUT / "figure_10_high_meta_trace.csv", index=False)
    fig10_low.to_csv(OUT / "figure_10_low_meta_trace.csv", index=False)

    sweep = run_stability_sweep()
    sweep.to_csv(OUT / "stability_envelope.csv", index=False)
    stable = sweep[sweep["stable"]]

    summary = {
        "params": asdict(params),
        "figure_8": summarize_attention(fig8, (10,)),
        "figure_10_high_meta": summarize_attention(fig10_high, (10, 20)),
        "figure_10_low_meta": summarize_attention(fig10_low, (10, 20)),
        "stability_sweep": {
            "rows": int(len(sweep)),
            "stable_rows": int(len(stable)),
            "stable_fraction": float(len(stable) / len(sweep)),
            "stable_lr_max": float(stable["gamma_l2_lr"].max()) if not stable.empty else math.nan,
            "stable_horizon_max": int(stable["policy_horizon"].max()) if not stable.empty else 0,
            "safe_precision_bounds_observed": sorted(
                {
                    f"{row.gamma_min:g}-{row.gamma_max:g}"
                    for row in stable[["gamma_min", "gamma_max"]].drop_duplicates().itertuples()
                }
            ),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
