# Experiment 50-H Stage A report

Status: **Stage A complete; confirmatory execution stopped.** The freeze candidate awaits evaluator verification and commit. No seed at or above `700000` was selected, generated, or run.

## Build decisions

- One reachable entrypoint, `src/ModelOrganism.jl`, owns all strain equations. The old Experiment 44–49 modules remain untouched and unreachable from Experiment 50 runners.
- Experiment 49's copied Sim-5 mapping → categorical depth → effective precision path was reimplemented once as `update_dyad!`; all assays use the canonical function.
- The gate is `protector_permission ≥ permission_threshold`; there is no gate object or completion rule.
- Mature trust, root, repertoire cost, and reliability beliefs are produced only by seeded developmental replay. Pilot growth logs ship per assay.
- Assay configurations are categorical topology/intervention records. All numeric authored choices, including analysis thresholds, are in `genome.toml` with rationales.

## Phase 0 joint calibration

The grammar and all ten analysis plans were hash-locked before Phase 0. The joint pass consulted one apparatus-first dynamic-range quantity per assay and no criterion statistic. All genome values were retained; no operationalization moved. The ledger preserves any inadequate range as an honest limitation rather than tuning it away.

## Assay 0 audits

- Identity and genome hash guard: passed in every invoked runner.
- Duplicate equation / unreachable legacy adapter check: passed.
- Bit-for-bit zero-slot idleness, provenance, grammar expressibility, machinery classification, parameter-use, and compression outputs are in the audit package.
- Machinery audit conclusion: canonical state-change transitions are organization-only; world generators are classified neither; no carrier parameter exists.

## Pilot descriptives

Each assay ran 12 descriptive pilot worlds below `700000` (analytic assays additionally enumerated their frozen property domains). `per_seed.csv`, `summary.json`, `developmental-history.csv`, and `report.md` are present for every assay. These are descriptives, not confirmatory verdicts:

| Assay | Pilot rows | Descriptive means across recorded rows |
|---:|---:|---|
| 1 | 300 | `property_holds=1.0`; `precision=2.4480000000000004` |
| 2 | 36 | `closed_revision=0.31792080820593455`; `revision_effect=0.1329763270433738` |
| 3 | 48 | `correct_2d=1.0`; `loss_1d=0.25027055728831804` |
| 4 | 36 | `root_revised=0.05555555555555555`; `untreated_transfer=0.07814746689551065` |
| 5 | 48 | `root_change=0.19719300809925658`; `uptake=0.9363297998712515` |
| 6 | 60 | `diagonal=1.0`; `heldout_margin=1.2059402411357802` |
| 7 | 1236 | `sign_matches=1.0`; `doover_success=0.515625` |
| 8 | 24 | `selection_tracks=0.75`; `relational_change=0.16720179405475763` |
| 9 | 48 | `recovered=0.8541666666666666`; `sign_prediction_match=0.6458333333333334` |
| 10 | 84 | `descent=0.21428571428571427`; `root_change=0.08001369859309165` |

## Conservative ambiguity resolutions

- Spec §3.2 describes pilots after strain freeze while the Stage A brief permits instrument repair before the freeze package is finalized. I treated the Stage A pilots as pre-commit descriptive shake-downs under §3.4; the manifest is assembled only after re-pilot. Two apparatus repairs were logged: paired partner-stream replay in assay 10 and complete genome inventory of already-effective literals. Every assay was re-piloted on the final source and genome.
- “Every authored constant” was read broadly: protocol counts and analysis margins are inventoried alongside agent constants, while assay files contain no numeric agent overrides.
- The legacy source may still contain equations because Experiments 44–49 must remain unchanged. “Anywhere assay-reachable” was enforced as the transitive Experiment 50 include graph; the duplicate audit also forbids legacy includes in all Experiment 50 runners.
- A zero-count slot remains represented in configuration and is tested for exact idleness; it is not compiled out.
- The sealed hashes were copied verbatim as withheld manifest entries. Their plaintext was neither sought nor inferred.

## Freeze and stopping point

`freeze-manifest.json` independently hashes the organism, genome, grammar, configurations, frozen world populations, generators, protocols/runners, analysis code/plans, RNG definitions, environment, audit and pilot records, and the four evaluator-provided sealed hashes. The commit field is explicitly evaluator-pending. This implementation stops before every confirmatory block and before 50-P/50-L execution.
