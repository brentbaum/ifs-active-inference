# Experiment 43 specification: an IFS bundle found through guided inquiry

**Status:** Proposed handoff specification; not yet piloted or preregistered  
**Date:** 2026-07-15  
**Implementation home:** `projects/emergence-suite/continuous/`  
**Paper home:** `projects/ifs-paper/`  
**Starting point:** Experiments 39–42, especially
`src/UnifiedRelationalAgent.jl` and
`src/ConfirmRelationalActionInteraction.jl`

## 1. The question

Build the smallest model that can test two linked ideas without defining either
one into existence:

1. A burdened part is not one belief. It is an organized pattern linking a
   self-model, a world-model, a protective policy, and an expected outcome.
2. A therapist can help change that pattern by guiding where inquiry turns
   without supplying the conclusion the client is required to reach.

The first idea concerns the **target of learning**. The second concerns the
**policy for finding evidence**. Keep them separate in code, controls, and
interpretation.

The experiment should also represent loving contact as evidence. A client's
part is activated and shown; a steady other meets it with care rather than the
predicted rejection or control. This interpersonal observation is potentially
transformative evidence about the bundle's expected outcome. It is not a gate,
a generic safety bonus, or the only observation capable of revision.

The experiment is a construction-level test. Even a clean success would not
establish a clinical effect, a biological implementation, or the ontology of
parts.

## 2. Plain-language thesis

Use this sentence to keep the implementation honest:

> What defines a part is not any single expectation, but the way expectations
> about self, world, action, and outcome have become organized together.

Use **configural** only as a statistical adjective for that organization.
Reserve **relationship** and **relational** for the interpersonal relation.
The relationship can make evidence admissible; guided attention can make it
findable. Neither substitutes for the other.

Do not describe a failed sample as “avoidance prevented discriminating
evidence.” The neutral computational statement is:

> The frozen bundle's existing policies leave some identity-relevant
> observations unsampled or unable to update the joint model.

## 3. Minimal architecture

### 3.1 Explicit bundle

Let the latent identity root be

\[
g \in \{-1,+1\}.
\]

Give the part four explicit binary variables:

\[
b=(b_{self},b_{world},b_{policy},b_{outcome}).
\]

Their clinical gloss is fixed for interpretation, not used by the inference
code:

| Variable | Frozen pole | Present-compatible pole |
|---|---|---|
| `self` | deficient, unwanted, or unsafe to reveal | acceptable and able to be known |
| `world` | rejecting, controlling, or unavailable | responsive enough to learn from |
| `policy` | conceal, appease, attack, or withdraw | remain present and sample |
| `outcome` | rejection, engulfment, or abandonment | contact without the predicted catastrophe |

The first version should remain binary. Do not add multiple parts, protector
stacks, continuous valence, or a language model.

### 3.2 The target distribution

Generate complete bundle scenes from a conditional joint distribution

\[
p(b\mid g,\Theta) \propto
\exp\left(
  \sum_j h_j g b_j
  + \sum_{j<k} J_{jk} g b_j b_k
\right).
\]

The local terms `h` make every component partly informative. The coupling
terms `J` make some combinations more informative than their components taken
separately. Choose the smallest nonzero coupling pattern that produces this
property in pilot runs. Record all retained coefficients in the frozen config.

The agent must **learn** the conditional joint table or its log-linear
parameters from complete training scenes. It must not receive the true `J`
matrix as an inference prior. With four binary variables, a conditional
Dirichlet table over the 16 configurations is the simplest auditable learner.

This requirement prevents a circular result in which the experiment authors
declare that a part is joint structure, hand the agent exactly that structure,
and then celebrate its use.

### 3.3 Matched factorized target

Construct the exact factorized projection

\[
p_{fact}(b\mid g)=\prod_j p_{joint}(b_j\mid g).
\]

It must preserve every conditional local marginal to numerical precision while
removing only higher-order dependence. It retains the same shared identity root
`g`. This distinguishes an effect of bundle organization from an effect of
merely having a common cause.

Run both of these comparisons:

- **Matched-world comparison:** generate and infer with either the learned joint
  model or its exact factorized projection.
- **Exact-action replay:** give the factorized inference model the joint
  agent's exact actions and observations. This isolates binding from action.

For a capacity check, run the same joint learner after independently shuffling
the alignment of bundle components within each value of `g`. This preserves
the local marginals, parameter count, optimizer, and training volume while
destroying cross-component organization. Also report held-out log score or
model evidence so that a raw higher-capacity in-sample win is never called a
discovery of bundle structure.

