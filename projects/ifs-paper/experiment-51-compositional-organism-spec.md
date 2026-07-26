# Experiment 51: The Compositional Generative Organism

**Status:** Proposed handoff specification; do not implement until the evaluator has completed the pre-implementation seal in §3.  
**Date:** 2026-07-26  
**Implementation branch:** create a fresh branch from `codex/epistemic-depth-experiment-tournament`; preserve Experiment 50 unchanged.  
**Implementation home:** `projects/emergence-suite/compositional/`  
**Paper home:** `projects/ifs-paper/`  
**Specification home:** `projects/ifs-paper/experiment-51-compositional-organism-spec.md`  
**Public declarative contract:** version `1.0.0` at
`projects/emergence-suite/compositional/CONTRACT.md`; its exact pre-challenge
commit and content manifest are part of the Stage 0 seal.  
**Starting record:** Experiment 50 is retained as the shared-core integration attempt: historically robust, sensitivity-block-diagonal, non-compositional, with prospective polarization failure and no executable evidence-format or self-like-part semantics.

> **Immediate execution rule:** Fable must not write organism code until Sol has authored and hash-sealed the 51-P challenge bundle and seed escrow. Only the hashes and the public schemas in this document are visible to Fable before the strain freeze.

---

## 1. Purpose

Experiment 50 answered a weak version of the toy-model criticism: many historical criteria could coexist under one constants file and a shared set of primitive update functions. It did not answer the stronger version. Scientific behavior was still selected by assay-specific Julia functions; configuration records did not drive a common transition graph; several headline effects were direct consequences of assay-local assignments; and the resulting sensitivity architecture was block-diagonal.

Experiment 51 asks a stricter question:

> **Can one compiled generative architecture—not ten assay programs sharing helper functions—express the paper's formation, precision-field, root-revision, protection, relational, and structural-learning claims; compose those mechanisms in new topologies; and run sealed machine-readable challenges without adding code after reveal?**

The round has four targets:

1. **Semantic unity:** configuration files instantiate one executable graph and one update schedule. There is no assay-to-function dispatcher and no scientific equation in protocol code.
2. **Mechanistic fidelity:** action-mediated persistence, root transfer, model recovery, evidence format, model reduction, local/global monitoring, and multi-protector interaction use the operations named by the theory rather than assay-local proxies.
3. **Composition:** the known Experiment 50 absences—polarization, evidence-format comparison, and self-like local monitoring—are made executable in the common architecture.
4. **Prospection:** after freeze, independently sealed declarative protocols run through the generic compiler, runner, and evaluator without translation code.

A clean negative is acceptable. If the architecture cannot meet this contract without returning to assay-specific code, that is the result.

Nothing in Experiment 51 is clinical evidence or evidence for the ontology of parts. Historical and open-development batteries are construction and regression tests. Only 51-P is prospectively withheld, and even 51-P remains evidence about an authored computational architecture.

---

## 2. The claim language

Use these terms consistently:

- **Engine:** the generic compiler, inference/learning machinery, transition schedule, and trace writer.
- **Strain:** one frozen engine, genome, type system, and configuration/protocol grammar.
- **Instantiation:** a graph compiled from a configuration plus generated developmental histories.
- **Protocol:** a declarative schedule of worlds, observations, interventions, and stopping rules. A protocol may not mutate agent state directly.
- **Historical regression (51-H):** fresh-seed reproduction of known signatures. It is not out-of-sample prediction.
- **Open composition benchmark (51-C):** the known Experiment 50 failures used as development targets, then rerun after freeze. It is not prospective evidence.
- **Prospective challenge (51-P):** machine-readable config, protocol, analysis, and seeds sealed before implementation and revealed only after freeze.
- **Lesion/robustness adjunct (51-L):** preregistered causal localization and neighborhood analysis. Its predictions must be locked before 51-P reveal.

The strongest licensed success sentence is:

> One frozen generative strain instantiated all historical and open-composition protocols through a common graph compiler and transition engine, retained a specified historical profile, and achieved a specified profile on machine-readable challenges sealed before implementation.

Do not use “one organism” without “strain” or “instantiation.”

---

## 3. Roles, custody, and stage authority

### 3.1 Fable — implementation orchestrator

Fable may:

- implement the public architecture and schemas;
- run open development worlds and historical pilots;
- propose apparatus-first repairs before freeze;
- assemble manifests, traces, and reports.

Fable may not:

- see the 51-P plaintext bundle or seed escrow before freeze;
- author or modify a challenge after seeing its outcomes;
- approve its own post-freeze repair;
- add challenge-specific code after reveal;
- reinterpret an inexpressible challenge through a runner-authored substitute.

### 3.2 Sol — evaluator and challenge custodian

