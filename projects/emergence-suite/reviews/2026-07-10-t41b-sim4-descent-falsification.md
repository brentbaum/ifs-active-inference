# T4.1b Step A report — Sim 4 repaired access rule

## Status

- Implementation: **complete**.
- Pilot: **complete**, seeds **1001–1010 only**, label **pilot**.
- Confirmatory seeds: **not run**.
- Git commit: **none**.
- Output: `projects/emergence-suite/suite/runs/sim4/pilot/`.
- Implementation status: `implementation_passed=true`.
- Overall theory result: **falsified**.
- Final suite tests: **39/39 passed**.
- Scope: only `src/sims/sim4/`, `configs/sim4*.yaml`, generated Sim 4 pilot outputs, and this requested report were changed/written.

## Fix implemented

The audited directional gate was removed. There are no greater-than or
less-than cause-ID comparisons in `Sim4.jl`'s access/EFE path (grep clean).
Pair identity is found by equality lookup rather than formation-position
indexing.

Before every Sim 1 developmental trial, Sim 4 now logs the active
policy-owning cause. After `Sim1.run_trial!`, it separately logs the cause
whose banks received the write. For each directed pair `(blocker j, target i)`:

```
protective_mass_j =
    P_j(flee) + P_j(appease) + P_j(attenuate)

history_fraction_ji =
    cue+affect write mass to j while i was active
    ------------------------------------------------
    all cue+affect write mass to j

blocking_strength_ji = protective_mass_j * history_fraction_ji
```

Cue write mass is exactly Sim 1's
`cue_learning_weight * learning_rate`; affect write mass is exactly
`learning_rate`. A pair with no coupled writes is exactly zero. No taxonomy,
structural precision, forecast, formation-order comparison, or fitted cutoff
enters this calculation.

Access is the minimum pair availability:

`1 - blocking_strength * (1 - current_permission)`,

where current permission is one for an allow-access policy and otherwise the
blocker's trust share relative to the unchanged permission threshold. Thus
therapy may relax a learned gate but cannot create a gate for an uncoupled
pair.

A4.shuffle-history permutes the multiset of blocking strengths across all
off-diagonal directed pairs within each seed. The multiset-preservation audit
passed in 10/10 seeds. A4.perm remains as the separate forecast control.
`Sim4.grow_stack(seed, params)` retains its two-return-value signature for
Sim 7.

## Preregistration

The revised `S4.descent` wording, A4.shuffle-history criterion, shuffle
domain, RNG offset, and degradation threshold were written before the repaired
pilot ran. The first pilot invocation then stopped without producing results
on an empty filtered sum for an uncoupled pair. That edge case was fixed to
return the theoretically required zero; no criterion or constant changed
before rerunning the same pilot seeds.

## Per-criterion results

| Criterion | Pilot value | Target | Result |
|---|---:|---:|---|
| S4.descent | baseline outside-in 1/10 | >= 8/10 | **Falsified** |
| A4.perm | forecast-permuted outside-in 1/10 | >= 8/10 | **Falsified**; pass/fail agreed with baseline in 10/10 |
| A4.shuffle-history | shuffled outside-in 0/10; degradation 1/10 | degradation >= 2/10 | **Weak support only**; grown coupling is not accepted as the population ordering carrier |
| A4.grown | 20/20 causes with complete Sim 1 provenance; 0 authored | 100%, 0 authored | **Support** |
| S4.rupture | asymmetry 4/10; breach-after-repair observed 5/10 | >= 8/10 | **Null** |
| Frozen readout classifier | unchanged | unchanged | Preserved |
| Labels in EFE | none | none | Preserved |

The retained equal-write sweep produced S4.descent = 1/10 at every candidate
write size. At the retained 0.25 size, repair and breach each write 0.25,
rupture asymmetry was 4/10, and the mean grown breach/repair ratio was 1.3380.

## Per-seed results

First-contact sessions are listed in newest-to-oldest formation order. Zero
means that cause was never contacted. “Later share” is the fraction of all
non-self grown blocking mass directed from later-formed to earlier-formed
causes.

