# V2.3.2 pre-mechanism no-evidence neutrality audit

Status: **FAIL — nonzero bookkeeping artifact. Stop before V2.3.2
mechanism design.**

This audit was run first, as required by §0 of
`projects/ifs-paper/suite-v2-v232-plan.md`. It tests the frozen V2.3.1
stage at commit `7d5650c`; its 64-file freeze manifest was unchanged and
had already been identity-verified for C-V23b. No V2.3 or V2.3.1 engine,
parameter, contract, protocol, result, or manifest file was modified.

The audit used no new development worlds. The generic apparatus checks are
analytic and seed-free. The C-V23b decomposition replays only the four
already-released low-control pairs that defined its persistence failure
(seeds 809307, 809342, 809345, and 809384).

## Verdict

The frozen V2.3.1 graph is not neutral when all
structure-discriminating observation channels are masked. The exact
per-structure partition masses on the initial neutral slice are

`Z_transient = 1.00376009`

`Z_persistent = 1.00700942`.

Consequently, the masked slice contributes

`BF_persistent:transient = 1.00323715997684`

and

`log BF = +0.00323193165472`

in addition to the declared structure transition. The required value is
exactly 1 (log BF 0). This residual is small for the first slice but is
state-dependent and compounds as latent posteriors change.

The residual is a **bookkeeping artifact**, not informational evidence and
not a numerical error. Per the adopted stop rule, the V2.3.2 public contract,
F/M analysis plans, and dummy bundles were not created in this run.

## Analytic audit

Let `q_t(H)` be the carried structure posterior and `T_H` the declared
structure-transition CPT. The legitimate prediction is

`q^-_t(H) = Σ_h q_(t-1)(h) T_H(h,H)`.

For observations `o_t`, a normalized generative model should then satisfy

`logit q_t(H=1) - logit q^-_t(H=1) = log p(o_t|H=1) - log p(o_t|H=0)`.

When every structure-discriminating observation is masked, each normalized
CPT sums to one and the right-hand side must be zero.

V2.3.1 additionally contains
`bounded_log_odds_accumulation(H,E,K,C,R,Y)`, with potential

`ψ = exp((2H-1)s(E,K,C,R,Y)/2)`.

It is not a conditional distribution over a declared child and is not
normalized separately for each `H`. After the ordinary latent CPTs are
marginalized, the no-observation mass is therefore

`Z_H = E_H[ψ(H,E,K,C,R,Y)]`,

not 1. Because `E`, `C`, `R`, and `Y` remain latent when their observation
channels are masked, their predicted distributions still weight the
potential. In general `Z_1/Z_0 != 1`. The exact engine faithfully treats
this as model evidence, even though no datum was observed.

Thus the apparatus-first localization is:

1. The observation-mask operation itself correctly removes the observation
   likelihood.
2. The exact inference engine correctly sums the factors it is given.
3. The compiled structure candidate is not a normalized generative
   distribution conditional on `H`, because the standalone accumulation
   potential has an `H`-dependent partition function.
4. That partition-function ratio is incorrectly counted as slice evidence.

This is a model-evidence bookkeeping/compilation defect. It is not evidence
for or against the scientific attribution mechanism proposed for V2.3.2.

## Exact-enumeration method

Two independent paths were compared:

- the frozen `ExactEngine`, using its ordinary elimination path; and
- a fresh Cartesian enumerator written for this audit, which fixes `H`,
  iterates every assignment of all remaining binary variables, multiplies
  the declared factor entries directly, sums their masses, and divides out
  the declared `H` prior to obtain candidate-conditional evidence.

The fresh enumerator imports no oracle and shares no elimination
intermediates with the engine. On the initial masked slice, the maximum
engine/enumerator conditional-evidence difference was
`1.20e-14`. Across masked and fully observed representative safe slices from
all eight C-V23b trajectories used below, the maximum difference was
`8.88e-15`.

## The four §0 properties