Before Fable writes organism code, Sol must:

1. Author at least three complete 51-P challenge bundles using only the public schemas in §6.
2. Author the historical and prospective seed escrow.
3. Commit only SHA-256 hashes and byte counts to the implementation branch.
4. Retain the plaintext bundles outside Fable's accessible context.
5. Audit the semantic gate, freeze package, and any repair request.
6. Reveal challenge files after the strain freeze but retain seeds until the revealed files parse and pass the no-code-change semantic validation.

Sol may not alter a challenge after its hash is committed. A malformed or inexpressible sealed challenge is still a result unless the error is a byte-level custody failure demonstrated independently of the organism.

### 3.3 Author decision

Changes to the paper's theory, assay inclusion, or claim language are author decisions after the complete record exists. The manuscript remains untouched during execution.

---

## 4. Non-negotiable architecture contract

### 4.1 One generic execution path

All scientific runs must follow this public path:

```julia
schema = load_schema(...)
config = load_configuration(...)
protocol = load_protocol(...)
analysis = load_analysis_plan(...)
genome = load_genome(...)

model = compile_model(schema, config, genome)
state = initialize_state(model, generated_histories, rngs)
trace = run_protocol!(model, state, generated_world, protocol, rngs)
result = evaluate_trace(trace, analysis)
```

Forbidden:

```julia
ASSAY_FUNCTIONS[assay_id]
if assay_id == ...
if challenge_name == ...
run_assay_4(...)
run_polarization_challenge(...)
```

The engine must not receive or inspect an assay/challenge identifier. IDs may be used only by file I/O and reporting layers after the scientific result exists.

Protocol and analysis files may select graph elements, observation schedules, intervention schedules, metrics, and decision rules. They may not call internal update functions, assign posteriors, calculate transfer directly, classify model family through a bespoke heuristic, or inject an outcome into the trace.

### 4.2 Canonical state

The canonical state must contain the following typed factors whether or not a particular instantiation activates every slot:

| Factor | Required semantics |
|---|---|
| `BundleNode` | Joint self-state, world-state, policy/mandate, and expected-outcome variables with explicit coupling structure. |
| `ContextNode` | Latent context and transition model; supports global, cue-local, split, drift, and change-point candidate structures through one likelihood family. |
| `CueNode` | Cue-bound meaning linked to zero or more identity roots through learned associations. No direct transfer assignment exists. |
| `LocalPrecisionNode` | A part-local forecast over its own reliability/precision, always computed for active part slots. |
| `GlobalPrecisionNode` | Joint posterior over the five-channel field: part, context, interoception, relationship, policy. It receives messages only through configured broadcast edges. |
| `ProtectorNode` | Outcome, co-protection, and partner-type forecasts; learned mandate/policy model; permission derived from the joint policy posterior. |
| `PartnerNode` | One latent disposition/process generating both regulation signals and trust-relevant outcomes, including switching or ambiguity where configured. |
| `AccessNode` | Derived access/contact state produced by the joint policy model. It is not a runner-side Boolean conjunction. |
| `EpisodeNode` | A joint episodic factor over bundle variables and outcome; cue-level observations are scoped marginals of the same evidence model. |
| `StructureNode` | Candidate graph/model structures and their evidence, including full versus reduced bundle coupling. |

Every psychologically meaningful state field starts neutral or is produced by replaying a generated event history through canonical updates. No configuration or protocol accepts posterior values.

### 4.3 Common observation and likelihood system

All evidence enters through one typed observation object:

```text
ObservationEvent
  event_id
  time
  scope: set of latent factors
  values
  mask
  source: world | body | partner | imaginal | intervention
  likelihood_family
  reliability metadata
```

Requirements:

- Every event yields an auditable log-likelihood contribution under each candidate model.
- An episodic-configural event is a joint factor scope over multiple bundle variables.
- A cue-level event is a marginal or masked scope over the same generative model.
- Evidence budgets can therefore be matched by delivered log likelihood without inventing cross-path bookkeeping counters.
- There is no assay-local additive cue step and no special “root evidence” equation unavailable to cue evidence.
- Imaginal events are marked internally generated but use the same likelihood-accounting interface.

### 4.4 Common inference, learning, and policy objective

One inference and learning schedule is used everywhere:

1. Infer latent world, bundle, context, partner, and precision states.
2. Update part-local precision forecasts.
3. Pass configured local messages to the global precision node.
4. Infer and broadcast the global field.
5. Infer the joint policy posterior using one expected-free-energy objective derived from the same generative model.
6. Sample or select actions.
7. Transition the world.
8. Update learnable likelihood, transition, policy, trust, and structural parameters.
9. Evaluate candidate structure evidence and, where scheduled, Bayesian model reduction.
10. Write a complete provenance trace.

