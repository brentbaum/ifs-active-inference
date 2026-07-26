# V2.3 retained development failures

## Semantic probe 1

Run before open-assay execution, after the public plan and parameters were
frozen.

- Event-precision log-odds increase: `1.733675` (pass).
- Low-control action evidence difference: `0` (pass).
- High-control action evidence difference: `0.171850` (failed frozen `.50`
  threshold).
- Avoid-minus-engage threat probability: `0.359` (failed frozen `.50`
  threshold).
- Reflexive-broadcast persistent-probability effect: `0.126921` (pass).
- Independent finite-comparison error: `2.78e-16` (pass).

Localization:

1. `_scaled_probability` incorrectly clipped every probability below `.5` to
   `.501`; it was written as though all inputs were reliabilities, but the
   action-transition table legitimately contains probabilities on both sides
   of `.5`.
2. The controllability diagnostic compared `log p(O=1|A=0)` with
   `log p(O=1|A=1)`. The frozen plan specifies the policy-consequence
   log-evidence contrast; for binary evidence that is the difference of
   outcome log odds.

Repair: broaden the neutral scaling helper's valid interval to
`.001`–`.999`, and compute the declared binary log-odds contrast. No frozen
parameter, prior, assay schedule, or threshold changed.

## Open profile attempt 1

The first complete recovery run passed:

- structure accuracy / mean true probability: `1.000` / `0.952`;
- structure Brier / ECE: `0.00590` / `0.04789`;
- controllability / broadcast accuracy: `0.828` / `0.992`;
- policy-consequence parameter MAE / coverage: `0.02925` / `0.945`.

The following open-assay process was interrupted before producing an open
result. The pre-action policy query had included downstream `W`, `Y`, and
unobserved `O` in the independent Cartesian check even though their normalized
CPTs marginalize to one before action realization. The replacement query is
the exact ancestral marginal of the same full slice (`H,G,S,C,R,E,A` and
their observations). The full post-action posterior remains checked with
`W,Y` present. No scientific result from the interrupted open run was used.

## Two-world open smoke profile

This non-gating smoke run used seeds 62000–62001 and failed the eventual gate-3
targets:

- acute final persistence: `0.9978`;
- gradual final persistence: `0.2090`;
- acute-minus-controlled: `0.7197`;
- low-minus-high control: `-0.2285`;
- adaptive-danger persistence: `0.0709`;
- closed-loop-minus-replay structure effect: `0.5217`.

Localization and construction repair:

1. The gradual schedule alternated mild events with safe integrated slices, so
   it tested repeated recovery rather than gradual accumulation. The schedule
   now presents consecutive low-precision events.
2. The low/high-control comparison allowed inferred policies to diverge before
   comparing policy consequences. Both arms now replay the same engage policy,
   leaving only action-dependent transitions and observations to identify
   controllability.
3. The adaptive-danger schedule repeatedly generated strong `now` context,
   which correctly favored the transient candidate. Chronic real danger now
   uses collapsed contextual broadcast; persistence must be earned from its
   action-dependent adverse transitions and event evidence.

No frozen parameter or threshold changed.

## Eight-world open development profile

Seeds 62000–62007 still failed three frozen targets:

- acute final persistence: `0.7823`;
- gradual final persistence: `0.2389`;
- acute-minus-controlled: `0.4114`;
- low-minus-high control: `-0.00839`;
- adaptive-danger persistence: `0.03059`;
- closed-loop-minus-replay structure effect: `0.3944`.

Trace localization showed that the candidate-family world factor was
`p(W|C,A)` in both candidates. Thus chronic adverse transitions could not
favor persistent `H/G` coupling; only event/self and expected-outcome factors
differed. This contradicted the frozen persistent-bundle contract. The factor
is corrected to `p(W|H,G,C,A)`, with its root coupling derived from the already
frozen `event_root_coupling`; its coupling lesion restores the factorized
table. The low/high-control assay also uses the same balanced declared action
sequence in both arms, preventing the policy label itself from dominating
consequence-based controllability inference. No frozen parameter or threshold
changed.

## Recovery rerun after coupled-world correction

The first recovery rerun after the final candidate-family correction failed
the frozen structure thresholds:

- confusion matrix: `[[64, 0], [40, 24]]`;
- accuracy / mean true probability: `0.6875` / `0.6457`;
- Brier / ECE: `0.19998` / `0.17379`.

Controllability (`0.789`), broadcast (`0.992`), parameter MAE (`0.02925`),
and parameter coverage (`0.945`) passed.