| Seed | Causes / evaluable | Baseline sessions / pass | Forecast-perm sessions / pass | History-shuffle sessions / pass | Later share | Structural precision vs order r | Rupture ratio / asymmetric | Contacts |
|---:|---|---|---|---|---:|---:|---|---:|
| 1001 | 2 / yes | 0-0 / no | 0-0 / no | 0-0 / no | 0.471 | -1.000 | 0.000 / no | 0 |
| 1002 | 1 / no | 1 / no | 1 / no | 1 / no | 0.000 | n/e | 5.365 / yes | 96 |
| 1003 | 2 / yes | 1-17 / **yes** | 1-21 / **yes** | 21-1 / no | 1.000 | -1.000 | 2.694 / yes | 96 |
| 1004 | 2 / yes | 0-0 / no | 0-0 / no | 0-0 / no | 0.056 | -1.000 | 0.000 / no | 0 |
| 1005 | 3 / yes | 0-1-0 / no | 0-1-0 / no | 0-0-0 / no | 0.793 | -0.949 | 0.798 / no | 13 |
| 1006 | 1 / no | 1 / no | 1 / no | 1 / no | 0.000 | n/e | 2.721 / yes | 96 |
| 1007 | 2 / yes | 0-0 / no | 0-0 / no | 0-0 / no | 0.466 | -1.000 | 0.000 / no | 0 |
| 1008 | 2 / yes | 0-0 / no | 0-0 / no | 0-0 / no | 0.073 | -1.000 | 0.000 / no | 0 |
| 1009 | 3 / yes | 0-1-0 / no | 0-1-0 / no | 0-1-0 / no | 0.796 | -0.896 | 1.802 / yes | 21 |
| 1010 | 2 / yes | 0-0 / no | 0-0 / no | 0-0 / no | 0.068 | -1.000 | 0.000 / no | 0 |

Only seed 1003 grew a clean one-way later-to-earlier gate and completed
outside-in first contact. Shuffling its two directed strengths reversed first
contact and destroyed that pass. This is seed-level evidence that grown content
can carry direction, but 1/10 degradation misses the preregistered population
criterion.

## What carries the ordering now

The only directional input to access is the learned pairwise history coupling.
It does **not** reliably point outside-in:

- Mean later-to-earlier share was 0.465 across the eight multi-cause seeds.
- Several seeds gave the initial cause substantial learned coupling back onto
  newer causes, producing reversed or mutual gates.
- Five of eight multi-cause seeds made zero therapy contacts because EFE kept
  selecting a cause whose content-grown gate never reached full permission.
- Forecast permutation changed no seed's pass/fail result, so forecasts did not
  carry the ordering.
- History shuffle destroyed the sole baseline pass, but the 1/10 aggregate
  degradation was below the frozen 2/10 threshold. The grown coupling therefore
  is not established as a robust population-level ordering carrier.

Structural precision strongly mirrors formation order: mean Pearson
`r=-0.9806` across the eight multi-cause seeds. This correlation is disclosed
because it could look like a proxy for direction. It cannot carry the present
result: structural precision is absent from `access_fraction`,
`score_contact`, and all EFE terms. It remains only a frozen classifier/audit
readout.

## New constants and fixed choices

| Constant/choice | Value | Provenance |
|---|---:|---|
| Protective policy mass | `flee + appease + attenuate` posterior mass | Semantic complement of Sim 1 approach/allow; frozen before pilot |
| Cue write contribution | `cue_learning_weight * learning_rate` | Exact Sim 1 bank update |
| Affect write contribution | `learning_rate` | Exact Sim 1 bank update |
| Pair history normalization | coupled cue+affect write / all blocker cue+affect write | Dimensionless grown fraction |
| Uncoupled pair strength | `0.0` | Required by mechanism; no cutoff |
| Shuffle domain | all off-diagonal directed pairs within seed | Preserves strengths, makes either direction reachable |
| Shuffle RNG offset | `9_000_031` | Frozen before repaired pilot |
| A4.shuffle-history target | baseline minus shuffled rate >= `0.20` | Material degradation of 2/10 seeds |
| A4.shuffle-history weak target | `0.10` | Frozen before repaired pilot |
| Contact write size | `0.25` repair and breach | Retained passed-audit equal-write setting |

## Blockers and findings

Scientific blockers:

1. **S4.descent does not emerge after removing the authored direction.** The
   repaired result is 1/10, not 8/10.
2. **The grown coupling often creates cycles or the opposite direction.** Five
   multi-cause seeds never contact any cause during therapy.
3. **A4.shuffle-history does not meet its material-degradation threshold.**
   Although it removes the only pass, aggregate degradation is only 1/10.
4. **Two seeds grow only one cause**, so descent is not evaluable there; they
   remain failures in the unchanged 10-seed headline.
5. **S4.rupture no longer reaches its target** because the repaired access
   dynamics sharply reduce contact/breach opportunities.
6. **Structural precision has a near-perfect order correlation**, but using it
   would re-smuggle direction through a proxy; it is disclosed and remains
   excluded.

Implementation blockers: none outstanding. The initial empty-sum pilot abort
was fixed as the zero-coupling edge case, outputs are complete, grep/diff checks
are clean, and the final full suite test pass succeeded.

## Key artifacts

- `runs/sim4/pilot/summary.json`
- `runs/sim4/pilot/criteria-results.json`
- `runs/sim4/pilot/per_seed_metrics.csv`
- `runs/sim4/pilot/blocking_strengths.csv`
- `runs/sim4/pilot/developmental_history.csv`
- `runs/sim4/pilot/write_size_sweep.csv`
- `src/sims/sim4/README.md`
- `src/sims/sim4/magic-numbers.md`

STOP: no confirmatory seeds and no commit.
