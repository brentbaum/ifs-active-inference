# T4.1c Step A report — graded contact vs exact-access gate

Date: 2026-07-10  
Stage: pilot only  
Seeds: 1001–1010 only  
Output: `projects/emergence-suite/suite/runs/sim4/pilot/`  
Confirmatory seeds: not run  
Git commit: none

## Outcome

The experiment identifies the exact-access gate as the cause of the zero-contact deadlock, but not as the cause of the negative descent result. Arms W and P unlocked contact in 10/10 seeds each, while complete outside-in first-contact ordering stayed at 1/10 in both arms, exactly matching Arm G's 1/10. Under the preregistered interpretation rule, T4.1b's conclusion that this grown coupling has no reliable outside-in directional bias is confirmed. Missing concurrent activation remains a candidate explanation for why directional coupling is absent; it is not uniquely established by this experiment.

## Implementation and protocol audit

- Arm G: contact iff `access >= 1.0 - 1e-9`; full-size writes. This is the unchanged T4.1b gate.
- Arm W: contact always occurs on the EFE-selected cause; relational, policy/trust, mandate (if applicable), and root-revision writes are multiplied by raw continuous access. There is no W threshold or floor.
- Arm P: contact is a Bernoulli draw with probability equal to access; writes are full-size on contact.
- Arm P uses the preregistered independent `seed + 3_000_037` RNG stream. Formation, policy/choice, outcome, forecast, forecast-permutation, and history-shuffle streams retain their prior offsets.
- The three arms use the same deterministic Sim 1-grown stacks, grown pair strengths, randomized initial forecasts, EFE scoring/selection procedure, parameters, and seeds. Only post-selection contact occurrence/write scaling differs.
- No directional ID comparison was introduced. `Sim4.grow_stack(seed::Int, params::Sim4Params)` retains its signature for Sim 7.
- The runner rejects any label other than `pilot` and any seed list other than 1001–1010.
- Final package test suite passed: 39/39 tests.
- `status.json`: `implementation_passed=true`, `stage="pilot"`, `confirmatory_run=false`.

## Preregistered criteria

| Criterion | G | W | P | Result |
|---|---:|---:|---:|---|
| A4c.baseline | ordering 1/10; zero-contact 5/8 multi-cause | — | — | **Support.** G exactly reproduced both T4.1b values. |
| S4c.unlock | contacts in 5/10 seeds | contacts in 10/10 | contacts in 10/10 | **Support.** Minimum graded-arm contact rate = 1.0, above 0.7. |
| S4c.descent | ordering 1/10 | ordering 1/10 | ordering 1/10 | Positive descent criterion **falsified** (maximum graded rate 0.1 vs 0.8). Because both graded arms unlocked and remained <=3/10, the preregistered no-direction interpretation is confirmed. |
| A4.shuffle-history trigger | baseline 1/10; shuffled 0/10 | baseline 1/10; shuffled 2/10 | baseline 1/10; shuffled 2/10 | No arm reached the preregistered 8/10 trigger. Controls were run for all arms as an audit; the shuffle did not reveal a hidden population-level directional carrier. |
| A4.grown (shared) | 20/20 causes provenance-complete; 0 authored | same stacks | same stacks | **Support.** |

Legacy T4.1b records remain in the criteria file and continue to read Arm G: S4.descent 0.1 (falsified), A4.perm 0.1 (falsified), A4.shuffle-history degradation 0.1 (weak support), A4.grown 1.0 (support), and S4.rupture 0.4 (null).

## Per-arm totals

| Arm | Seeds with contact | Zero-contact multi-cause seeds | Total contacts | Outside-in passes | History-shuffled passes |
|---|---:|---:|---:|---:|---:|
| G — gate | 5/10 | 5/8 | 322 | 1/10 (1003) | 0/10 |
| W — weighted | 10/10 | 0/8 | 960 | 1/10 (1003) | 2/10 (1005, 1010) |
| P — probabilistic | 10/10 | 0/8 | 942 | 1/10 (1003) | 2/10 (1005, 1010) |