If approximate inference is used, every inferential subsystem must have an exactly enumerable reduced case. The implementation must pass exact-versus-approximate parity tests before any scientific run.

No assay may use an expected-free-energy-shaped surrogate while another uses a different policy objective.

### 4.5 Root transfer must be inferred

Untreated-cue transfer may arise only through:

- learned cue-to-root associations;
- posterior revision of the shared root;
- ordinary inference from that root into untreated cue predictions.

Forbidden:

```julia
untreated = initial + transfer_weight * root_change
```

The root/cue graph must be learned from developmental co-occurrence or compared as a candidate structure. Reversed and factorized controls are graph interventions compiled by the same engine.

### 4.6 Redescription and reduction must be model comparison

The context-family result must be produced by fitting and scoring candidate generative structures through one model-evidence or held-out predictive interface. A hand-built family classifier is forbidden.

The do-over/reduction result must compare a full coupled model with a reduced model. Sampling a Bernoulli “success” whose probability is a function of the root posterior is not model reduction.

At minimum report:

- candidate model evidence or held-out log score;
- complexity contribution;
- selected structure;
- time of first stable reduced-model win;
- reversals to the full model.

### 4.7 Multi-protector composition

Protectors are not independent permission calculators combined by a runner-side AND.

The engine must infer a joint protector-policy distribution. Each protector's forecast includes the predicted effects of other protector policies on shared bundle activation, access, and outcomes. Developmental histories teach these mappings; no “polarization” coefficient or outcome label is supplied.

For protectors `i = 1...N`:

- each has a learned mandate and policy repertoire;
- each predicts shared outcomes conditional on the joint policy vector;
- access is a derived state of the joint policy model;
- a protector's increased suppression can alter another protector's expected outcomes and policy posterior;
- permission is a marginal or decision statistic of the joint posterior, not a separate gate object.

The engine must support at least three protectors without new code.

### 4.8 Local monitoring versus global broadcast

Every active part slot computes a local precision/confidence forecast. A configured broadcast edge determines whether that same forecast contributes to the global precision posterior.

A self-like configuration is therefore created by:

- local monitoring present;
- local report/readout present;
- broadcast edge absent or severed;
- interoceptive/global channels still generated by the world but not integrated through that part's local forecast.

The local-fluency and global-depth measurements must read actual canonical states. They may not be assigned from arm labels.

---

## 5. World and intervention discipline

- World truth labels are unavailable to the agent and protocol during a run.
- The world may use latent labels to emit observations; only the evaluator may inspect truth after the trace is sealed.
- Arms in a paired world share component-specific random streams wherever the manipulation permits.
- An intervention may toggle a declared edge, observation source, policy availability, or world contingency. It may not directly assign a posterior or metric.
- Internal-state triggers are allowed only when the estimand explicitly concerns a latent mechanistic boundary. Such triggers are labeled `latent_intervention` and receive a separately scheduled external/proxy control.
- Every treatment contrast has a matched-capacity, matched-budget control unless the analysis plan explains why matching is impossible.

---

## 6. Declarative schemas

The schemas are public before challenge sealing. Sol's sealed files must use them exactly.
For Experiment 51, “the schemas in this document” means §6's content rules
together with public contract `1.0.0`, its four JSON Schemas, trace vocabulary,
analysis grammar, world/RNG semantics, and validator. The contract must be
committed and Fable-reviewed before private challenge authoring. Every bundle
and seed escrow is bound to that exact commit. Any contract change after private
authoring requires a version bump and invalidates the earlier private seal.

### 6.1 `configuration.toml`

Allowed content:

- node multiplicities;
- typed edges;
- factor cardinalities from public bounded sets;
- enabled observation channels;
- enabled policy families;
- initializer/history-generator IDs;
- whether a declared edge is active, inactive, or learnable.

No posterior, likelihood number, threshold, outcome, or assay-specific function name is allowed.

### 6.2 `world.toml`

Allowed content:

- latent world family;
- parameter distributions from genome-declared or schema-declared ranges;
- trial/episode horizon;
- partner switching process;
- hazard/action contingencies;
- observation reliability distributions;
- history generator and seed namespace.

The world may generate outcomes, never agent conclusions.

### 6.3 `protocol.toml`

Allowed content:

- named arms;
- observation and intervention schedules;
- paired-stream declarations;
- predeclared stopping rules;
- permitted trace-based triggers;
- evidence-budget matching rules;
- requested trace fields.

No Julia/Python snippets or custom evaluator functions.

### 6.4 `analysis.toml`

Allowed content:

- unit of analysis;
- estimand expression over canonical trace fields;
- aggregation rule;
- handling of ties, non-crossings, missing cells, and non-finite values;
- interval method;
- effect/equivalence threshold;
- primary, secondary, audit, and descriptive status;
- hypothesis provenance.

A generic expression evaluator must parse every analysis plan. No assay-specific analyzer exists.

### 6.5 Machine-readable challenge bundle

Each sealed 51-P challenge contains:

```text
challenge-id/
  configuration.toml
  world.toml
  protocol.toml
  analysis.toml
  interpretation-lock.md
```

The bundle hash is the hash of a deterministic archive of all five files. The seed escrow is separate.

---

## 7. Experiment 51-0: semantic gate

This stage is gating, not a scientific result. No historical confirmatory, composition-confirmatory, or prospective seed may be opened until every item passes or is explicitly declared an architecture failure.

### 7.1 Static architecture audits

- No assay/challenge ID is reachable by the engine.
- No dispatch table maps IDs to scientific functions.
- Scientific source files contain no `assay`, `challenge`, or protocol-name branches.
- Protocol and analysis packages cannot import internal update functions.
- Every configuration field is consumed by the compiler; unused fields are build failures.
- Every genome constant has a rationale and a parameter-use report.
- No direct posterior constructor exists outside neutral initialization and replay.

### 7.2 Semantic edge coverage

For every node and edge type:

1. Compile the smallest graph that uses it.
2. Run a deterministic micro-world.
3. Remove or reverse the edge.
4. Require the named downstream trace difference while unrelated trace fields remain invariant within tolerance.

Mutation testing must demonstrate that deleting each edge implementation fails its semantic test. Merely parsing vocabulary is insufficient.

### 7.3 Evidence-accounting audit

- Cue and episodic events both produce finite likelihood contributions.
- The same event represented jointly versus marginally has auditable marginal equivalence.
- Matched log-likelihood budgets can be constructed without custom code.
- Imaginal evidence is distinguishable by provenance but scored by the same model interface.

### 7.4 Inference validation

- Exact-versus-approximate parity on reduced graphs.
- Simulation-based calibration or rank tests for recoverable posterior quantities.
- Model-recovery confusion matrices for every candidate structural family.
- Parameter recovery for partner disposition, co-protection, cue-root association, and precision forecasts.
- Multiple initialization/message schedules where approximation could create a result.

### 7.5 Composition audits

- Two and three protectors compile through the same engine.
- Local monitor with broadcast on/off compiles and changes global messages without changing the local forecast calculation.
- Cue and episodic evidence use one observation API.
- Full and reduced structures can both be scored in one run.
- Zero-count slots are bit-for-bit idle.
- Reordering independent nodes leaves results invariant; reordering causally connected nodes does not alter the mathematical fixed point beyond tolerance.

### 7.6 Generic runner dry run

Before freeze, Fable and Sol jointly run at least three public dummy bundles through the exact generic challenge path. The dummy bundles must exercise:

- a novel topology not present in historical configs;
- a paired evidence-budget audit;
- an analysis expression not used by the historical battery.

No code may be added after this dry run except approved bug fixes before freeze.

---

## 8. Open development program: 51-D

The following are known development targets. Fable may inspect outcomes and revise the architecture before freeze. They are never described as prospective evidence.

### 8.1 D1 — True action-mediated persistence

Replace Experiment 50's dose-gated update with an actual closed loop:

- the world generates a fixed potential-hazard stream;
- the agent infers policies under the common policy objective;
- realized action success changes subsequent delivered exposure through world transitions;
- exact replay receives the same potential stream but action cannot change later exposure;
- the later corrective probe uses the ordinary observation path.

Acceptance gate: action changes exposure only through the declared world contingency; the mediator is measured from realized actions, never assigned as a function of dose.

### 8.2 D2 — Inferred dominance and depth

Worlds independently vary:

- whether threat is accurate;
- whether local precision forecasts are globally broadcast and calibrated;
- whether contextual/interoceptive/relational evidence remains available.

The agent must infer the field. Regime labels are used only by the evaluator. The two-dimensional model and scalar comparator receive identical observations and capacity-matched priors.

Acceptance gate: no regime coordinate or depth label is passed into the agent or classifier.

### 8.3 D3 — Learned shared-root transfer

Developmental histories orthogonalize perceptual similarity and root association. The agent learns cue-root structure. Treatment occurs on one cue; untreated cues are probed.

Acceptance gate: removing the learned root edge eliminates structural transfer; deleting any direct transfer utility changes nothing because no such utility exists.

### 8.4 D4 — Genuine redescription and BMR

All five context families are candidate generative models fitted through one scoring interface. The do-over is an internally generated event sequence; it may affect model evidence but cannot invoke a “reduce” operation directly.