### 3.4 Gaussian observation hierarchy and precision field

Each of the four bundle variables drives its own three-level Gaussian branch:

\[
b_j \rightarrow x_j^{(3)} \rightarrow x_j^{(2)}
\rightarrow x_j^{(1)} \rightarrow s_j.
\]

Extend the current explicit hierarchy from three to four bundle channels. The
global hyper-model forecasts the 12 layer-by-channel log precisions
`Phi[layer, channel]`. If loving contact is a scalar observation, append one
learned contact-likelihood log precision to the same field rather than
pretending it is a fifth bundle variable. Inference alternates between
`q(x, b, g)` and `q(Phi)`; lower-level residuals provide the second-order
errors; the revised field is rebroadcast downward. Log local, hyper, and joint
free-energy traces.

Preserve the current identifiability boundary. Bottom-only observations
identify total branch variance, not an otherwise invisible decomposition into
three unique layer precisions. Do not claim layer-specific recovery unless the
experiment adds direct layer observations. The global field may improve
forecasting and sampling while its layerwise decomposition remains
underdetermined.

No scalar depth variable may enter an update, gate, likelihood, precision, or
action bonus. If a depth summary is reported, it is a readout of the inferred
precision field only.

### 3.5 Loving contact as an observation

Add one always-visible interpersonal observation, `contact_t`, outside the four
target channels. It reports how the activated material is met. In the primary
condition it contradicts the bundle's expected rejection while preserving the
fact that the part is active.

Requirements:

- The realized contact observations are identical across inquiry, random
  guidance, autonomous inquiry, and conclusion-injection arms.
- Contact enters inference as data. It must not directly lower part precision,
  raise context precision, flip a gate, or award utility.
- Its forecast precision is learned within the same global field machinery.
- It must be informative without becoming individually decisive: report its
  mutual information with `g` and verify that the contact-only arm does not
  saturate root inference.
- Include `contact_absent` and `contact_misattuned` stress cells, but do not use
  them to imply that relationship is the only possible revising content.
- In the primary comparison, every guidance arm receives the same quantity and
  quality of contact so that loving contact is not confounded with the form of
  guidance.

The simplest implementation can make `contact_t` conditionally informative
about `b_outcome` and `g` after disclosure. If it is implemented as a fifth
Gaussian branch, keep it observational: it is evidence about what happened in
the interpersonal encounter, not a fifth member of the IFS bundle.

## 4. Inquiry and conclusion arms

### 4.1 Actions

At each inquiry step, an action selects one unsampled bundle channel. The
environment returns the observation generated on that channel. The observation
value is never chosen by the guide.

Use a two-packet budget over the four bundle channels. Compare:

1. **Autonomous precision-guided inquiry:** the client's policy selects the
   channel with the greatest expected information gain under its current
   precision forecast.
2. **Therapist-scaffolded inquiry:** the guide selects which channel to sample
   using the same information-gain objective, with a better calibrated forecast
   during early sessions. It supplies a question, not an answer.
3. **Matched random guidance:** the guide selects channels randomly under the
   same action and communication budget.
4. **Conclusion injection:** instead of selecting a channel, the guide supplies
   a high-precision pseudo-observation about `g` or a bundle component. The
   client does not receive the corresponding environment-generated observation.
5. **No additional guidance:** contact remains present, but no extra bundle
   packet or conclusion is supplied.

The inquiry arms operationalize therapist-guided attention. They do not claim
that the therapist “turns up epistemic depth.” A guide may scaffold both a
precision forecast (what is currently trustworthy) and a sampling policy
(where inquiry should turn next), but these are different operations.

### 4.2 Fairness of the conclusion comparison

Report two budget matches:

- **Interaction-budget match:** the same number of guide interventions.
- **Information-budget sensitivity:** tune the conclusion reliability so its
  expected information at the start of an episode matches the inquiry packet's
  expected information, then rerun the comparison.

Never require inquiry to beat a perfectly accurate oracle conclusion on
immediate accuracy. An accurate, stable conclusion may be faster. The stronger
prediction is about calibration, generalization, resistance to suggestion,
and performance after the guide is removed.

### 4.3 Guide reliability and context change

Cross the inquiry-versus-conclusion contrast with four guide regimes:

- `accurate_stable`: advice remains calibrated;
- `noisy`: reliability is uncertain and observable across trials;
- `systematically_wrong`: the guide repeatedly favors the wrong root or
  component;
