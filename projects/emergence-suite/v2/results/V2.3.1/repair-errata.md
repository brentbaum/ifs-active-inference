# V2.3.1r instrument-repair errata

Status: **instrument repair verified; V2.3.1 Gates 2 and 3 fail on
invalidate-and-repeat; C-V23b (repaired instrument) FAIL.**

This erratum preserves the original V2.3.1 freeze, its defective-instrument
gate results, and both original sealed failures. V2.3.1r is the same declared
strain and the same parameter block, with only evidence normalization
repaired. No V2.3.2 mechanism was implemented.

## Defect and original decomposition

The declared `bounded_log_odds_accumulation` factor is an energy potential
inside each structure candidate. The defective implementation sent its raw
potential to model comparison without dividing by the candidate's partition
function. The exact engine therefore counted an H-dependent partition ratio
as evidence even when all discriminating observations were masked.

On the original audited neutral slice, the spurious BF was
`1.00323715997684`. Across the four C-V23b Test-4 pairs, the defective
available-minus-replay structure-log-odds decomposition was:

| Component | Log-odds contribution |
|---|---:|
| Declared structure transition | `+2.09630316911` |
| Genuine normalized likelihood | `+0.195027086259` |
| Erroneous partition term | `-3.16277382303` |
| Net final difference | `-0.871443567663` |

The partition term reversed the sign of the legitimate contributions.

## Authorized repair

After all frozen V2.3.1 factors are compiled, V2.3.1r exactly computes the
no-observation partition for each H candidate and adds its reciprocal as a
normalization factor. Interventional models normalize separately for
`do(A=engage)` and `do(A=avoid)`. Normalized leaf likelihoods (`B`, `Q`, `X`,
and `O`) sum out analytically; the remaining binary variables are enumerated
exactly.

The repair does not change:

- the accumulation score or cap;
- any candidate contrast, transition, likelihood, prior, or parameter;
- any protocol field, action mode, seed, RNG stream, readout, or threshold;
- any V2.0, V2.1, V2.2.1, V2.3, or frozen result artifact.

## Exact verification

The repair regression suite uses a fresh Cartesian enumerator with no shared
elimination intermediates.

| Check | Result |
|---|---:|
| Masked BF, `do(A=engage)` | `1 ± 4.44e-16` |
| Masked BF, `do(A=avoid)` | `1 ± 4.44e-16` |
| Masked BF, generated action | `1 ± 4.44e-16` |
| Equally predicted outcome contribution | `1` to `1e-12` |
| Repeated masked slices | posterior H equals transition prediction to `1e-12` |
| Audited C-V23b trajectories | 8 |
| Audited slices | 900 |
| Maximum absolute artifact log BF | `4.44e-16` |
| Maximum absolute trajectory artifact sum | `1.67e-15` |

## Cross-stage partition sweep

The sweep asks whether any potential has a partition function that depends on
the compared structure after masked observations are marginalized.

| Stage / factor family | Partition check | Status |
|---|---|---|
| V2.0 conditional templates (chain, fork, collider, temporal) | Every child row sums to 1 exactly. | Clean |
| V2.0 finite model comparison `p(D|H)` | Fixed row sum `1.0`; beta-binomial row sum `0.9999999999999984`. | Clean |
| V2.1 monitor, broadcast/return, and precision likelihoods | Maximum child-row error `0.0`, broadcast on and off. | Clean |
| V2.2.1 spike/slab association `p(K|Z)` | Null row `1.0`; slab row `0.9999999999999304` across tested histories. | Clean |
| V2.2.1 seam conditional factors | Maximum child-row error `0.0` at zero, low, and high association. | Clean |
| V2.3 conditional candidate factors | Masked candidate BF differs from 1 by at most `2.18e-14`; no accumulation potential exists. | Clean |
| V2.3.1 accumulation potential, defective implementation | H-dependent partition; masked BF `1.00323715997684` initially and state-dependent thereafter. | **Affected** |
| V2.3.1r accumulation potential | Candidate/action-conditional partition explicitly normalized; maximum audited artifact log BF `4.44e-16`. | Repaired |

No earlier-stage factor has the same defect class.

## Gates 1–5, same frozen parameters and development seeds

Outputs are retained under `results/V2.3.1r/`. The exhaustive numeric-leaf
comparison is `results/V2.3.1r/metric-diff.json`: 865 of 1,818 shared numeric
leaves moved. This file reports every moved numeric metric with defective
value, repaired value, and delta.