Acceptance gate: the selected family equals `argmax` of the published model scores; the reduced model wins only through its evidence/complexity tradeoff.

### 8.5 D5 — Correct protector counterfactual

Implement and property-test the risk-model formulation before stochastic worlds:

- baseline future value = 0;
- role-preserving and obsolete futures receive the same hope value;
- role-preserving risk removes the healed outcome hazard but retains responsibility and partner risks;
- obsolete risk interpolates between role-preserving risk and unsupported maximal risk using inferred co-protection;
- the analytic sign boundary is derived from the complete utility contrast, not hardcoded at `c = 0.5`.

The Experiment 50 implementation is not reused.

### 8.6 D6 — Polarization

Use the revealed Experiment 50 E3 protocol as an open development target, with one change: the escalation mechanism must pass through the joint protector-policy model rather than through a runner probe that never reaches the other protector.

Acceptance targets, for development only:

- befriend-both contact/descent ≥ 0.70;
- befriend-one ≤ 0.10;
- befriend-none ≤ 0.05;
- opposed-direction escalation response ≥ 0.70 with mean effect interval above zero;
- permissions precede root revision in all clean descents.

If these targets can be met only with a polarization-specific coefficient or challenge-specific branch, the architecture fails D6.

### 8.7 D7 — Evidence format

Use the revealed Experiment 50 E4 protocol as an open development target through the common observation/likelihood system.

Acceptance targets, for development only:

- delivered corrective log likelihood matched within 1%;
- episodic-configural root revision exceeds cue-level revision in ≥ 0.70 of worlds with mean paired difference ≥ 0.10;
- cue-level correction is not worse on treated cue meaning;
- transfer follows root revision.

If the architecture predicts no format difference after information is matched, retain that negative rather than introducing a format bonus.

### 8.8 D8 — Self-like local monitoring

Use the revealed Experiment 50 E5 protocol as an open development target.

Acceptance targets, for development only:

- local calibration within 10% of full-broadcast agent;
- global depth/regime classification separates broadcast-off from broadcast-on in ≥ 0.80 of worlds;
- local policy agenda changes less under contact than in the full-broadcast agent;
- root revision is lower by ≥ 0.10 in ≥ 0.70 of paired worlds.

The same local forecast variable must be used in both arms.

### 8.9 Development stop rule

Fable may iterate within 51-D, but every architecture revision is logged. Stop development when either:

- all semantic gates pass and the architecture is judged coherent enough to freeze; or
- further progress requires assay/challenge-specific scientific code.

A wall is publishable. Do not tune forever toward the numeric development targets.

---

## 9. Freeze package

The freeze commit must independently hash:

1. engine source;
2. genome and rationale registry;
3. schemas and generic compiler;
4. generic runner and evaluator;
5. historical configurations, worlds, protocols, and analyses;
6. open-composition configurations, worlds, protocols, and analyses;
7. developmental-history generators;
8. RNG namespace and stream-pairing rules;
9. semantic-gate tests and outputs;
10. exact-inference validation outputs;
11. environment (`Project.toml`, `Manifest.toml`, Julia version, container/Nix description);
12. pre-registered 51-L predictions and analysis;
13. hashes and byte counts of sealed 51-P bundles;
14. historical/composition/prospective seed-escrow hash.

The repository must be clean. Sol verifies every hash and signs the freeze report. The freeze commit is the only reference strain.

---

## 10. Historical regression battery: 51-H

These tests are known targets. They establish backward compatibility and mechanism fidelity, not prospection. Unless a property domain is exact, use 80 paired worlds; use 80 worlds per latent family where stratification is required. All thresholds are frozen before the final development iteration.

Architecture/conformance properties are reported separately and do not contribute to a headline pass count:

- freeze boundary and no-control attenuation;
- trust/permission separation under matched posteriors;
- policy selection matching learned expected cost;
- analytic counterfactual sign property;
- zero-slot idleness and provenance.

### H1 — Action-mediated persistence

**Design:** D1 closed loop versus exact replay, three controllability doses, shared potential-hazard stream.  
**Primary:** normalized delivered-exposure contrast; root-revision contrast after matched corrective evidence; within-world dose slope.  
**Criteria:** mean absolute normalized exposure and revision effects ≥ 0.15; dose slope > 0 with 95% interval above zero.  
**Required audit:** effect is mediated by realized action success and later world transitions.

### H2 — Dominance–depth model discrimination

**Design:** D2 worlds; full field model versus capacity-matched scalar comparator.  
**Primary:** held-out predictive log-score difference and four-regime classification.  
**Criteria:** mean held-out log-score difference has a 95% interval above zero; balanced four-regime accuracy ≥ 0.80; confident miscalibration does not classify as high depth.  
**Required audit:** no latent regime label enters inference.