- `context_switch`: early guidance was locally useful, but the relevant
  precision profile changes out of sample.

In an inquiry arm, a mistaken guide sends attention to a less informative
channel, but the observation still comes from the world/client process. In the
conclusion arm, a mistaken guide supplies the mistaken content itself. This is
the proposed mechanical reason that questions may be safer than therapist-
supplied interpretations under uncertainty.

### 4.4 Scaffold removal and policy learning

After repeated guided sessions, remove the guide while leaving the learned
client model intact. Test two things separately:

- retention of the learned **precision profile** across the context switch;
- retention of the learned **sampling policy**, measured by which channel the
  client chooses first without guidance.

Do not infer policy learning merely because precision forecasting improved.
If internalizing a policy requires a new learning rule, implement a minimal
contextual bandit or Dirichlet action table and ablate it explicitly. Name this
Stage 43C and do not let its failure invalidate the simpler 43A bundle test.

## 5. Experimental sequence

The stages are gates. Do not tune later stages to conceal an earlier failure.

### Stage 43A — Is the target really a bundle?

Run learned joint and matched-factorized worlds with autonomous inquiry,
matched random sampling, and exact-action replay.

Primary questions:

- Does learned joint structure improve inference of the shared identity root?
- Does it improve transfer to held-out combinations and untreated cues?
- Does precision-guided sampling become more useful when the answer lives in a
  pattern rather than in one component?
- Does a configuration-violating world remove or reverse the joint-model
  advantage?

Stop and record a null if the joint learner only memorizes training
configurations, if local marginals cease to match, or if the shared root alone
explains the result.

### Stage 43B — Inquiry versus supplied conclusions

Only after 43A is interpretable, add therapist-scaffolded inquiry, random
guidance, conclusion injection, and equal loving-contact evidence. Cross these
with guide reliability and the out-of-sample context switch.

Primary questions:

- Is conclusion injection faster when it is accurate?
- Is inquiry better calibrated and less suggestion-prone when the guide is
  noisy, wrong, or stale after a context switch?
- Does inquiry produce more transfer to unsampled bundle components?
- Does its advantage grow in the joint bundle world relative to the matched
  factorized world?

### Stage 43C — Is guided attention internalized?

Only if 43B shows a coherent inquiry effect, add the minimal policy-learning
rule and remove the guide. Test whether the client continues to choose useful
channels before local loops have fully relearned after the switch.

This is the computational analogue of learning how to turn toward one's own
experience. It is not established by Experiments 39–42, which learned a
precision profile rather than a sampling policy.

### Stress cell — Coordinated, not rigidly global

In every stage, include a late regime in which one channel's reliability
departs from the shared global pattern. Compare:

- adaptive global `Phi`, which can reduce inappropriate tying;
- rigid global `Phi`, whose coupling is fixed;
- matched independent local meta-loops.

The desired result is conditional globality: global coordination helps while
the channels share structure and releases when they do not. A rigid global
interpretation should become confidently wrong in the deviation regime. This
is the model-level distinction between epistemic depth and an over-rigid global
interpretation.

## 6. Measures

Log per episode, arm, seed, and stage:

- posterior probability and decision for `g`;
- posterior probability for all four bundle variables;
- joint bundle log score and calibration;
- root accuracy, log loss, and Brier score;
- held-out configuration accuracy;
- transfer to untreated cues and unsampled components;
- false-root revision and false-component revision;
- time or packets to the first correct revision;
- first and second selected channel;
- expected and realized information gain per action;
- guide dependence after scaffold removal;
- precision forecast error before and after the context switch;
- global coupling/release weight in the deviation regime;
- local, hyper, and joint free-energy traces;
- exact packet, intervention, replay, and contact budgets.

Report Self-energy only as a multivariate descriptive profile if useful:
representational breadth, part opacity, flexible attention, and revision
availability. Do not average these into a causal master scalar. The simulation
can show operations that resemble expressions of Self-energy; it cannot
identify Self-energy itself.

## 7. Frozen controls

The confirmatory run must include all of the following:

1. exact conditional-marginal factorized projection;
2. exact-action and exact-observation replay;
3. matched-budget random sampling;
4. precision-blind action ranking while preserving perceptual precision;
5. independent local precision meta-loops;
6. rigid global precision tying;
7. configuration-violating scenes;
8. loving contact held identical across guidance arms;
9. contact absent and misattuned stress cells;
10. accurate, noisy, wrong, and stale conclusion sources;
11. scaffold-removal probe, if Stage 43C is run;
12. a shuffled-label check showing that learned coupling does not survive when
    bundle configurations are destroyed.

