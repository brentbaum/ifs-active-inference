# Sim 4: Grown-for-real trust ledger

T4.1 Step A replaces the retired authored three-cause stack. The only permitted
run is the pilot: seeds 1001-1010, label `pilot`, output
`runs/sim4/pilot/`. No confirmatory seeds are accepted by the runner.

## Formation contract

One `Sim1.AgentState` lives through the neutral `(omega, kappa)` episode
schedule in `configs/sim4.yaml`. Every trial calls Sim 1's own
`sample_evidence` and `run_trial!`; therefore policy selection, prediction,
arousal, reflexivity, spawn pressure, `spawn_cause!`, and bank updates are Sim
1's actual formation machinery. The returned Sim 1 population is the stack.
Sim 4 does not add, remove, pad, or hand-initialize causes.

`formation_events.csv` contains one auditable `Sim1.init_agent` or
`Sim1.run_trial!/spawn_cause!` event per cause. `developmental_history.csv`
contains the trial path. Formation order is measured from Sim 1 cause IDs;
route is only `initial_cause` or the route logged by Sim 1 spawning.

## Frozen taxonomy readout

The classifier thresholds live in `configs/sim4-criteria.yaml` and were frozen
before the pilot. It reads only:

- count-weighted written reflexivity;
- structural precision;
- dominant Sim 1 policy;
- posterior catastrophic-severity belief.

It does not read route strings, spawned status, formation order, therapy
outcomes, or stack position. Labels can be missing or uneven; they do not enter
EFE.

## T4.1b access-rule audit and fix

The Step B audit found that the first T4.1 build selected blockers with a
greater-than comparison between cause IDs. That authored the outside-in
direction in the access rule. A4.perm was therefore non-diagnostic: forecast
order could not matter because formation IDs already fixed the gate.

The repaired access rule has no formation-order comparison. For each directed
pair `(blocker, target)`, Sim 4 measures the fraction of the blocker's Sim 1
cue/affect write mass accrued on trials when the target was the active
policy-owning cause. It multiplies that fraction by the blocker's learned Sim 1
non-approach policy mass (`flee + appease + attenuate`). A pair with no such
write history has exactly zero blocking strength, regardless of formation
position. Therapy trust can relax a nonzero learned gate, but cannot create a
gate for an uncoupled pair.

This makes either direction earnable from content. A4.shuffle-history
permutates the learned strengths among directed pairs while leaving causes,
forecasts, and all other banks intact. The revised preregistration requires the
baseline outside-in result to remain at least 8/10 evaluable seeds and the
shuffle to reduce that rate by at least 2/10. If it does not, the grown coupling
is not accepted as the ordering carrier.

### Repaired pilot result

The authored direction was not recovered. Baseline outside-in ordering passed
in 1/10 seeds (seed 1003), forecast permutation also passed in 1/10, and the
history shuffle passed in 0/10. The 1/10 degradation is only weak support under
the frozen A4.shuffle-history rule and does not establish the grown coupling as
a population-level ordering carrier. Five multi-cause seeds made no therapy
contact at all because their content-grown pair strengths formed mutual or
reversed gates; the model has no authored tie-breaker to escape those cycles.

Structural precision strongly mirrored formation order in the opposite
direction (mean Pearson `r = -0.981` across the eight multi-cause seeds). This
is disclosed as a proxy correlation, not an explanation of the observed
contact order: structural precision is absent from `access_fraction`,
`score_contact`, and every EFE term.

## Forecast and ordering controls

Each grown cause receives IID bounded symmetric relational pseudo-counts from a
seeded RNG independent of formation order. Causes never inherit blockers'
forecasts. The permutation arm shuffles those exact forecasts among grown
causes before therapy.

EFE contains access-conditioned expected outcome, accessible information gain,
and a settled-contact cost. Access is computed only from the grown directed-pair
strengths and the blockers' current permission state. There is no direct depth,
position, taxonomy, structural-precision, or desired-order term. The criterion
requires complete newest-to-oldest first contact in at least 8/10 seeds in both
baseline and forecast-permutation arms. Structural precision versus formation
order is reported as an audit correlation, but structural precision is not an
access or EFE input.

## Rupture and write-path audit

Repair and breach observations write the same configured evidence mass through
the same relational-weight pathway. Breaches are sampled from a seed-specific
therapy stream. Their effect is compared with the immediately preceding repair
to the same cause; any asymmetry is therefore posterior history, not an 80:8
event-size ratio. The pilot evaluates the preregistered write-size sweep and
logs it to `write_size_sweep.csv`.