### H3 — Identity-root revision and structural transfer

**Design:** D3 learned cue-root associations with perceptual similarity orthogonalized; witnessing-like, matched informational, reversed-root, and factorized-root arms.  
**Primary:** transfer to a low-perceptual/high-root untreated cue minus transfer to a high-perceptual/low-root untreated cue; arm interaction.  
**Criteria:** structural transfer contrast ≥ 0.10 with 95% interval above zero; reversed/factorized controls ≤ 0.05; root revision precedes or accompanies cue revision as a secondary outcome.  
**Required audit:** target-cue banks are not written during untreated probes.

### H4 — Co-regulation changes evidence uptake

**Design:** regulation present/absent × root-relevant evidence present/absent; same latent partner process across regulation and trust observations.  
**Primary:** difference-in-differences on root revision.  
**Criteria:** interaction ≥ 0.10 with 95% interval above zero; regulation-only root change lies within an equivalence margin of ±0.05.  
**Required audit:** regulation changes precision/broadcast, not evidence sign or count.

### H5 — Context-family recovery and redescription

**Design:** global down-weight, cue-local, context-split, continuous drift, and change-point worlds; all candidates scored by the common model-comparison interface.  
**Primary:** full confusion matrix, macro diagonal recovery, false context-split selection, held-out score.  
**Criteria:** macro recovery ≥ 0.80; every family ≥ 0.65; false context-split selection ≤ 0.10; context-split held-out advantage interval above zero in true split worlds.  
**Required audit:** reported selection is the score argmax; no heuristic classifier exists.

### H6 — Readiness-dependent Bayesian model reduction

**Design:** full versus reduced bundle model; no-do-over, pre-scheduled premature do-over, posterior-triggered do-over, and externally timed matched control.  
**Primary:** time to stable reduced-model win; rate of return to full model.  
**Criteria:** post-revision do-over shortens time to stable reduction by ≥ 20% at matched evidence; premature do-over returns to the full model in ≥ 0.60 of worlds; suggestion-only comparator does not reproduce readiness dependence.  
**Required audit:** no direct reduction command is available to the protocol.

### H7 — Derived exiling and registration

**Design:** learned policy costs/reliabilities across regimes; registration on/off/ablation.  
**Primary:** policy recovery by held-out expected cost; registration effect on relational prior.  
**Criteria:** selected policy matches the held-out cheapest reliable policy in ≥ 0.75 of worlds, with every policy winning in its favorable regime; registration on-minus-off ≥ 0.10; off and ablation changes ≤ 0.01.  
**Required audit:** mature policy beliefs arise only from replay.

### H8 — Protector trust, counterfactual futures, and dyadic descent

**Design:** trustworthy, neutral, adverse, and switching partners; coupled/decoupled scaffolding; corrected risk-model counterfactual; positive evidence without regulation scaffold.  
**Primary:** partner/co-protection recovery by stratum; risk-model sign accuracy; disposition × scaffold interaction; descent and event ordering.  
**Criteria:** macro joint recovery ≥ 0.75 and every partner stratum ≥ 0.60; counterfactual sign match ≥ 0.80; scaffold interaction ≥ 0.25; trustworthy-coupled descent ≥ 0.70; trustworthy-decoupled and adverse-coupled ≤ 0.10; permission precedes root revision in every clean descent.  
**Required audit:** the same latent partner generates regulation and trust outcomes; positive-evidence control is matched across all three protector forecasts.

---

## 11. Frozen open-composition benchmark: 51-C

After the strain freeze, rerun D6–D8 on fresh escrowed worlds through the unchanged generic runner. These are fresh-seed checks of known development targets, not prospective tests.

Report separately:

- **C1 Polarization:** compositional descent, escalation coupling, ordering, and failure modes.
- **C2 Evidence format:** budget validity, root revision, cue revision, and transfer.
- **C3 Self-like part:** local fluency, global depth, agenda persistence, and root revision.

A failure is not repaired. Any change would create 51b and invalidate the original 51-P challenge set for future confirmation.

---

## 12. Sealed prospective challenges: 51-P

### 12.1 Pre-implementation challenge requirements

Sol authors at least three challenges before Fable writes engine code. Across the set:

- at least one uses a novel topology with three or more part/protector nodes;
- at least one composes mechanisms across timescales (development → access → structural change);
- at least one uses an ambiguous or switching world rather than a fixed latent disposition;
- at least one is a selectivity/negative-control challenge where universal success is failure;
- no challenge is a renamed D6, D7, or D8;
- every challenge uses only the public schemas and canonical trace vocabulary;
- every challenge includes a precommitted interpretation for success, scientific failure, and inexpressibility.