## 8. Preregistration and decision rules

### 8.1 Seed discipline

- Pilot only on `16901:16910`.
- After the model, coefficients, plots, and thresholds are frozen in a commit,
  run confirmation once on untouched seeds `17001:17020`.
- Stress cells may use `17101:17120`, frozen before opening.
- Preserve all misses. Do not round a failed threshold down or rerun until it
  passes.

### 8.2 Implementation criteria

All must pass before empirical interpretation:

- maximum conditional local-marginal mismatch `< 1e-10`;
- replay action and observation match rate `= 1.0`;
- action, packet, contact, and intervention budgets exactly equal where
  declared matched;
- all local, hyper, and joint energies finite;
- joint free-energy traces non-increasing to tolerance `1e-8`;
- the scalar depth readout has no downstream consumers;
- inquiry guides never set observation values;
- conclusion arms never receive the displaced inquiry observation;
- contact streams are byte-identical across paired guidance arms;
- the agent's learned joint parameters are initialized independently of the
  data-generating joint coefficients.

### 8.3 Frozen empirical criteria

Freeze exact thresholds after the pilot and before confirmation. Unless the
pilot supplies a principled reason to change them, use:

- **Bundle gain:** learned joint root accuracy exceeds exact-action factorized
  replay by at least `0.03`, with paired wins on at least `15/20` seeds.
- **Transfer gain:** learned joint held-out transfer exceeds the factorized
  model by at least `0.03`, with paired wins on at least `15/20` seeds.
- **Action interaction:** the precision-guided-minus-random gain is at least
  `0.03` larger in the joint world than in the matched-factorized world.
- **Adversarial reversal:** configuration-violating scenes remove or reverse
  the joint advantage; their paired 95% interval must not support a positive
  advantage of `0.03` or more.
- **Guidance calibration interaction:** under noisy, wrong, and stale guidance,
  inquiry improves log loss over conclusion injection with a paired 95%
  interval excluding zero. Immediate accuracy under `accurate_stable` is
  descriptive and may favor conclusions.
- **Suggestion cost:** under `systematically_wrong`, conclusion injection
  causes more false-root revision than inquiry, with a paired 95% interval
  excluding zero.
- **Post-scaffold transfer:** if 43C is run, guided inquiry beats random guidance
  by at least `0.03` after removal and chooses the newly informative channel
  first in at least `75%` of post-switch episodes.
- **Calibrated release:** adaptive global `Phi` beats rigid global tying in the
  local-deviation regime and does not lose its coordinated-regime advantage
  over independent loops; both paired 95% intervals must exclude zero.

Report paired effects, per-seed win rates, and two-sided 95% Student `t`
intervals. Treat exact equality, marginal matching, budget matching, and
line-search descent as implementation checks, not empirical findings.

### 8.4 Status labels

Give 43A, 43B, and 43C separate statuses:

- `support`: every frozen criterion for the stage passes;
- `mixed`: the primary interaction passes but at least one other criterion
  fails;
- `null`: implementation is valid but the primary effect is absent;
- `falsified`: a named adversarial result contradicts the proposed mechanism;
- `invalid`: an implementation or matching check fails.

Never let success in 43B or 43C rewrite a failed 43A status.

## 9. What outcomes would mean

### Results that strengthen the paper

The bundle claim is strengthened if a learned joint model revises a shared
identity root, transfers to untreated components, survives exact-marginal and
capacity checks, and loses its advantage when the configuration is violated.

The guided-attention claim is strengthened if inquiry remains calibrated under
guide error, transfers beyond the sampled component, and continues after the
scaffold is removed. A larger inquiry advantage for the joint bundle would
support the prediction that guidance matters most when the answer lives in a
pattern rather than one fact.

The loving-contact claim is strengthened if contact supplies direct evidence
against the expected interpersonal outcome while inquiry still adds value by
finding the bundle components that make that evidence identity-relevant.

### Results that weaken or refine the paper

- If joint and factorized models perform equally, the shared root may be doing
  the work; the paper should not call parts configural causes on this evidence.
- If only the sampled component changes, the model has not shown identity-level
  revision or bundle transfer.
- If a higher-capacity joint model wins only in-sample, the result is
  memorization, not structure learning.
- If accurate conclusions remain equally calibrated, transferable, and robust
  after context change, the simulation supplies no reason to privilege inquiry
  over interpretation.