Localization: the persistent-truth generator reused the deliberately
ambiguous ordinary active-persistence schedule intended for the closed-loop
composition contrast. Candidate recovery now uses the explicit persistent
real-danger family; transient recovery remains an isolated integrated,
controllable event. This changes no factor, parameter, or open assay.

## Sixteen-world open development profile

Seeds 62000–62015 produced:

- acute final persistence: `0.6471` (failed `.70`);
- gradual final persistence / change: `0.9035` / `0.6835` (pass);
- acute-minus-gradual maximum step: `0.05076` (pass);
- acute-minus-controlled: `0.3207` (pass);
- low-minus-high control: `0.2317` (pass);
- adaptive-danger persistence: `0.9973` (pass);
- closed-loop policy / transition / observation effects: `0.3490` /
  `0.1771` / `0.1146` (pass);
- closed-loop structure / root effects: `0.0162` / `0.0297`, with intervals
  crossing zero (fail);
- realized mediator effect: `0.1565` (pass).

Localization: the transient and persistent candidates assigned almost the
same high threat probability to avoidance transitions (`.86` versus `.88`),
so the realized action-generated evidence could not identify the coupled
candidate. The transient transition retains action dependence but caps its
avoidance-threat row at `.50`; the persistent `H=1,G=1` row retains the frozen
`.88` coupling. The environment generator remains the frozen physical
action-transition process and does not inspect `H` or `G`. Acute and matched
controlled schedules each gain one identically placed event slice to estimate
their stable final means. No frozen parameter or threshold changed.

## Intervention-semantics correction

The next trace audit showed that `declared` and `engage_replay` actions were
conditioned through `p(A|H,G,C)`. That treats an externally replayed policy as
evidence about the latent state rather than as an intervention. It especially
penalized the persistent candidate during repeated engage replays, regardless
of the realized transition.

Declared and replay actions now compile as `do(A)`: only the policy-prior
factor is absent on those slices. The action-controlled transition,
expected-outcome factor, common outcome likelihood, and conjugate consequence
update remain. Closed-loop actions retain `p(A|H,G,C)`. Gradual accumulation
uses balanced declared actions to isolate accumulating event evidence, and
adaptive real danger uses high event precision with collapsed context so the
persistent candidate can be correct for an enduring threat. No frozen
parameter or threshold changed.

The active-persistence schedule now gives both paired arms the same two-slice
high-precision activation followed by twelve ordinary slices. This prevents
formation from saturating on exogenous evidence while ensuring the policy
posterior is engaged before the action-dependent phase. A 16-world
construction check yielded mean paired policy, transition, observation,
structure, root, and realized-mediator effects of `0.430`, `0.250`, `0.195`,
`0.110`, `0.205`, and `0.203`, respectively. The full 64-world run remains the
gating estimate.

The open schedule implementation then adopted the intended evidential doses:
gradual accumulation uses 20 ordinary slices followed by five elevated but
distributed slices (rather than one acute injection); the low/high-control
comparison uses 40 matched policy-consequence trials; and active-persistence
uses ordinary event precision so its closed-loop difference cannot be
saturated by overwhelm alone. These are assay-dose definitions, not parameter
changes.

## Recovery calibration follow-up

The explicit persistent-danger recovery family reached perfect structure
classification but missed structure ECE (`0.10654` versus `.10`) and
controllability accuracy (`0.74219` versus `.75`). Real-danger rows
intentionally provide little control discrimination, so primitive
controllability recovery is now measured on the matched 40-trial low/high
control schedules. The transient recovery trace is lengthened from seven to
twelve slices around the same single mild event to calibrate confidence in
transience. Structure and control remain generated and inferred, not assigned.

That separation raised controllability accuracy to `0.906` and kept perfect
structure classification, but structure ECE remained `0.10284`. The
transient generator therefore uses a three-slice mild integrated event cluster
inside the same twelve-slice trace. Replicated now-context likelihoods, not a
prior or threshold change, provide the additional calibration evidence.

## Freeze validation correction

The first successful freeze writer produced an intact reflexive-broadcast
lesion contrast of `-0.06543`, reduced to numerical zero by lesion. The probe
had used `X=0`, whereas the registered semantic prediction concerns the
`X=1` now-context observation. The lesion probe now uses that same observation
in both integrated and collapsed arms. This aligns direction and
disappearance; no model, parameter, gate threshold, or open result changes.
The complete freeze writer is rerun rather than patching result files.
