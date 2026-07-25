# Stage B apparatus errata

## Erratum B-001 — confirmatory execution layer absent

- Discovered: before opening any released confirmatory seed.
- Affected scope: all ten assays.
- Apparatus-first statement: the frozen Stage A runner exposes `--prepare`, `--phase0`, `--pilot`, `--audit`, `--report`, `--freeze`, and `--stage-a`; it explicitly has no confirmatory mode. The canonical module exposes simulation rows and descriptive pilot summaries, but no implementation that applies the frozen analysis plans to a released confirmatory block.
- Evidence: `scripts/model_organism/run_stage_a.jl` states “No confirmatory mode exists”; `src/model_organism/RecordIO.jl` contains `run_pilot` but no confirmatory runner or criterion evaluator.
- Classification: pure software/instrument omission. The ten analysis plans already freeze the estimands, populations, aggregation, missing-event handling, margins, thresholds, and provenance labels. No organism equation, genome value, grammar term, configuration, generator, protocol, plan, or frozen manifest entry is changed.
- Repair: add `scripts/model_organism/run_stage_b.jl` as a separate execution/reporting layer. It must verify commit `274f888`, call the frozen `run_assay` functions unchanged, use exactly the first frozen-plan world count from each released block, write separate `confirm-*` outputs, and evaluate only rules stated in the locked plans.
- Asymmetry: the repair introduces no rescue route. Missing frozen cells or outputs count as failures. In particular, assay 8's frozen simulator has no distinct registration-ablation row; Stage B will not manufacture one, and the affected criterion will fail for missing required evidence.
- Confirmatory status: preserved under spec §3.2 as a software-only execution repair. No confirmatory seed was read before this entry was written.

### Interval conventions required by the frozen plans

The plans require 95% intervals but do not name every computational convention. The repair uses deterministic, conventional mappings without changing any decision rule:

- Rates: Wilson 95% intervals.
- Mean paired effects: normal-approximation 95% confidence intervals.
- Where a plan explicitly says “percentile interval”: empirical 2.5th–97.5th percentiles of the frozen per-world effects.
- Exact analytic properties: Wilson interval for the enumerated property-domain success proportion; the decision remains exact agreement where specified.

Intervals describe uncertainty and never replace or move a frozen threshold.

## Erratum B-002 — combined safeguard interval omitted from rendered row

- Discovered: after assay 10 completed, during output verification.
- Affected scope: assay 10 reporting only; simulation rows, cell rates, cell-specific Wilson intervals, effect estimate, and verdict were already correct in `confirm-summary.json`.
- Apparatus-first statement: the combined `decoupled/adverse safeguards` report row rendered its interval as not estimable even though both constituent rates had frozen-world Wilson intervals.
- Classification: pure reporting software error. No seed is reopened and no estimate, threshold, or verdict changes.
- Repair: report the conservative combined interval from zero to the larger constituent Wilson upper bound. For two observed rates of `0/80`, this is `[0.0, 0.0458197362645751]`.

## Erratum B-003 — post-completion audit found frozen-design omissions

- Discovered: independent post-completion critique, after released blocks had run but before Stage B was claimed complete.
- Affected scope: assays 8 and 9.
- Assay 8 apparatus-first statement: the frozen configuration and plan require a distinct registration-ablation arm, but the frozen simulator emits registration off/on only. The Stage B executor initially recorded the missing criterion as a failed result. That was incorrect: the planned treatment was never observed, so the assay is incomplete rather than a negative confirmatory verdict.
- Assay 9 apparatus-first statement: the frozen plan requires a 101-point analytic domain across stakes and transfer locality. The frozen simulator emits one repeated invariant row per stochastic seed and assigns `transfer_local = true`; it does not enumerate or property-test locality. The invariant verdict is therefore unsupported and the assay is incomplete.
- Classification: frozen apparatus/design omissions, not ordinary outcome failures. Implementing either missing mechanism after seeing confirmatory outputs could weaken the strain's ability to fail and therefore requires evaluator adjudication under the asymmetry rule.
- Action: no seed was rerun and no frozen component was changed. Valid assay 8 selection/registration-on-off estimates and assay 9 learned-history/crossover estimates are retained. Overall assay status is corrected to `incomplete_apparatus_stop`; missing criteria are `not evaluable`, not pass/fail.
- Additional audit finding: assay 9 joint recovery was `80/80` trustworthy, `9/80` neutral, and `79/80` adverse. The pooled/macro rate of `0.70` meets its frozen boundary but masks the neutral-family failure; the strata are now reported explicitly.