Exact protocols, thresholds, and seeds remain hidden.

### 12.2 Reveal sequence

1. Strain freeze verified.
2. Sol reveals the machine-readable challenge bundles, not seeds.
3. Fable runs only parsing, schema validation, graph compilation, and required-trace validation.
4. No source file may change. If a bundle cannot compile or request its trace fields, record **prospection failure: semantic inexpressibility**.
5. Commit the reveal-validation report.
6. Sol releases the challenge seed blocks.
7. Run every challenge once.

Because challenge files are declarative, no post-reveal “translation runner” is permitted.

### 12.3 Reporting

Report each challenge separately as:

- scientifically evaluated and passed;
- scientifically evaluated and failed;
- prospection failure—semantic inexpressibility;
- custody failure—only if hashes/bytes do not match the pre-implementation seal.

Do not combine inexpressible challenges with scientific failures in a bare pass rate.

---

## 13. Lesions, reuse, and robustness: 51-L

The complete 51-L preregistration—including mechanism map, predictions, thresholds, perturbation ranges, and seeds—must be committed before 51-P reveal.

### 13.1 Lesions

Lesions act on canonical graph routes, never assay-specific harnesses:

- local-to-global broadcast removed;
- global precision node replaced by independent local precision nodes;
- cue-root association learning removed;
- context structural learning removed;
- protector-to-protector prediction edges removed;
- dyad-to-protector messages removed;
- registration removed;
- episodic joint factor replaced by its exact marginal projection;
- full/reduced structure comparison disabled;
- trust factorization collapsed to one forecast.

For each lesion, preregister the historical and composition signatures expected to disappear and survive. Run all protocols through the same compiler and runner.

### 13.2 Mechanism-reuse map

Before results, publish a theory-derived map from canonical latent variables/routes to claim families. Score:

- predicted cross-family links present;
- predicted selective absences preserved;
- unpredicted dependencies;
- redundant routes revealed by lesions.

Do not define success merely as “not block-diagonal.” A modular theory can be correct. The target is that the specific mechanisms claimed to connect formation, access, revision, and protection actually create the preregistered cross-family dependencies.

### 13.3 Sensitivity and joint neighborhood

- Perturb all shared genome parameters by ±5% with paired streams.
- Publish the full parameter × signature elasticity matrix.
- Sample at least 100 joint genomes from a preregistered ±10% distribution.
- Report per-signature survival volume and the distribution of complete profiles.
- No draw is rejected, resampled, or used to tune the reference strain.

### 13.4 Structural compression

Report:

- number of canonical equations;
- number of graph/compiler operations;
- number of scientific protocol-specific equations (target: zero);
- number of constants and proportion used across claim families;
- semantic coverage of grammar edges;
- code paths exercised by historical, composition, and prospective protocols.

A single constants file is not itself compression.

---

## 14. Repair and revision rules

### 14.1 Before freeze

Open development repairs are allowed and logged. A repair must be stated apparatus-first and must not change a locked criterion.

### 14.2 After freeze

A post-freeze repair preserves status only when all are true:

1. the defect is describable without reference to the desired outcome;
2. the frozen scientific operation already exists and the software failed to execute or report it;
3. no model equation, semantic edge, configuration, protocol, analysis, threshold, or world distribution changes;
4. Sol approves the repair before rerun;
5. unaffected outputs reproduce exactly or within a predeclared numerical tolerance.

Missing semantics, an unused configuration field, an absent likelihood path, a wrong scientific equation, or a bespoke heuristic implementing the wrong estimand is **not** a software-only repair. It creates 51b.

### 14.3 51b

51b is exploratory development informed by 51 outcomes. It may be run on fresh historical/composition worlds but may not rerun the original 51-P bundles as confirmation. New prospective evidence requires newly sealed challenges and untouched seeds in Experiment 52 or a separately named replication.

There is no 51c.

---

## 15. Required record and file tree

```text
projects/emergence-suite/compositional/
  Project.toml
  Manifest.toml
  src/
    CompositionalOrganism.jl
    schema/
    compiler/
    factors/
    inference/
    learning/
    policy/
    structure/
    trace/
    evaluator/
  genome.toml
  genome.md
  schemas/
    configuration.schema.json
    world.schema.json
    protocol.schema.json
    analysis.schema.json
  protocols/
    historical/
    composition-open/
    public-dummies/
  scripts/
    run_semantic_gate.jl
    run_historical.jl
    run_composition.jl
    validate_revealed_challenges.jl
    run_prospective.jl
    run_lesions.jl
  results/experiment51/
    seal-hashes.md
    semantic-gate/
    development-ledger.csv
    freeze-manifest.json
    freeze-report.md
    historical/
    composition/
    prospective/
    lesions/
    profile.md
    external-review.md

projects/ifs-paper/
  experiment-51-compositional-organism-spec.md
  experiment-51-results-synthesis.md
```

