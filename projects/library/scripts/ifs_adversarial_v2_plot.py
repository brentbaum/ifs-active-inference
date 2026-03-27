from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
FIGURE_DIR = ROOT / "projects" / "ifs-paper" / "figures" / "v2" / "adversarial"
DATA_DIR = FIGURE_DIR / "data"

COLORS = {
    "gray": "#666666",
    "blue": "#5478a6",
    "accent": "#c45a3c",
    "bg": "#fffff8",
    "grid": "#d9d9d9",
    "green": "#64935e",
    "light_gray": "#b8b8b8",
    "soft_blue": "#92abca",
    "soft_taupe": "#b3a697",
}

CHANNEL_COLORS = {
    1: COLORS["light_gray"],
    2: COLORS["soft_blue"],
    3: COLORS["soft_taupe"],
    4: COLORS["blue"],
    5: COLORS["accent"],
}


def configure():
    plt.rcParams.update(
        {
            "figure.facecolor": COLORS["bg"],
            "axes.facecolor": COLORS["bg"],
            "savefig.facecolor": COLORS["bg"],
            "font.family": "serif",
            "font.serif": ["Georgia", "Times New Roman", "DejaVu Serif"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
        }
    )


def onset_x(x, y, min_fraction=0.10, floor=0.01):
    peak = float(y.max())
    threshold = max(floor, peak * min_fraction)
    hits = y >= threshold
    if not hits.any():
        return None
    return float(x[hits.idxmax()]) if hasattr(hits, "idxmax") else float(x[hits.argmax()])


def tufte(ax):
    ax.spines["left"].set_color(COLORS["gray"])
    ax.spines["bottom"].set_color(COLORS["gray"])
    ax.tick_params(colors=COLORS["gray"])
    return ax


def plot_test1():
    df = pd.read_csv(DATA_DIR / "test1_alpha_linear.tsv", sep="\t")
    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
    ax.plot(df["E_t"], df["base_mean"], color=COLORS["accent"], label="alpha = 3", lw=2.2)
    ax.fill_between(df["E_t"], df["base_mean"] - df["base_std"], df["base_mean"] + df["base_std"], color=COLORS["accent"], alpha=0.14)
    ax.plot(df["E_t"], df["linear_mean"], color=COLORS["blue"], label="alpha = 1", lw=2.0)
    ax.fill_between(df["E_t"], df["linear_mean"] - df["linear_std"], df["linear_mean"] + df["linear_std"], color=COLORS["blue"], alpha=0.12)
    ax.set_title("Linear Gate Softens the Eruption but Does Not Remove It")
    ax.set_xlabel("Self-energy E_t")
    ax.set_ylabel("Channel 5 epistemic value")
    ax.legend(frameon=False, loc="upper left")
    base_onset = onset_x(df["E_t"], df["base_mean"])
    if base_onset is not None:
        ax.axvline(base_onset, color=COLORS["accent"], lw=1.0, ls=":")
        ax.text(base_onset + 0.01, df["base_mean"].max() * 0.88, f"alpha=3 onset {base_onset:.2f}", color=COLORS["accent"], fontsize=8)
    linear_onset = onset_x(df["E_t"], df["linear_mean"])
    if linear_onset is not None:
        ax.text(linear_onset + 0.01, df["linear_mean"].max() * 0.72, f"alpha=1 onset {linear_onset:.2f}", color=COLORS["blue"], fontsize=8)
    tufte(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test1_alpha_linear.png")
    plt.close(fig)


def plot_test2():
    df = pd.read_csv(DATA_DIR / "test2_threshold_robustness.tsv", sep="\t")
    fig, ax = plt.subplots(figsize=(8.8, 5.0), dpi=300)
    x = range(len(df))
    ax.errorbar(list(x), df["onset_mean"], yerr=df["onset_std"], fmt="o", color=COLORS["accent"], ecolor=COLORS["gray"], elinewidth=1.3, capsize=0)
    ax.axhline(0.60, color=COLORS["grid"], lw=1.0, ls="--")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["label"], rotation=35, ha="right")
    ax.set_ylim(0.35, 0.75)
    ax.set_ylabel("Onset E_t")
    ax.set_xlabel("Perturbation")
    ax.set_title("Threshold Location Stays Clustered Under ±20% Perturbations")
    tufte(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test2_threshold_robustness.png")
    plt.close(fig)


def plot_test3():
    df = pd.read_csv(DATA_DIR / "test3_no_channel5.tsv", sep="\t")
    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
    for channel, group in df.groupby("channel"):
        ax.plot(group["E_t"], group["epistemic_value"], color=CHANNEL_COLORS[int(channel)], lw=2.0 if int(channel) == 5 else 1.8, label=f"Channel {int(channel)}")
    ax.set_title("Without Channel 5, No Other Channel Produces the Same Late Eruption")
    ax.set_xlabel("Self-energy E_t")
    ax.set_ylabel("Epistemic value")
    ax.legend(frameon=False, loc="upper left")
    tufte(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test3_no_channel5.png")
    plt.close(fig)


def plot_test4():
    gate = pd.read_csv(DATA_DIR / "test4_fake_channel5_gate.tsv", sep="\t")
    cascade = pd.read_csv(DATA_DIR / "test4_fake_channel5_cascade.tsv", sep="\t")

    fig, axes = plt.subplots(2, 1, figsize=(7.8, 8.8), dpi=300)

    ax = axes[0]
    ax.plot(gate["E_t"], gate["original_mean"], color=COLORS["accent"], label="Original self-state content", lw=2.2)
    ax.fill_between(gate["E_t"], gate["original_mean"] - gate["original_std"], gate["original_mean"] + gate["original_std"], color=COLORS["accent"], alpha=0.14)
    ax.plot(gate["E_t"], gate["fake_mean"], color=COLORS["blue"], label="Fake threat content", lw=2.0)
    ax.fill_between(gate["E_t"], gate["fake_mean"] - gate["fake_std"], gate["fake_mean"] + gate["fake_std"], color=COLORS["blue"], alpha=0.12)
    ax.set_title("The Gate Still Opens When Channel 5 Carries Threat Content")
    ax.set_xlabel("Self-energy E_t")
    ax.set_ylabel("Channel 5 epistemic value")
    ax.legend(frameon=False, loc="upper left")
    tufte(ax)

    ax = axes[1]
    ax.plot(cascade["E_t"], cascade["self_mean"], color=COLORS["accent"], label="Self-state", lw=2.1)
    ax.plot(cascade["E_t"], cascade["threat_mean"], color=COLORS["blue"], label="Threat", lw=1.9)
    ax.plot(cascade["E_t"], cascade["outcome_mean"], color=COLORS["green"], label="Outcome", lw=1.9)
    ax.plot(cascade["E_t"], cascade["policy_mean"], color=COLORS["gray"], label="P(approach/stay)", lw=1.9)
    ax.set_title("But the Downstream Cascade Weakens When Channel 5 Stops Observing Self-State")
    ax.set_xlabel("Self-energy E_t")
    ax.set_ylabel("Belief / action probability")
    ax.legend(frameon=False, loc="lower right")
    tufte(ax)

    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test4_fake_channel5.png")
    plt.close(fig)


def plot_test5():
    df = pd.read_csv(DATA_DIR / "test5_constant_Et.tsv", sep="\t")
    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
    ax.plot(df["time_step"], df["mean_epistemic"], color=COLORS["accent"], lw=2.2)
    ax.fill_between(df["time_step"], df["mean_epistemic"] - df["std_epistemic"], df["mean_epistemic"] + df["std_epistemic"], color=COLORS["accent"], alpha=0.14)
    peak = df.loc[df["mean_epistemic"].idxmax()]
    ax.scatter([peak["time_step"]], [peak["mean_epistemic"]], color=COLORS["accent"], s=14)
    ax.text(peak["time_step"] + 0.6, peak["mean_epistemic"], "early spike", color=COLORS["accent"], fontsize=8)
    ax.text(df["time_step"].iloc[-6], df["mean_epistemic"].iloc[-1] + 0.01, "near-zero tail", color=COLORS["gray"], fontsize=8)
    ax.set_title("At Constant Relational Depth, Channel 5 Curiosity Is Brief")
    ax.set_xlabel("Time step")
    ax.set_ylabel("Channel 5 epistemic value")
    tufte(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test5_constant_Et.png")
    plt.close(fig)


def plot_test6():
    df = pd.read_csv(DATA_DIR / "test6_revision_speed.tsv", sep="\t")
    fig, ax = plt.subplots(figsize=(7.6, 5.0), dpi=300)
    ax.plot(df["E_t"], df["mean_delta"], color=COLORS["accent"], lw=2.2)
    ax.fill_between(df["E_t"], df["mean_delta"] - df["std_delta"], df["mean_delta"] + df["std_delta"], color=COLORS["accent"], alpha=0.14)
    ax.axhline(0.0, color=COLORS["grid"], lw=1.0)
    onset = onset_x(df["E_t"], df["mean_delta"], floor=0.002)
    if onset is not None:
        ax.axvline(onset, color=COLORS["accent"], lw=1.0, ls=":")
        ax.text(onset + 0.01, df["mean_delta"].max() * 0.88, f"onset {onset:.2f}", color=COLORS["accent"], fontsize=8)
    ax.set_title("Revision Speed Shows the Same Narrow Emergence Window")
    ax.set_xlabel("Self-energy E_t")
    ax.set_ylabel("Δ P(capable / present)")
    tufte(ax)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "test6_revision_speed.png")
    plt.close(fig)


def main():
    configure()
    plot_test1()
    plot_test2()
    plot_test3()
    plot_test4()
    plot_test5()
    plot_test6()


if __name__ == "__main__":
    main()