Stage B cannot be called complete until the evaluator decides whether these omissions qualify for software-only repair/rerun or require a 50b revision.

## Erratum B-004 — generic missing/non-finite handler overclaimed

- Discovered: independent post-completion critique.
- Apparatus-first statement: several Stage B analyzers require exactly one row per planned cell and would throw on a missing cell rather than automatically convert it to a worst-case outcome. The initial report boilerplate therefore overclaimed that every possible missing event was handled by the runner.
- Observed-block check: all emitted numeric rows for assays 1–7 and 10 were finite and their required cells were present. Assays 8 and 9 have the design omissions described in B-003. No observed estimate changes.
- Action: the blanket claim was removed from every report. Any evaluator-authorized rerun should add an explicit plan-keyed required-cell and finite-value validator before opening a seed.

## Evaluator adjudication and authorized repair

The evaluator subsequently adjudicated both B-003 omissions as pure software errors under spec §3.2 and authorized confirmatory-preserving repair:

- Assay 8 apparatus-first: **the frozen plan requires paired registration on/off/ablation arms; the runner produces on/off only.** Repair adds the missing ablation execution through the frozen `update_registration!` no-registration path, reruns the same released worlds, and requires the pre-existing on/off CSV to reproduce byte-for-byte before the repaired three-arm output is accepted.
- Assay 9 apparatus-first: **the frozen plan requires a 101-point stakes/locality property domain; the runner produces repeated stochastic invariant rows and does not enumerate that domain.** Repair adds the deterministic 101-point property executor using neutral initialization plus canonical posterior updates with logged provenance. It does not rerun or reinterpret the already-complete learned-history world block.

The assay 9 risk-model obsolescence crossover (`0.5167` against `0.80`) remains a scientific **FAIL**, its first prospective test. Neutral recovery (`9/80`) is retained.

Files authorized to change or be added by this repair:

- `scripts/model_organism/run_stage_b.jl` (additive apparatus only)
- `results/model_organism/stage-b-errata.md`
- `results/model_organism/assays/8/confirm-per_seed.csv`
- `results/model_organism/assays/8/confirm-pre-repair-per_seed.csv`
- `results/model_organism/assays/8/confirm-summary.json`
- `results/model_organism/assays/8/report.md`
- `results/model_organism/assays/9/confirm-property-domain.csv`
- `results/model_organism/assays/9/confirm-property-summary.json`
- `results/model_organism/assays/9/confirm-summary.json`
- `results/model_organism/assays/9/report.md`
- `results/model_organism/profile.md`
- `results/model_organism/stage-b-manifest.json`

No organism source, genome, grammar, configuration, generator, frozen analysis plan, or assay 9 world-block output is authorized to change.

### Repair execution record

- Frozen organism core SHA-256 remained `b5813d625a338d7231af9b7ad45bba316ca893e5699576ea16b294ec125dde41`; genome SHA-256 remained `efd5d83d4053858ddb07e5229ae2eb8e27bdd10d026115b37485bbc71f56074a`.
- Assay 8 pre-repair on/off CSV SHA-256: `61953fe9c3cf987145da016a5a8f90ba8f6c93121f05abc54b07026b471c4690`.
- Assay 8 regenerated on/off CSV SHA-256 before adding ablation: the same `61953fe...`; byte-for-byte equality `true`, maximum absolute deviation `0.0`.
- Assay 8 repaired three-arm CSV SHA-256: `e6ebf301b37c8f5a1fb0f1300ecb7dd0638c2e607caefe8f99a00f6a9dbc66fb`. Off and ablation were static in `80/80`; the assay verdict is **PASS**.
- Assay 9 learned-history world CSV remained `d7f478ac45f33c90fbb178fc5adf74db12af66a778732e1011cf34c9f6d336c7` before and after repair; it was not rerun.
- Assay 9 property-domain CSV SHA-256: `6a54188dc016cf1a159fc2bf489761e53f3f97d03e9d32e0471db6842f8ae896`. All `101/101` stakes/locality points passed.
- Assay 9 overall verdict remains **FAIL** solely because the risk-model obsolescence crossover remained `0.5167 < 0.80`.