Policy and mandate rates count actual nonzero before/after bank deltas. Ordinary
repair/breach observations route to policy and relational banks; only a
catastrophic observation has a mandate-bank pathway. Zero observed mandate
writes, if obtained, is a measurement of the realized stream rather than a
`mandate_learning_rate = 0` assumption.

## Outputs

- `summary.json`, `status.json`, `criteria-results.json`, `metadata.json`
- `formation_events.csv`, `developmental_history.csv`,
  `taxonomy_readouts.csv`
- `per_seed_metrics.csv`, `contact_arm_metrics.csv`, `posterior_traces.csv`,
  `write_size_sweep.csv`
- `blocking_strengths.csv`: grown and history-shuffled directed-pair strengths
- `figures/descent.svg`

The scripted original S4.1-S4.5/A4.1-A4.2 criteria remain explicitly falsified
as historical records in `configs/sim4-criteria.yaml`.

## T4.1b Step B verdict (orchestrator, 2026-07-10): descent claim FALSIFIED in this model class — the finding is architectural

With the authored `id >` access rule removed and blocking derived from grown
pairwise history coupling (protective policy mass x write-history fraction),
outside-in descent fell from the authored 8/10 to 1/10; the single clean pass
(seed 1003) was destroyed by the history shuffle; forecast permutation changed
nothing anywhere (0.465 mean later-to-earlier share — direction is a coin
flip). Rupture asymmetry degraded to 4/10 (grown ratio 1.34). The previous
T4.1 "support" was carried entirely by the authored rule.

Why the coupling cannot form here: Sim 1 has ONE active cause per trial. When
a protector spawns, it becomes the active cause — so it never accumulates
writes "while the earlier wound is active." The theory's mechanism for descent
(protectors learn on the exile's live distress and therefore gate it) requires
concurrent multi-cause activation, which this model class does not implement.
S4.descent is recorded as unearned here, with the missing carrier identified.
A third cycle, if attempted, must preregister a DISTINCT theory-motivated
coupling (e.g. content overlap: the protector's cue banks written on contexts
associated with the wound's activating contexts) — not a rescaled version of
this one. Two cycles of falsification stand in the record either way.

## T4.1c Step A identifying-pilot result (2026-07-10)

T4.1c changed only the post-selection contact rule on the same pilot seeds and
deterministic formation/forecast/coupling streams. Arm G retained T4.1b's
exact-access gate. Arm W always contacted the EFE-selected cause and scaled
every write by continuous access, with no threshold. Arm P contacted with
probability equal to access and made a full-size write on contact; its contact
draw used the preregistered independent `seed + 3_000_037` stream.

Arm G exactly reproduced T4.1b: outside-in ordering was 1/10, and 5/8
multi-cause seeds made zero contacts. W and P both eliminated the deadlock:
10/10 seeds contacted in each arm, with zero zero-contact multi-cause seeds.
But complete outside-in ordering remained 1/10 in W and 1/10 in P, with seed
1003 the sole pass in every arm.

Under the frozen interpretation rule, this confirms the T4.1b conclusion that
the grown coupling has no reliable outside-in directional bias. The
exact-access rule authored the deadlock but did not author the negative
directional result. Missing concurrent activation remains the leading
candidate among the stated explanations, not a uniquely identified diagnosis.
No arm reached the 8/10 ordering trigger for A4.shuffle-history; the controls
were still run for all arms and yielded G=0/10, W=2/10, and P=2/10 after
shuffle.

## T4.1c identifying experiment (orchestrator ticket, 2026-07-10): the gate caused the deadlock, NOT the negative descent

Three preregistered contact rules on the same grown stacks, couplings, and
seeds: G (T4.1b's exact-access gate), W (always-contact, access-weighted
writes), P (contact with probability = access). G reproduced T4.1b exactly.
W and P unlocked contact in 10/10 seeds (960/942 contacts vs G's 322) — and
outside-in ordering stayed at exactly 1/10 in ALL THREE ARMS. Under the
preregistered interpretation rule, the re-review's alternative explanation
("useful coupling trapped by the gate") is eliminated: this grown coupling has
no outside-in directional bias, gated or not. Missing concurrent activation
remains a CANDIDATE explanation for why no directional coupling forms — not
uniquely established. Sim 4's descent claim is closed for this model class:
three cycles, each preregistered, converging on unearned.