- If loving contact alone produces the whole effect, attention is unnecessary
  in this construction. If attention works identically without contact,
  relationship is not doing the proposed evidential work.
- If rigid global tying beats adaptive release in the deviation regime, the
  implementation has confused globality with depth.
- If policy behavior changes after scaffolding without an explicit policy
  learning rule, the implementation has mislabeled precision-profile learning
  as attention-policy learning.

## 10. Implementation plan

### Task 1 — Add failing unit tests for the four-node target

**Modify:** `projects/emergence-suite/continuous/test/runtests.jl`  
**Create:** `projects/emergence-suite/continuous/src/IFSBundleInquiry.jl`

Test exact conditional marginals, learned-joint initialization independence,
four explicit target channels, three explicit Gaussian levels per channel, and
configuration-violation behavior. Run:

```bash
~/.juliaup/bin/julia --project=projects/emergence-suite/continuous \
  projects/emergence-suite/continuous/test/runtests.jl
```

Commit the tests and minimal model separately.

### Task 2 — Extend the precision hierarchy from three to four channels

Reuse generic operations from `src/UnifiedBeautifulLoop.jl`; do not duplicate
its optimizer. Parameterize channel count where simple. If generalizing the old
module creates broad regression risk, keep the four-channel adapter inside
`IFSBundleInquiry.jl` and share only pure helpers.

Add tests for 12 bundle components plus the scalar contact precision in `Phi`,
endogenous residuals, downward rebroadcast, finite local/hyper/joint energies,
and monotone joint free energy.

### Task 3 — Implement evidence-selection arms

Add autonomous, scaffolded, random, conclusion, and no-guidance policies. Use
one action interface and one explicit budget ledger. Add paired episode
generation so all arms can consume identical latent scenes and contact streams.

Test that inquiry changes only the channel index, conclusion injection changes
only pseudo-observation content, and the two never accidentally receive both
benefits.

### Task 4 — Implement loving contact and guide reliability

Add `contact_t` as an observation with learned precision. Add stable, noisy,
wrong, and context-switched guide regimes. Test paired equality of contact
streams and the absence of any direct contact-to-precision or contact-to-depth
assignment.

### Task 5 — Run the pilot and freeze

**Create:**

- `projects/emergence-suite/continuous/scripts/run_ifs_bundle_inquiry_pilot.jl`
- `projects/emergence-suite/continuous/results/ifs_bundle_inquiry_pilot/`

Use only seeds `16901:16910`. Diagnose failures, simplify before adding
parameters, and retain an attempt ledger. Once stable, write the chosen config,
criteria, and untouched seed ranges to `summary.json` and commit the freeze
before opening confirmation seeds.

### Task 6 — Run the single frozen confirmation

**Create:**

- `projects/emergence-suite/continuous/src/ConfirmIFSBundleInquiry.jl`
- `projects/emergence-suite/continuous/scripts/run_confirm_ifs_bundle_inquiry.jl`
- `projects/emergence-suite/continuous/results/confirm_ifs_bundle_inquiry/`

The result bundle must contain:

- `summary.json`;
- `status.json` with separate 43A/43B/43C statuses;
- `per_seed.csv`;
- `episode_trace.csv`;
- `free_energy_trace.csv`;
- `budget_audit.csv`;
- `magic-numbers.md`;
- the freeze commit and result commit hashes.

### Task 7 — Record without editing the manuscript

**Create:** `projects/ifs-paper/experiment-43-ifs-bundle-guided-inquiry.md`  
**Modify:** `projects/emergence-suite/continuous/README.md`

State what passed, failed, or remained authored. Distinguish direct simulation
results from theory-grounded clinical implications. Do **not** edit
`draft-v11-theory.md`, `draft-v11-outline.md`, or any manuscript file as part
of this handoff.

## 11. Simplicity rule

Prefer one root, four binary bundle variables, one learned joint table, four
three-level observation branches, one global precision field, and one sampling
policy. Add a mechanism only when a frozen test requires it. In particular:

- do not simulate a full IFS system;
- do not add protector/exile labels to the generative model;
- do not make Self-energy a knob;
- do not make loving contact a safety bonus;
- do not force inquiry to win every condition;
- do not call globally rigid confidence epistemic depth;
- do not infer internalized attention from a learned precision profile.

The ideal result is not that every favored clinical sentence wins. It is that a
small model makes the distinctions unavoidable and exposes exactly where they
stop holding.