| Property | Exact result | Verdict |
|---|---:|---|
| Masked outcome BF exactly 1 | With `do(A=engage)` retained and all observation channels masked, BF = `1.00323715997684`; the observation mask contributes no factor, but the latent accumulation partition contributes the residual. | **FAIL** |
| Equally predicted outcome BF exactly 1 | Replacing only `p(O|Y)` by identical `[0.5,0.5]` rows gives an outcome-channel contribution BF of `0.999999999999998` (absolute error `1.78e-15`). The total slice still contains the separate partition artifact. | **PASS for the outcome channel; FAIL for total-slice neutrality** |
| Repeated masked outcomes produce no decay | Starting at the exact stationary probability of the declared structure transition, `p(H=persistent)=0.8`, 60 fully masked `do(A=engage)` slices move it to `0.962575031373`; cumulative artifact log BF is `+4.14745002305`. There is no literal decay in this example, but there is large evidence-free strengthening, so the required plateau fails. | **FAIL** |
| All decay traceable to declared transitions or real likelihood differences | C-V23b contains a nonzero residual partition term, quantified below. | **FAIL** |

For the repeated-mask check, the declared Markov transition leaves 0.8
exactly unchanged before evidence on the first slice. The first posterior is
`0.800516607723`; slices 10, 30, and 60 end at `0.820666264707`,
`0.904164112610`, and `0.962575031373`. The corresponding masked BFs grow
from `1.00323715998` to `1.13291546254` as the other latent posteriors are
carried forward.

## C-V23b persistence-erosion decomposition

The decomposition uses log odds and the four replay-selected low-control
pairs from the retained C-V23b Test-4 failure. For each slice:

`Δ log odds = d_t + g_t + a_t`,

where

- `d_t` is the change from the declared `structure_transition` before
  observations;
- `a_t = log Z_1(masked)/Z_0(masked)` is the bookkeeping partition term,
  retaining an observed action only when it is a declared intervention; and
- `g_t = log BF_full - a_t` is the normalized likelihood contribution of
  the actual observations. In the closed-loop arm, an action generated by
  the frozen policy factor remains part of the actual likelihood; in the
  replay arm, `do(A=engage)` is retained as an intervention and contributes
  no action likelihood.

Positive values favor greater persistence in avoidance-available relative
to replay; negative values are erosion in the available arm.

| Available minus replay, mean over 4 matched pairs | Signed log-odds contribution |
|---|---:|
| Declared structural dynamics `(i)` | `+2.09630316911` |
| Genuine observation likelihood `(ii)` | `+0.195027086259` |
| Bookkeeping artifact `(iii)` | `-3.16277382303` |
| Observed full likelihood difference | `-2.96774673677` |
| Net final structure-log-odds difference | `-0.871443567663` |

The identity closes to

`+2.09630316911 + 0.195027086259 - 3.16277382303`

`= -0.871443567663`,

with maximum per-trajectory numerical closure error `3.33e-14`.

Therefore neither declared structural dynamics nor genuine likelihood
differences explain the paired erosion: both slightly favor the
avoidance-available arm in this subset. The artifact contributes
`-3.16277` log-odds units and reverses their combined sign.

Restricting the same decomposition to safe (`actual_event=0`) slices gives:

| Safe slices only, available minus replay | Signed contribution |
|---|---:|
| Declared structural dynamics | `+1.79965507471` |
| Genuine safe-observation likelihood | `+1.29926007208` |
| Bookkeeping artifact | `-2.67023569316` |
| Full safe-slice likelihood difference | `-1.37097562108` |

On these safe slices the transient candidate has no genuine likelihood
advantage in the paired contrast: the normalized observations instead favor
the persistent candidate by `+1.29926`. The apparent transient advantage in
the frozen evidence readout is the negative partition term.

For completeness, averaging the eight trajectories without taking the
paired contrast gives `+1.68485206509` from declared transitions,
`+1.14175454114` from genuine likelihood, and `-0.445904027342` from the
artifact, for a mean net log-odds increase of `+2.38070257890`. The artifact
is therefore not a constant offset: its sign and size depend on the carried
latent state, which is why it creates a much larger arm difference than its
unpaired mean suggests.

## Stop

Component `(iii)` is decisively nonzero. Under the binding Phase-1 rule,
this report is the only deliverable produced. No V2.3.2 mechanism contract,
analysis plan, dummy bundle, implementation, or repair is included; repair
classification is deferred to evaluator adjudication.