## Per-seed first contacts and counts

`seq` is cause ID order of first contact. `sessions` is the first-contact-session vector aligned to the listed newest-to-oldest formation order; zero means never contacted. One-cause seeds 1002 and 1006 are preregistered ordering failures, not trivial passes.

| Seed | Newest→oldest | G seq; sessions; count | W seq; sessions; count | P seq; sessions; count | Outside-in G/W/P |
|---:|---|---|---|---|---|
| 1001 | 2-1 | —; 0-0; 0 | 1-2; 2-1; 96 | 1-2; 2-1; 85 | no / no / no |
| 1002 | 1 | 1; 1; 96 | 1; 1; 96 | 1; 1; 96 | no / no / no |
| 1003 | 2-1 | 2-1; 1-17; 96 | 2-1; 1-17; 96 | 2-1; 1-17; 96 | **yes / yes / yes** |
| 1004 | 2-1 | —; 0-0; 0 | 1-2; 27-1; 96 | 1-2; 26-1; 96 | no / no / no |
| 1005 | 3-2-1 | 2; 0-1-0; 13 | 2-3-1; 14-1-18; 96 | 2-3-1; 14-1-18; 96 | no / no / no |
| 1006 | 1 | 1; 1; 96 | 1; 1; 96 | 1; 1; 96 | no / no / no |
| 1007 | 2-1 | —; 0-0; 0 | 1-2; 5-1; 96 | 1-2; 6-3; 91 | no / no / no |
| 1008 | 2-1 | —; 0-0; 0 | 1-2; 18-1; 96 | 1-2; 18-1; 96 | no / no / no |
| 1009 | 3-2-1 | 2; 0-1-0; 21 | 2-3-1; 22-1-33; 96 | 2-3-1; 22-1-28; 94 | no / no / no |
| 1010 | 2-1 | —; 0-0; 0 | 1-2; 27-1; 96 | 1-2; 27-1; 96 | no / no / no |

## Identification among the three explanations

1. **Grown coupling with no reliable direction — supported.** Once the gate is removed or randomized proportionally to access, contacts become ubiquitous but ordering does not improve: G/W/P are all 1/10, and seed 1003 is the sole pass in every unshuffled arm.
2. **Useful outside-in coupling trapped by the all-or-nothing gate — not supported for the preregistered descent estimand.** The gate did trap contact in five multi-cause seeds, but unlocking those seeds produced mostly inside-out or incomplete first-contact order, not outside-in descent.
3. **Missing concurrent activation — remains the candidate diagnosis, not uniquely identified.** The result removes the exact gate as an alternative explanation for absent directional ordering. It does not directly manipulate concurrent activation, so a concurrency mechanism would require a separately preregistered experiment.

In short: the gate authored the deadlock; the coupling authored no reliable direction. No fresh-seed descent cycle is warranted by T4.1c.

## Artifacts

- `summary.json`: per-arm criteria metrics and interpretation.
- `contact_arm_metrics.csv`: 30 arm-by-seed rows with first-contact sequences, sessions, counts, and shuffle control.
- `posterior_traces.csv`: arm/rule, access, contact occurrence, write scale, applied size, and write mass for every session.
- `criteria-results.json`, `status.json`, `metadata.json`, formation/provenance files, blocking-strength audit, forecast control, and prior write-size sweep remain in the pilot directory.

## Blockers and caveats

- No implementation or execution blockers.
- No arm reached the 8/10 ordering threshold, so the preregistered conditional A4.shuffle-history reporting trigger did not fire; all-arm shuffle results are reported only as an additional audit.
- This is pilot evidence on reused seeds 1001–1010. No confirmatory claim is made.
- The two one-cause seeds make complete ordering structurally impossible and remain scored as failures by the frozen rule.