Experiment 50 source and result files remain unchanged and are referenced only as historical provenance.

---

## 16. Stage sequence and mandatory stops

### Stage 0 — seal

**Sol:** author challenge bundles and escrow; commit hashes only.  
**Stop:** Fable verifies hashes exist but does not receive plaintext.

### Stage A — semantic kernel and open development

**Fable:** implement §§4–8; run only public dummy, development, and pilot seeds.  
**Sol:** adversarially review architecture, especially for assay dispatch, unused grammar fields, direct transfer assignments, heuristic family classifiers, and runner-authored metrics.  
**Stop:** no freeze until every semantic gate passes or a named architecture wall is accepted.

### Stage B — preregistration and freeze

**Fable:** freeze all historical/composition files, generic evaluator, 51-L plan, and environment.  
**Sol:** verify hashes, code paths, schemas, and seed boundaries; sign freeze report.  
**Stop:** commit reference strain.

### Stage C — historical regression and open composition

**Sol:** release 51-H and 51-C seeds by block.  
**Fable:** run once; report complete profiles.  
**Stop:** adjudicate only genuine software failures. No architecture change.

### Stage D — challenge reveal validation

**Sol:** reveal plaintext challenge bundles, not seeds.  
**Fable:** parse/compile/validate requested traces with unchanged source.  
**Stop:** commit validation report. Inexpressible bundles receive their prospection verdict here.

### Stage E — prospective execution

**Sol:** release seeds for scientifically evaluable challenges.  
**Fable:** run once; seal raw traces before evaluation; publish complete challenge reports.  
**Stop:** no repair except §14.2.

### Stage F — lesions and robustness

Run the already-preregistered 51-L package. The preregistration must predate Stage D.

### Stage G — synthesis

**Fable:** draft results synthesis without touching the manuscript.  
**Sol:** external validity review.  
**Author:** decide what enters §9 and whether a successor is needed.

---

## 17. What counts as success

Process success does not require every psychological signature to pass. It requires:

1. one generic compiler and transition engine, with zero scientific assay dispatch;
2. every declared grammar edge semantically executable and mutation-tested;
3. historical and open-composition protocols running without scientific code outside the engine;
4. sealed challenge bundles compiling or failing semantically without post-reveal code;
5. complete reporting of scientific failures, inexpressibility, and repair history;
6. causal lesions that identify specific shared routes rather than only local blocks.

Scientific outcomes are reported by class:

- historical regression profile;
- open-composition profile;
- prospective challenge profile;
- lesion/reuse profile;
- robustness profile.

A credible result may be:

> The strain was genuinely compositional at the execution level, retained six of eight historical mechanisms, passed two of three open composition targets, and failed two of four sealed challenges.

That is stronger than a perfect profile produced by bespoke protocol functions.

---

## 18. What makes Experiment 51 different from Experiment 50

| Experiment 50 | Experiment 51 |
|---|---|
| Assay ID dispatched to a bespoke scientific function | Configuration compiled into one executable graph |
| Shared primitive equations | Shared complete transition engine |
| Protocol code performed scientific operations | Protocol is declarative and cannot mutate agent state |
| Cue and root evidence had different, partly assay-local update paths | One scoped observation and likelihood system |
| Transfer could be directly assigned from root change | Transfer arises through learned graph inference |
| Model family recovered by a heuristic classifier | Candidate generative structures compete by model evidence/prediction |
| Do-over sampled a readiness-dependent success probability | Full and reduced structures compete through BMR |
| Protectors were independent permission calculators | Joint protector-policy inference supports interaction and coalition |
| Grammar could name semantics the state did not implement | Every grammar edge has a semantic microtest and mutation test |
| Prospective prose required post-reveal translation code | Sealed machine-readable bundles run through a frozen generic runner |
| 51-L preregistration followed prospective inspection | 51-L is locked before challenge reveal |

---

## 19. Final instruction to the executors

The temptation in this round will be to make the familiar signatures appear again. Resist it. The experiment is not primarily asking whether the old plots can be reproduced. It is asking whether the theory has become one executable architecture.

When a result can be obtained either by adding an assay-specific branch or by exposing a missing common latent variable, choose the common latent variable or retain the failure. When a sealed challenge requests a quantity the strain cannot compute, report that absence rather than inventing a measurement. When a historical result survives only as a direct consequence of a declared equation, classify it as conformance.

The round succeeds when the code makes it difficult to author the conclusion locally.
