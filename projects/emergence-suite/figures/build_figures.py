#!/usr/bin/env python3
"""Build paper-grade Emergence Suite figures from preregistered run artifacts."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR",
    "/private/tmp/ifs-active-inference-matplotlib-cache",
)
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle


ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent

RUN = ROOT / "projects/emergence-suite/suite/runs"
SIM1 = RUN / "sim1/sim1-t1-2"
SIM2 = RUN / "sim2/preregistered"
SIM3 = RUN / "sim3/preregistered"
SIM4 = RUN / "sim4/preregistered"
SIM5 = RUN / "sim5/preregistered"
SIM6A = RUN / "sim6a/stage2-preregistered"
SIM7 = RUN / "sim7/preregistered"
SIM6C = ROOT / "projects/emergence-suite/continuous/results/sim6a_continuous_stage3"

ACCENT = "#0B6E69"
ACCENT2 = "#8C3F2B"
GREY = "#6B6F72"
LIGHT = "#D9D9D4"
DARK = "#202124"
MUTED = "#9EA2A2"
H2 = "#4D4D4D"
EXPOSURE = "#8E6F52"
DISS = "#A8A29E"
INFO = "#B9B9B2"

COND_COLORS = {
    "witnessing": ACCENT,
    "H1-witnessing": ACCENT,
    "full-life": ACCENT,
    "regulated": ACCENT,
    "contact-under-capture": "#888C8C",
    "dissociative-quiet": DISS,
    "informational": INFO,
    "H1-exposure": EXPOSURE,
    "H2-witnessing": H2,
    "h2-life": H2,
    "resilient-world": "#B8B8B2",
    "fluent-but-threatened": ACCENT2,
    "dysregulated": "#A7A7A2",
    "regulation-only": "#C4C4BF",
}

PROVENANCE: dict[str, list[tuple[str, str]]] = {}


def setup() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.2,
            "figure.dpi": 180,
            "savefig.dpi": 300,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.6,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
        }
    )


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def panel(ax, letter: str) -> None:
    ax.text(-0.08, 1.04, letter, transform=ax.transAxes, fontweight="bold", fontsize=10, va="bottom")


def finish(fig: plt.Figure, stem: str) -> None:
    for ext in ("svg", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight")
    plt.close(fig)


def mean_ci(df: pd.DataFrame, by: list[str], value: str) -> pd.DataFrame:
    g = df.groupby(by)[value]
    out = g.agg(["mean", "count", "std"]).reset_index()
    out["ci"] = 1.96 * out["std"].fillna(0) / np.sqrt(out["count"].clip(lower=1))
    out["lo"] = out["mean"] - out["ci"]
    out["hi"] = out["mean"] + out["ci"]
    return out


def norm(s: pd.Series | np.ndarray) -> np.ndarray:
    a = np.asarray(s, dtype=float)
    lo, hi = np.nanmin(a), np.nanmax(a)
    return np.zeros_like(a) if hi == lo else (a - lo) / (hi - lo)


def plot_band(ax, frame, x, y, color, label=None, alpha=0.18, lw=1.8, ls="-"):
    ax.plot(frame[x], frame["mean"], color=color, lw=lw, label=label, ls=ls)
    ax.fill_between(
        frame[x].to_numpy(float),
        frame["lo"].to_numpy(float),
        frame["hi"].to_numpy(float),
        color=color,
        alpha=alpha,
        lw=0,
    )


def figure_1():
    files = [SIM1 / "cell_metrics.csv", SIM1 / "posterior_traces.csv", SIM1 / "summary.json"]
    PROVENANCE["F1"] = [
        ("phase diagram cells, frozen region, attenuation band", rel(files[0])),
        ("slow-accumulation life path and crossing point", rel(files[1])),
        ("acute-region and slow-path thresholds", rel(files[2])),
    ]
    cells = pd.read_csv(files[0])
    trace = pd.read_csv(files[1])
    summary = json.load(open(files[2]))

    omegas = np.sort(cells.omega.unique())
    kappas = np.sort(cells.kappa.unique())
    z = cells.pivot(index="kappa", columns="omega", values="frozen_rate").loc[kappas, omegas]
    frozen = cells.pivot(index="kappa", columns="omega", values="frozen_rate").loc[kappas, omegas]
    atten = cells.pivot(index="kappa", columns="omega", values="attenuation_rate").loc[kappas, omegas]
    frozen_mask = frozen.values >= 0.5
    assert int(frozen_mask.sum()) == int(summary["metrics"]["frozen_cell_count"])

    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    cmap = LinearSegmentedColormap.from_list("frozen_rate", ["#F2F0EA", "#0B6E69", "#052E2C"])
    dx = float(np.median(np.diff(omegas)))
    dy = float(np.median(np.diff(kappas)))
    im = ax.imshow(
        z.values,
        origin="lower",
        extent=[omegas.min() - dx / 2, omegas.max() + dx / 2, kappas.min() - dy / 2, kappas.max() + dy / 2],
        aspect="auto",
        cmap=cmap,
        vmin=0,
        vmax=0.75,
    )
    ax.contourf(
        omegas,
        kappas,
        atten.values,
        levels=[0.5, float(np.nanmax(atten.values)) + 0.01],
        colors=[DARK],
        alpha=0.14,
    )
    ax.contour(omegas, kappas, frozen_mask.astype(float), levels=[0.5], colors=[DARK], linewidths=1.8)
    for k_i, kappa in enumerate(kappas):
        for o_i, omega in enumerate(omegas):
            if frozen_mask[k_i, o_i]:
                ax.add_patch(Rectangle((omega - dx / 2, kappa - dy / 2), dx, dy, fill=False, edgecolor=DARK, linewidth=0.45))

    # Acute route as a single strike into the frozen boundary.
    strike = (1.58, 0.11)
    ax.scatter([strike[0]], [strike[1]], s=42, color=ACCENT, edgecolor="white", linewidth=0.7, zorder=7)
    ax.annotate(
        "single strike",
        xy=strike,
        xytext=(1.36, 0.24),
        arrowprops=dict(arrowstyle="-", color=ACCENT, lw=0.8),
        color=ACCENT,
        fontsize=7.5,
        ha="right",
    )

    slow = trace[trace.seed.eq(trace.seed.min())].copy()
    slow["kplot"] = 0.035 + 0.018 * np.sin(np.linspace(0, 5 * np.pi, len(slow)))
    ax.plot(slow.per_trial_omega, slow.kplot, color=DARK, lw=1.1, alpha=0.95, zorder=5)
    cross = slow[slow.crossed.astype(bool)].head(1)
    if not cross.empty:
        cx = float(cross.per_trial_omega.iloc[0])
        cy = float(cross.kplot.iloc[0])
        ax.scatter([cx], [cy], s=38, color=DARK, zorder=8, marker="D")
        ax.annotate(
            "count crossing",
            xy=(cx, cy),
            xytext=(1.10, 0.145),
            arrowprops=dict(arrowstyle="-", lw=0.75, color=DARK),
            fontsize=7.3,
            color=DARK,
        )
    ax.annotate(
        "slow accumulation",
        xy=(0.74, 0.045),
        xytext=(0.42, 0.18),
        arrowprops=dict(arrowstyle="-", lw=0.75, color=DARK),
        fontsize=7.3,
        color=DARK,
    )

    ax.text(
        2.72,
        0.12,
        "shutdown /\nattenuation",
        fontsize=7.2,
        color=DARK,
        ha="center",
        va="center",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.72, pad=0.8),
    )
    ax.text(2.45, 0.29, "frozen", fontsize=8.0, color="white", ha="center", va="center", fontweight="bold")
    ax.text(0.82, 0.86, "ordinary\nlearning", fontsize=7.6, color=DARK, ha="center", va="center")
    ax.set_xlabel("overwhelm $\\omega$")
    ax.set_ylabel("control $\\kappa$")
    ax.set_xlim(0.1, 3.1)
    ax.set_ylim(-0.05, 1.45)
    cb = fig.colorbar(im, ax=ax, pad=0.018, fraction=0.055)
    cb.set_label("frozen rate")
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=ACCENT, markeredgecolor="white", markersize=6, label="single strike"),
        Line2D([0], [0], color=DARK, lw=1.1, label="slow path"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor=DARK, markersize=5, label="crossing"),
        Patch(facecolor=DARK, alpha=0.14, edgecolor="none", label="attenuation band"),
        Line2D([0], [0], color=DARK, lw=1.8, label="frozen boundary"),
    ]
    ax.legend(handles=handles, frameon=True, framealpha=0.94, facecolor="white", edgecolor="#D8D8D2", loc="upper left", ncol=1)
    panel(ax, "A")
    finish(fig, "F1_freezing_phase_diagram")


def figure_2():
    files = [SIM2 / "posterior_traces.csv", SIM2 / "prompt_probe_metrics.csv"]
    PROVENANCE["F2"] = [
        ("four regime structural-root trajectories and prune markers", rel(files[0])),
        ("premature-vs-late prompt inset", rel(files[1])),
    ]
    tr = pd.read_csv(files[0])
    prompt = pd.read_csv(files[1])
    order = ["informational", "contact-under-capture", "dissociative-quiet", "witnessing"]

    fig = plt.figure(figsize=(6.4, 4.0))
    ax = fig.add_subplot(111)
    for cond in order:
        f = mean_ci(tr[tr.condition.eq(cond)], ["condition", "cumulative_corrective_evidence"], "structural_root_precision")
        color = COND_COLORS[cond]
        lw = 2.3 if cond == "witnessing" else 1.2
        alpha = 0.2 if cond == "witnessing" else 0.10
        plot_band(ax, f, "cumulative_corrective_evidence", "structural_root_precision", color, cond.replace("-", " "), alpha=alpha, lw=lw)

    wp = tr[(tr.condition.eq("witnessing")) & (tr.pruned_now.astype(bool))]
    if not wp.empty:
        ev = float(wp.cumulative_corrective_evidence.mean())
        y = float(wp.structural_root_precision.mean())
        ax.axvline(ev, color=ACCENT, lw=1.0, ls="--")
        ax.scatter([ev], [y], s=46, color=ACCENT, edgecolor="white", linewidth=0.7, zorder=6)
        ax.text(ev + 1.2, y + 5, "BMR prune", color=ACCENT, fontsize=7.5)

    ax.set_xlabel("cumulative corrective evidence")
    ax.set_ylabel("structural root precision")
    ax.set_xlim(0, tr.cumulative_corrective_evidence.max())
    ax.legend(frameon=False, loc="upper left", ncol=1)
    panel(ax, "A")

    ax.add_patch(
        Rectangle(
            (0.60, 0.45),
            0.36,
            0.43,
            transform=ax.transAxes,
            facecolor="white",
            edgecolor="none",
            zorder=4,
        )
    )
    ins = ax.inset_axes([0.62, 0.47, 0.31, 0.38], zorder=5)
    ins.set_facecolor("white")
    ins.patch.set_alpha(1.0)
    ins.set_zorder(5)
    p = prompt.groupby("prompt_phase").agg(score=("bmr_score", "mean"), fail=("failed", "mean")).reindex(["early", "late"])
    xs = np.arange(len(p))
    colors = [MUTED, ACCENT]
    ins.axhline(0, color="#777", lw=0.7)
    ins.bar(xs, p.score, color=colors, width=0.58)
    for i, v in enumerate(p.fail):
        ins.text(i, p.score.iloc[i] + (0.25 if p.score.iloc[i] >= 0 else -0.45), f"fail {v:.0%}", ha="center", fontsize=6.5)
    ins.set_xticks(xs, ["early", "late"])
    ins.set_ylabel("BMR score", fontsize=7)
    ins.tick_params(labelsize=6.5)
    ins.spines["top"].set_visible(False)
    ins.spines["right"].set_visible(False)
    finish(fig, "F2_hysteresis_loop")


def figure_3():
    files = [SIM3 / "summary.json"]
    PROVENANCE["F3"] = [
        ("condition cue transfer, structural-confound outlier, E_t threshold sweep", rel(files[0])),
    ]
    s = json.load(open(files[0]))
    conds = [("H1-witnessing", ACCENT), ("H1-exposure", EXPOSURE), ("H2-witnessing", H2)]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.9), sharex=True, sharey=True)
    for ax, (cond, color) in zip(axes, conds):
        cues = pd.DataFrame(s["conditions"][cond]["cues"])
        main = cues[~cues.structural_confound].sort_values("root_coupling")
        ax.plot(main.root_coupling, main.mean_contact, color=color, lw=1.8)
        ax.scatter(main.root_coupling, main.mean_contact, s=24, color=color, zorder=3)
        conf = cues[cues.structural_confound].iloc[0]
        ax.scatter([conf.root_coupling], [conf.mean_contact], s=38, marker="x", color=DARK, lw=1.4, zorder=4)
        if cond == "H1-witnessing":
            ax.annotate(
                "perceptually near,\nstructurally uncoupled",
                xy=(conf.root_coupling, conf.mean_contact),
                xytext=(0.12, 0.45),
                arrowprops=dict(arrowstyle="-", lw=0.7, color=DARK),
                fontsize=6.8,
            )
        ax.set_xlim(-0.04, 1.04)
        ax.set_ylim(-0.03, 1.05)
        ax.set_xlabel("root coupling")
        ax.text(0.03, 0.95, cond.replace("-witnessing", "\nwitnessing").replace("-exposure", "\nexposure"), transform=ax.transAxes, va="top", fontsize=7.3)
        ax.grid(axis="y", color="#ECECEA", lw=0.5)
    axes[0].set_ylabel("transfer: P(contact)")
    panel(axes[0], "A")

    ins = axes[2].inset_axes([0.16, 0.18, 0.76, 0.45])
    et = pd.DataFrame({"E_t": s["metrics"]["e_t_readout"]["E_values"], "transfer": s["metrics"]["e_t_readout"]["transfer_values"]})
    ins.plot(et.E_t, et.transfer, color=ACCENT, lw=1.6)
    ins.fill_between(et.E_t, 0, et.transfer, color=ACCENT, alpha=0.12)
    ins.axvline(et.loc[et.transfer.gt(0.01).idxmax(), "E_t"], color=DARK, ls="--", lw=0.8)
    ins.set_xlabel("$E_t$", fontsize=6.8)
    ins.set_ylabel("transfer", fontsize=6.8)
    ins.tick_params(labelsize=6.3)
    ins.spines["top"].set_visible(False)
    ins.spines["right"].set_visible(False)
    finish(fig, "F3_generalization_gradient")


def figure_4():
    files = [SIM4 / "posterior_traces.csv", SIM4 / "per_seed_metrics.csv", SIM4 / "forced_direct_access.csv"]
    PROVENANCE["F4"] = [
        ("gate state, trust curves, and contact-choice raster", rel(files[0])),
        ("permission and deep-revision first-passage sessions", rel(files[1])),
        ("forced-direct-access flood/thickening panel", rel(files[2])),
    ]
    tr = pd.read_csv(files[0])
    met = pd.read_csv(files[1])
    forced = pd.read_csv(files[2])
    seed = tr.seed.min()
    one = tr[tr.seed.eq(seed)]

    fig = plt.figure(figsize=(7.0, 4.8))
    gs = GridSpec(3, 2, figure=fig, width_ratios=[3.4, 1.15], height_ratios=[1.15, 1.0, 0.75], hspace=0.22, wspace=0.32)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[1, 0], sharex=ax1)
    ax3 = fig.add_subplot(gs[2, 0], sharex=ax1)
    ax4 = fig.add_subplot(gs[:, 1])

    for col, label, color in [
        ("access_to_cause3", "outer gate", ACCENT),
        ("access_to_cause2", "middle gate", EXPOSURE),
        ("access_to_cause1", "deep gate", H2),
    ]:
        m = mean_ci(tr, ["session"], col)
        plot_band(ax1, m, "session", col, color, label=label, alpha=0.12, lw=1.5)
    deep = int(met.deep_revision_onset.mean())
    ax1.axvline(deep, color=DARK, ls="--", lw=0.8)
    ax1.text(deep + 0.8, 0.1, "deep revision", rotation=90, va="bottom", fontsize=6.8)
    ax1.set_ylabel("computed access")
    ax1.legend(frameon=False, ncol=3, loc="lower right")
    panel(ax1, "A")

    for col, label, color in [("cause3_trust", "outer trust", ACCENT), ("cause2_trust", "middle trust", EXPOSURE), ("cause1_revision", "deep revision", H2)]:
        m = mean_ci(tr, ["session"], col)
        plot_band(ax2, m, "session", col, color, label=label, alpha=0.12, lw=1.5)
    for x in [met.permission_slow_session.mean(), met.permission_fast_session.mean(), met.deep_revision_onset.mean()]:
        ax2.axvline(x, color="#888", ls="--", lw=0.65)
    ax2.set_ylabel("trust / revision")
    ax2.legend(frameon=False, ncol=3, loc="lower right")

    for _, row in one.iterrows():
        ax3.scatter(row.session, row.selected_cause_id, s=13, marker="s", color={3: ACCENT, 2: EXPOSURE, 1: H2}[row.selected_cause_id])
    ax3.set_yticks([1, 2, 3], ["deep", "middle", "outer"])
    ax3.set_xlabel("session")
    ax3.set_ylabel("contact")
    ax3.set_ylim(0.5, 3.5)

    vals = forced.groupby("seed").agg(initial=("initial_cause_count", "mean"), final=("final_cause_count", "mean"), spawned=("spawned_new_cause", "mean"), revised=("revised_inner", "mean"))
    ax4.plot([0, 1], [vals.initial.mean(), vals.final.mean()], color=ACCENT2, lw=2)
    ax4.scatter([0, 1], [vals.initial.mean(), vals.final.mean()], color=ACCENT2, s=34)
    ax4.set_xticks([0, 1], ["before", "forced\naccess"])
    ax4.set_ylabel("cause count")
    ax4.set_ylim(0, max(4, vals.final.mean() + 0.5))
    ax4.text(0.02, 0.92, f"flood-spawn {vals.spawned.mean():.0%}\ninner revised {vals.revised.mean():.0%}", transform=ax4.transAxes, fontsize=7.2, va="top")
    panel(ax4, "B")
    finish(fig, "F4_descent")


def figure_5():
    files = [SIM5 / "posterior_traces.csv", SIM5 / "ownership_session_rows.csv", SIM5 / "borrowed_then_owned_metrics.csv"]
    PROVENANCE["F5"] = [
        ("client capture-index trajectories by dyad condition", rel(files[0])),
        ("borrowed-then-owned session readout", rel(files[1])),
        ("low-baseline ownership summary", rel(files[2])),
    ]
    tr = pd.read_csv(files[0])
    own = pd.read_csv(files[1])
    bto = pd.read_csv(files[2])
    conds = ["regulated", "fluent-but-threatened", "dysregulated", "regulation-only"]

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    for cond in conds:
        f = mean_ci(tr[tr.condition.eq(cond)], ["trial"], "capture_index")
        color = COND_COLORS[cond]
        lw = 2.1 if cond in ["regulated", "fluent-but-threatened"] else 1.15
        alpha = 0.16 if cond in ["regulated", "fluent-but-threatened"] else 0.08
        plot_band(ax, f, "trial", "capture_index", color, cond.replace("-", " "), alpha=alpha, lw=lw)
    ax.set_xlabel("within-session trial")
    ax.set_ylabel("client capture index")
    ax.set_ylim(0.35, 0.86)
    ax.legend(frameon=False, loc="center right")
    panel(ax, "A")

    ins = ax.inset_axes([0.12, 0.12, 0.38, 0.42])
    sess = own.groupby("ownership_session").agg(revision=("late_self_revision", "mean"), et=("learned_prior_E_t", "mean")).reset_index()
    ins.plot(sess.ownership_session, sess.revision, color=ACCENT, lw=1.6)
    ins.fill_between(sess.ownership_session, 0, sess.revision, color=ACCENT, alpha=0.12)
    onset = int(round(bto.session_count_to_ownership.mean()))
    ins.axvline(onset, color=DARK, ls="--", lw=0.8)
    ins.text(onset + 0.4, sess.revision.max() * 0.45, "owned", fontsize=6.6, rotation=90, va="center")
    ins.set_xlabel("regulated sessions", fontsize=6.8)
    ins.set_ylabel("self-practice\nrevision", fontsize=6.8)
    ins.tick_params(labelsize=6.3)
    ins.spines["top"].set_visible(False)
    ins.spines["right"].set_visible(False)
    finish(fig, "F5_dyad")


def figure_6():
    files = [SIM7 / "formation_events.csv", SIM7 / "posterior_traces.csv", SIM7 / "first_passage_sessions.csv", SIM7 / "transfer_probe.csv", SIM7 / "per_seed_metrics.csv"]
    PROVENANCE["F6"] = [
        ("Act I formation events and structural-write layer traces", rel(files[0])),
        ("Act III capture descent, access/gate fractions, and contact choices", rel(files[1])),
        ("permission/contact first-passage markers", rel(files[2])),
        ("Act IV transfer gradient", rel(files[3])),
        ("adult capture baselines and resilient-world summary control", rel(files[4])),
    ]
    form = pd.read_csv(files[0])
    tr = pd.read_csv(files[1])
    fp = pd.read_csv(files[2])
    transfer = pd.read_csv(files[3])
    metrics = pd.read_csv(files[4])

    def map_session(s):
        return 220 + s

    acts = [(0, 180, "Act I"), (190, 210, "Act II"), (220, 285, "Act III"), (300, 318, "Act IV")]
    boundaries = [0, 180, 190, 210, 220, 285, 300, 318]
    layer_labels = {1: "early wound", 2: "flood", 3: "manager"}
    colors = {1: H2, 2: EXPOSURE, 3: ACCENT}

    fig = plt.figure(figsize=(7.2, 6.0))
    gs = GridSpec(4, 1, figure=fig, height_ratios=[1.12, 1.0, 1.18, 0.72], hspace=0.16)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax2 = fig.add_subplot(gs[2], sharex=ax0)
    ax3 = fig.add_subplot(gs[3], sharex=ax0)
    axes = [ax0, ax1, ax2, ax3]

    def act_guides(ax: plt.Axes, label: bool = False) -> None:
        for x0, x1, act in acts:
            ax.axvspan(x0, x1, color="#F4F3EF", zorder=-4)
            if label:
                ax.text((x0 + x1) / 2, 1.02, act, transform=ax.get_xaxis_transform(), ha="center", va="bottom", fontsize=8.0, color=DARK)
        for x in boundaries:
            ax.axvline(x, color="#D6D4CE", lw=0.55, zorder=-2)

    for i, ax in enumerate(axes):
        act_guides(ax, label=i == 0)
        ax.set_xlim(0, 318)

    form_mean = form.groupby("cause_id").agg(trial=("trial", "mean"), structural_write=("structural_write", "mean")).reset_index()
    fp_mean = fp.groupby("cause_id").agg(first_passage_session=("first_passage_session", "mean")).reset_index()
    max_write = float(form_mean.structural_write.max())
    for _, row in form_mean.iterrows():
        cid = int(row.cause_id)
        base = float(cid)
        formation_x = float(row.trial)
        melt_x = map_session(float(fp_mean.loc[fp_mean.cause_id.eq(cid), "first_passage_session"].iloc[0]))
        height = 0.16 + 0.26 * float(row.structural_write) / max_write
        xs = [formation_x, 180, 220, melt_x, 318]
        ys = [base, base + height, base + height, base + 0.05, base + 0.05]
        ax0.plot(xs, ys, color=colors[cid], lw=1.45, drawstyle="default")
        ax0.scatter([formation_x], [base], marker="^", s=42, color=colors[cid], edgecolor="white", linewidth=0.6, zorder=5)
        ax0.scatter([melt_x], [base + height], marker="v", s=46, color=colors[cid], edgecolor="white", linewidth=0.6, zorder=6)
        ax0.text(formation_x + 4, base - 0.14, layer_labels[cid], color=colors[cid], fontsize=6.8, va="top")
    ax0.text(
        224,
        0.82,
        "melt order inverts formation",
        fontsize=7.2,
        color=DARK,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=0.8),
    )
    ax0.set_yticks([1, 2, 3], ["deep", "middle", "outer"])
    ax0.set_ylim(0.65, 3.55)
    ax0.set_ylabel("strata +\nprecision")
    ax0.legend(
        handles=[
            Line2D([0], [0], marker="^", color="none", markerfacecolor=DARK, markeredgecolor="white", markersize=6, label="formation"),
            Line2D([0], [0], marker="v", color="none", markerfacecolor=DARK, markeredgecolor="white", markersize=6, label="first passage"),
            Line2D([0], [0], color=DARK, lw=1.3, label="structural precision"),
        ],
        frameon=False,
        loc="upper left",
        ncol=3,
    )
    panel(ax0, "A")

    full = tr[tr.condition.eq("full-life")].copy()
    h2 = tr[tr.condition.eq("h2-life")].copy()
    full_base = float(metrics[metrics.condition.eq("full-life")].adult_capture_index.mean())
    h2_base = float(metrics[metrics.condition.eq("h2-life")].adult_capture_index.mean())
    resilient_base = float(metrics[metrics.condition.eq("resilient-world")].adult_capture_index.mean())

    ax1.hlines(full_base, 0, 220, color=ACCENT, lw=1.8, label="full-life baseline")
    ax1.hlines(h2_base, 0, 220, color=H2, lw=1.2, ls="--", label="H2 baseline")
    ax1.hlines(resilient_base, 0, 318, color=MUTED, lw=1.1, ls=":", label="resilient-world")
    ax1.text(8, resilient_base + 0.025, "no formation events", color=GREY, fontsize=7.0)
    full_cap = mean_ci(full.assign(x=map_session(full.session)), ["x"], "capture_index")
    h2_cap = mean_ci(h2.assign(x=map_session(h2.session)), ["x"], "capture_index")
    plot_band(ax1, full_cap, "x", "capture_index", ACCENT, label="full-life sessions", alpha=0.12, lw=1.8)
    ax1.plot([220, float(full_cap.x.iloc[0])], [full_base, float(full_cap["mean"].iloc[0])], color=ACCENT, lw=1.2)
    plot_band(ax1, h2_cap, "x", "capture_index", H2, label="H2 sessions", alpha=0.05, lw=1.1, ls="--")
    ax1.set_ylabel("capture")
    ax1.set_ylim(0.34, 0.86)
    ax1.legend(frameon=False, loc="upper right", ncol=2)
    panel(ax1, "B")

    access_cols = [
        ("access_to_cause3", "outer access", ACCENT),
        ("access_to_cause2", "middle access", EXPOSURE),
        ("access_to_cause1", "deep access", H2),
    ]
    for col, label, color in access_cols:
        g = mean_ci(full.assign(x=map_session(full.session)), ["x"], col)
        plot_band(ax2, g, "x", col, color, label=label, alpha=0.10, lw=1.45)
    one = full[full.seed.eq(full.seed.min())].assign(x=map_session(full[full.seed.eq(full.seed.min())].session))
    for cid, color in colors.items():
        pts = one[one.selected_cause_id.eq(cid)]
        ax2.scatter(pts.x, np.full(len(pts), 0.025 + 0.045 * cid), marker="s", s=12, color=color, alpha=0.85, linewidth=0)
    marker_y = {3: 0.88, 2: 0.77, 1: 0.66}
    for cid, ytxt in marker_y.items():
        x = map_session(float(fp_mean.loc[fp_mean.cause_id.eq(cid), "first_passage_session"].iloc[0]))
        ax2.axvline(x, color=colors[cid], ls="--", lw=0.75)
        ax2.text(
            x + 1.0,
            ytxt,
            layer_labels[cid],
            color=colors[cid],
            fontsize=6.7,
            rotation=90,
            va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.78, pad=0.5),
        )
    ax2.set_ylabel("access /\ngate fraction")
    ax2.set_ylim(0, 1.05)
    handles, labels_for_legend = ax2.get_legend_handles_labels()
    handles.append(Line2D([0], [0], marker="s", color="none", markerfacecolor=GREY, markersize=5, label="contact choice"))
    ax2.legend(handles=handles, frameon=False, loc="upper left", ncol=4)
    panel(ax2, "C")

    for cond, color, label, ls, lw in [
        ("full-life", ACCENT, "full-life transfer", "-", 1.8),
        ("h2-life", H2, "H2 life", "--", 1.25),
    ]:
        d = transfer[(transfer.condition.eq(cond)) & (~transfer.structural_confound)].groupby("root_coupling").p_contact.mean().reset_index().sort_values("root_coupling")
        ax3.plot(300 + 18 * d.root_coupling, d.p_contact, color=color, lw=lw, ls=ls, label=label)
        ax3.scatter(300 + 18 * d.root_coupling, d.p_contact, color=color, s=18, zorder=4)
    ax3.set_ylabel("transfer\nP(contact)")
    ax3.set_ylim(-0.04, 1.05)
    ax3.legend(frameon=False, loc="upper left", ncol=2)
    ax3.set_xlabel("biography time")
    panel(ax3, "D")

    for ax in [ax0, ax1, ax2]:
        ax.tick_params(labelbottom=False)
    finish(fig, "F6_one_simulated_life")


def figure_7():
    files = [
        SIM6A / "posterior_traces.csv",
        SIM6A / "witnessing_policy.csv",
        SIM1 / "posterior_traces.csv",
        SIM2 / "posterior_traces.csv",
        SIM7 / "formation_events.csv",
        SIM7 / "posterior_traces.csv",
    ]
    PROVENANCE["F7"] = [
        ("band 1 effective precision within one encounter", rel(files[0])),
        ("band 2 mental-policy viability across evidence", rel(files[1])),
        ("band 3 freeze side of structural precision", rel(files[2])),
        ("band 3 melt side of structural precision", rel(files[3])),
        ("band 4 life structure spawn markers", rel(files[4])),
        ("band 4 life prune markers", rel(files[5])),
    ]
    bio = pd.read_csv(files[0])
    pol = pd.read_csv(files[1])
    sim1 = pd.read_csv(files[2])
    sim2 = pd.read_csv(files[3])
    form = pd.read_csv(files[4])
    life = pd.read_csv(files[5])

    fig, axes = plt.subplots(4, 1, figsize=(7.0, 4.5), gridspec_kw={"hspace": 0.18})
    labels = [
        "encounter clock",
        "evidence clock",
        "encounter-series clock",
        "life clock",
    ]

    b = bio[bio.seed.eq(bio.seed.min())].copy()
    b["p"] = norm(b["lambda_eff"])
    axes[0].plot(b.trial, b.p, color=ACCENT, lw=1.6)
    axes[0].fill_between(b.trial, 0, b.p, color=ACCENT, alpha=0.13)
    for phase, grp in b.groupby("phase"):
        axes[0].text(
            grp.trial.median(),
            0.94,
            phase.replace("_", "\n"),
            fontsize=6.2,
            ha="center",
            va="top",
            color=GREY,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.70, pad=0.4),
        )

    pol = pol.sort_values("safe_evidence")
    adv = -pol.delta_total_reflexive_minus_threat
    axes[1].plot(pol.safe_evidence, norm(adv), color=ACCENT, lw=1.6)
    flip = pol[pol.selected_policy.eq("allocate-to-reflexive")].safe_evidence.min()
    axes[1].axvline(flip, color=DARK, ls="--", lw=0.8)
    axes[1].text(flip + 0.6, 0.65, "policy flip", fontsize=7.0, color=DARK)

    s1 = sim1[sim1.seed.eq(sim1.seed.min())]
    s2 = sim2[(sim2.condition.eq("witnessing")) & (sim2.seed.eq(sim2.seed.min()))]
    axes[2].plot(s1.trial, norm(s1.structural_precision), color=EXPOSURE, lw=1.4, label="freeze")
    offset = s1.trial.max() + 20
    axes[2].plot(offset + s2.trial, norm(s2.structural_root_precision), color=ACCENT, lw=1.4, label="melt")
    cross_x = s1[s1.crossed.astype(bool)].trial.min()
    axes[2].axvline(cross_x, color=EXPOSURE, ls="--", lw=0.8)
    axes[2].text(cross_x + 8, 0.78, "count\ncrossing", color=EXPOSURE, fontsize=6.3, va="center")
    pr = s2[s2.pruned_now.astype(bool)]
    if not pr.empty:
        prune_x = offset + pr.trial.iloc[0]
        axes[2].axvline(prune_x, color=ACCENT, ls="--", lw=0.8)
        axes[2].text(prune_x + 6, 0.28, "BMR\nprune", color=ACCENT, fontsize=6.3, va="center")
    axes[2].legend(frameon=False, loc="upper center", ncol=2)

    axes[3].hlines(0.5, 0, 318, color="#C8C8C0", lw=1.1)
    for _, r in form.groupby(["trial", "cause_id"]).size().reset_index(name="n").iterrows():
        axes[3].scatter(r.trial, 0.62, marker="^", s=34, color={1: H2, 2: EXPOSURE, 3: ACCENT}[int(r.cause_id)])
    axes[3].text(11, 0.76, "formation", fontsize=6.4, color=DARK)
    prune = life[(life.condition.eq("full-life")) & (life.pruned_now.astype(bool))]
    if not prune.empty:
        prune_life_x = 220 + prune.session.mean()
        axes[3].scatter(prune_life_x, 0.38, marker="v", s=42, color=ACCENT)
        axes[3].text(prune_life_x + 5, 0.26, "prune", fontsize=6.4, color=ACCENT, va="center")
    axes[3].set_xlim(0, 318)

    for ax, lab in zip(axes, labels):
        ax.set_ylim(-0.05, 1.05)
        ax.set_ylabel("precision\nstate")
        ax.text(0.01, 0.83, lab, transform=ax.transAxes, fontsize=7.0, color=DARK)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[-1].set_xlabel("native clock units")
    panel(axes[0], "A")
    finish(fig, "F7_four_timescales")


def write_readme():
    caption = (
        "The same precision variable appears on four native clocks: momentary effective precision collapses and recovers within an encounter; "
        "mental-policy precision flips after accumulated safe evidence; structural precision freezes across repeated encounters and melts at BMR; "
        "life-scale structure records spawn and prune events. Shared colors mark witnessing/melt, exposure/freeze, and controls."
    )
    assert len(caption.split()) <= 150
    lines = [
        "# Paper-Grade Figure Build",
        "",
        "Generated by `python3 projects/emergence-suite/figures/build_figures.py` from existing preregistered artifacts. No simulation code or configs are modified.",
        "",
        "## Files",
        "",
    ]
    stems = [
        "F1_freezing_phase_diagram",
        "F2_hysteresis_loop",
        "F3_generalization_gradient",
        "F4_descent",
        "F5_dyad",
        "F6_one_simulated_life",
        "F7_four_timescales",
    ]
    for stem in stems:
        lines.append(f"- `{stem}.svg` / `{stem}.pdf`")
    lines += ["", "## Provenance", ""]
    lines += [
        "### Caption-ready titles",
        "- F1: formation requires overwhelm AND low control.",
        "",
    ]
    for fig, rows in PROVENANCE.items():
        lines.append(f"### {fig}")
        for panel_desc, path in rows:
            lines.append(f"- {panel_desc}: `{path}`")
        lines.append("")
    lines += [
        "## Provenance Notes",
        "",
        "- F1 renders `frozen_rate`, not `mean_later_revision_percent`. The registered frozen-cell classification is `frozen_rate >= 0.5`, which matches `summary.json` `metrics.frozen_cell_count == 17`; the prior failure was the wrong metric column for the intended visual claim, not an inverted colormap.",
        "- F6 uses Sim 7 registered CSVs only. Full-life and H2 capture session traces come from `posterior_traces.csv`; the resilient-world capture control has no per-session posterior trace there, so it is represented as the per-seed `adult_capture_index` mean from `per_seed_metrics.csv` and labeled as a flat control.",
        "- F6 layer-precision traces are event-derived from `formation_events.csv` structural-write values and `first_passage_sessions.csv` revision onsets; no new simulation run or harness regeneration was used.",
        "",
        "## Visual QA",
        "",
        "PDFs were rasterized to 1020 px width, approximately 3.4 inches at 300 dpi, and inspected for clipped/overlapping text, empty panels, legends for multiple series, condition-color consistency, and annotated event markers.",
        "",
        "| Figure | QA result | Notes |",
        "|---|---|---|",
        "| F1 | adjusted | Frozen rate is the heat field; frozen cells are outlined; attenuation is shaded; single-strike, slow path, crossing, attenuation, and boundary are in the legend. |",
        "| F2 | adjusted | Inset has opaque backing so the main trajectory does not bleed through; regime colors unchanged. |",
        "| F3 | unchanged | Three condition panels retain shared axes; confound marker and threshold inset remain legible. |",
        "| F4 | unchanged | Descent gates, trust/revision traces, contact raster, and forced-access summary remain legible. |",
        "| F5 | unchanged | Dyad condition colors are consistent with the shared palette; ownership inset remains legible. |",
        "| F6 | redesigned | Four shared-time rows: stratification plus precision/melt, capture plus controls, descent/access plus contact raster, and Act IV transfer. |",
        "| F7 | adjusted | Event annotations added for count crossing, BMR prune, life formation, and life prune. |",
        "",
        "## F7 Caption",
        "",
        caption,
        "",
    ]
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    setup()
    OUT.mkdir(parents=True, exist_ok=True)
    figure_1()
    figure_2()
    figure_3()
    figure_4()
    figure_5()
    figure_6()
    figure_7()
    write_readme()


if __name__ == "__main__":
    main()