| Gate | Repaired verdict | Localization |
|---|---|---|
| 1 — semantic routes | PASS | Exact semantic and bounded-evidence obligations survive. |
| 2 — recovery | **FAIL** | Structure ECE moves `0.089366 → 0.105795`, above the frozen `0.10` ceiling. Accuracy improves `0.929688 → 0.953125`; Brier improves `0.065671 → 0.054505`. |
| 3 — direct composition/generalization | **FAIL** | Original open-assay thresholds pass, but surface incremental CV R² moves `0.025006 → 0.617333` (limit `0.05`) and paired low-minus-high control moves `0.319456 → 0.072760` (minimum `0.20`). |
| 4 — selective lesions | PASS | All three repaired lesions meet their frozen thresholds; inherited stages pass. |
| 5 — cumulative regression | PASS | Sensitivity, determinism, continuity, and all inherited cumulative gates pass. |

Every V2.0, V2.1, and V2.2.1 cumulative gate remains PASS.

## Principal moved scientific metrics

| Metric | Defective | Repaired | Delta |
|---|---:|---:|---:|
| Acute formation final persistent mean | `0.831123` | `0.732003` | `-0.099120` |
| Gradual accumulation final persistent mean | `0.991527` | `0.936357` | `-0.055170` |
| Low-minus-high control, original open assay | `0.151583` | `0.180703` | `+0.029120` |
| Closed-loop persistent-model effect | `0.136985` | `0.083066` | `-0.053919` |
| Adaptive real-threat persistence | `0.962922` | `0.871119` | `-0.091804` |
| Generalization surface incremental CV R² | `0.025006` | `0.617333` | `+0.592327` |
| Generalization low-minus-high control | `0.319456` | `0.072760` | `-0.246696` |
| Expanded p99 slice change | `0.097067` | `0.079118` | `-0.017949` |
| Expanded maximum slice change | `0.168948` | `0.144116` | `-0.024832` |

The repaired original open assays still satisfy their frozen thresholds:
acute `0.7320`, gradual `0.9364`, low-minus-high control `0.1807`,
adaptive threat `0.8711`, and closed-loop persistent-model effect `0.0831`
with its 95% interval above zero. The failed Gate 3 is specifically the
expanded generalization criterion.

## C-V23b (repaired instrument)

The repeat uses the original 120 paired base seeds (`809301:809420`), all 240
world trajectories, the original stream family, thresholds, and frozen p99
reference. Results are under
`results/challenges/C-V23b-repaired-instrument/`; the original
`results/challenges/C-V23b/` is unchanged.

| Test | Verdict | Repaired result |
|---|---|---|
| 1 — formation dose response | **FAIL** | One-acute rates by control level: `[0.1875, 0.1250, 0.1250, 0.1875, 0.0625]`; isotonic p `0.4946`; level-1 and chronic-only (`0/6`) anchors fail. |
| 2 — no-event floor | **FAIL** | Rates by level: `[0, 1.0, 0, 0.6667, 0.6667]`; levels 2, 4, and 5 exceed `0.05`. |
| 3 — continuity | PASS | `0/492` acute slices exceed p99; maximum all-slice change `0.085432`, below `1.75×p99 = 0.169867`. |
| 4 — persistence and mediation | **FAIL** | 6 formed low-control pairs; margin effect `-0.200573`, 95% CI `[-0.965961, 0.564815]`; mediator r `0.50499`, CI `[-0.09705, 0.83647]`; dose partial r `-0.67125`, CI `[-0.89888, -0.15834]`. |

Overall repaired-instrument verdict: **FAIL**.

## Historical C-V23 annotation

C-V23 ran on frozen V2.3, which has no accumulation potential. Fresh
Cartesian marginalization of its compiled candidate model gives:

- generated action, masked BF: `1 + 2.18e-14`;
- `do(A=engage)`, masked BF: `1 + 6.88e-15`;
- `do(A=avoid)`, masked BF: `1 + 7.11e-15`.

Therefore this defect contributed exactly zero within enumeration tolerance
to every C-V23 test. Its original FAIL stands unchanged and requires no
instrument-correction reinterpretation.

## Record status

The defective V2.3.1 freeze and original C-V23b FAIL remain in place with a
pointer to `results/V2.3.2/neutrality-audit.md`. V2.3.1r is verified as an
instrument repair, but its invalidated gate repeat fails Gates 2 and 3 and
its repaired C-V23b repeat fails Tests 1, 2, and 4. No V2.3.2 mechanism work
was performed.
