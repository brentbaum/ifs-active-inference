# Experiment 50 specification: the model-organism strain

**Status:** Draft v2 for review; not yet handed to implementation. v1 (2026-07-25) revised per external review (GPT-5.6 Pro, 2026-07-25); revision log at end.
**Date:** 2026-07-25
**Implementation home:** `projects/emergence-suite/continuous/`
**Paper home:** `projects/ifs-paper/` (`draft-v11-theory.md`; backbone selection agreed 2026-07-25)
**Starting points:** Experiment 49's integrated stack, Experiment 44b's context-split root machinery, the formation model's freeze write, the global-precision-field construction's five-channel regimes.

## 1. What this experiment is for

Every prior result in the suite comes from a construction built for its own test. The criticisms this experiment answers, in ascending order of difficulty:

| Criticism | Answered by |
|---|---|
| "Each assay has separately tuned agent parameters" | One frozen genome (50-H) |
| "The assay-specific world or starting state carries the result" | Frozen provenance: worlds, state histories, analyses (50-H) |
| "Ten mechanisms packaged into one architecture" | Parameter-use, sensitivity, and lesion audits (50-L) |
| "The architecture predicts nothing it wasn't built around" | Sealed prospective challenges (50-P) |
| "The same mechanisms are not necessary across assays" | Lesion clusters (50-L) |
| "This describes people or validates IFS clinically" | No such claim is made, anywhere |

The design runs identical equations and genome values but changes the number and arrangement of parts between assays. That is **one computational strain — one architecture, genome, and configuration grammar — instantiated in prespecified developmental and experimental configurations**, not literally one fixed system. Topology is load-bearing (a reversed graph is assay 4's tested hypothesis), and the claim language throughout uses "strain," never "organism" unqualified.

The work is three linked components, run sequentially with checkpoints:

- **50-H (historical integration):** build the strain, jointly calibrate it, freeze it, run the ten backbone assays on fresh worlds. Claim: compatibility and constraint. Joint calibration is **multi-task training**; 50-H is a fresh-seed regression benchmark, not out-of-sample prediction, and is described as such.
- **50-P (prospective challenges):** without touching the strain, run sealed challenge protocols the strain was never calibrated against. Claim: prospection.
- **50-L (lesions and robustness):** on the unchanged reference strain, run preregistered mechanism lesions and a genome-neighborhood sweep. Claim: compression and causal localization.

The pass count is not the headline. Results are organized by evidentiary class (§6), and a 7/10 profile honestly classed is worth more than ten conformance checks.

## 2. The strain

### 2.1 Architecture

A configuration template over part-slots:

- **Vulnerable bundle(s)** (Experiment 48 form): four-element bundle (self, world, policy, outcome), couplings, relational prior, contact-attempt rate, toggleable registration channel — extended at the root with **Experiment 44b's context-split machinery** (latent c ∈ {then, now}, learnable transition prior, three change-explanation classes competing by variational evidence). Root revision moves only through inference.
- **Protector(s)** (Experiment 47 form): three trust posteriors (outcome forecast, co-protection, partner model), stakes entering only the permission decision, permission as expected-cost choice. Counterfactual futures evaluated in the **risk-model form only** (through the co-protection posterior; no policy-addition variant, no obsolescence penalty constant).
- **Protective repertoire** (Experiment 48 form), with cost and reliability beliefs **learned from developmental history** (see 2.4), not read from world constants.
- **Five-channel precision field** (global-precision-field form) with endogenous forecast errors.
- **Dyad coupling** via one **latent partner process** that generates both regulation signals and trust-relevant outcomes (the Experiment 49 redesign, §5 assay 10) — partner disposition is a latent the protector must infer, not a favorable stream by construction.
- **Freeze process** (formation-model form): one-step high-precision write under overwhelm + low control, with working avoidance available to the policy layer. The write rule is authored; assay 1 is accordingly classed as conformance, not derivation.

The gate is the protector's permission decision; no separate gate object. Melting is model reduction winning a comparison; never a completion rule.

### 2.2 One canonical module

All organism equations live in one module (`ModelOrganism.jl` plus submodules). **No copied adapters:** the Sim-5 dyad path that Experiment 49 duplicated is refactored into the canonical module, and every assay calls the same functions. An equation existing in two places anywhere in the assay-reachable code is a build failure (checked by the identity audit, §4).

### 2.3 The genome and the configuration grammar

- `genome.toml` + `organism-genome.md`: **every** authored constant with one-line rationale. No per-assay constants on the agent side.
- `configuration-grammar.md`, frozen **before calibration**: the complete enumeration of allowed node types, edge types, slots, initializers, interventions, and observation channels. Every assay configuration must be expressible in the grammar; no assay gets a bespoke edge or constructor. The grammar is part of the freeze package.

### 2.4 State provenance

Posterior state is never directly authored. Trust posteriors, root posteriors, coupling strengths, precision profiles, and policy cost/reliability beliefs begin from neutral priors or are produced by **replaying a logged developmental history through the organism's own update equations**. Developmental histories are generator-produced, seeded, and frozen like worlds. Every psychologically meaningful state variable has provenance: what event last changed it, through which update function. An assay that needs a mature protector gets one by growing it, and the growth log ships with the results.

### 2.5 What "one strain" does and does not mean

All assays run identical update equations and genome values. Configurations differ within the frozen grammar; unused mechanisms are idle part-slots, never recompiled out (bit-for-bit idleness check, §4). Worlds and evidence streams are assay-specific by necessity and frozen by hash; the agent is not assay-specific in any respect.

## 3. Protocol

### 3.1 Freeze package

One externally timestamped commit (hash recorded in the freeze manifest) containing, each independently hashed:

1. Organism source and genome
2. Configuration grammar
3. All assay configurations
4. All initial-state generators and developmental-history generators
5. All world generators and their sampling distributions (the frozen definition of the world population every rate refers to)
6. Protocols and intervention definitions
7. **Statistical analysis plans, per assay** (§3.3)
8. Analysis code
9. RNG stream definitions (component-specific streams; paired across arms)
10. Julia version, `Manifest.toml`, execution environment
11. Hashes of the sealed 50-P challenge protocols (contents withheld; §7)
12. Confirmatory seed escrow: seeds held by the evaluator (not the implementer) and released per assay only after that assay's freeze log is committed

### 3.2 Phases

**Phase 0 — joint calibration (training).** Calibrate the genome against the dynamic range of all ten assays, on pilot seeds only. This is multi-task model selection and is labeled as such. The calibration/tuning boundary (§3.4) still applies — it preserves the *within-50-H* meaning of a failure — but no discipline inside Phase 0 makes 50-H out-of-sample; only 50-P is that.

**Strain freeze.** Freeze package committed. After this point the organism, grammar, worlds, histories, protocols, and analysis plans are all immutable.

**Phase 1 — assay execution.** Per assay: pilot block (descriptive only — pilots may no longer move any operationalization; §3.3), then confirmatory block on escrowed seeds. World counts per §8, not a uniform 20.

**Phase 2 — 50-P.** Sealed challenges revealed, protocols run unchanged on the frozen strain (§7).

**Phase 3 — 50-L.** Lesions and neighborhood sweep on the frozen strain (§9).

**Revision rule.** If a **pure software error** is found (wrong file read, numerical bug, demonstrably erroneous normalization), the run is invalidated and repeated; confirmatory status is preserved and the error logged. Any instrument or architecture change made after inspecting confirmatory outcomes produces **50b, an exploratory model revision**: its fresh-seed rerun demonstrates reproducibility of the revised model only. Independent confirmation of 50b belongs to a later sealed battery or Experiment 51. There is no confirmatory 50b and no 50c.

### 3.3 Analysis plans frozen before Phase 0

v1 of this spec said criteria were frozen and also "provisional until assay freeze"; that contradiction is resolved: **everything is frozen before Phase 0 opens.** Per assay, the analysis plan fixes: primary estimand; unit of analysis; aggregation level; treatment of ties and non-crossings; effect-size or equivalence margin; threshold; analysis population; missing-event and numerical-failure handling; primary vs. descriptive outcomes. The boundary between repair and revision: changing file formats, tolerances, or demonstrable bugs is instrument repair; changing aggregation level, absolute↔relative measures, first-passage↔eventual-passage, or endpoint↔mediator is a new hypothesis and cannot enter 50-H.

Every criterion carries a **hypothesis-provenance label**:

| Provenance | Meaning |
|---|---|
| Original prediction | Specified before the source experiment's pilot |
| Pilot-amended | Changed before the source confirmatory run (e.g., Sim 3's two-way ordering criterion) |
| Exploratory finding | Discovered after a source freeze (e.g., Experiment 47's risk-model obsolescence result) |
| 50 prospective | Frozen before any Experiment 50 run |

Exploratory-provenance criteria (notably the risk-model obsolescence crossover) receive their **first prospective test** here and are reported as such, never as inherited frozen results.

### 3.4 The calibration/tuning boundary

Calibration fixes whether an assay can discriminate; tuning fixes what it concludes. Within Phase 0:

- **Dynamic-range quantities only.** Calibration decisions may consult ceilings/floors, control saturation, and contrast variance — never a criterion statistic. The calibration ledger records the quantity consulted for every change; a criterion statistic in that column invalidates the freeze.
- **Defects stated apparatus-first.** An instrument failure must be statable without reference to the hypothesis.
- **The asymmetry rule.** A repair may make the strain more able to fail an assay, never less. The fingerprint of honest repair is retained post-repair failures.
- **Acknowledged limit:** dynamic range correlates with outcomes (evidence scales move arm separation; temperature moves descent rates). This is why Phase 0 is called training and why prospection lives only in 50-P.

### 3.5 Register guards

As in the 44–49 round: *organization* = bundle + couplings + precisions + field profile, fixed in advance; *carrier* = independently parameterized substrate; *witnessing* for exile contact, *befriending* for protector contact; *configural* statistical only; *relational* interpersonal only. No renaming after results.

### 3.6 Record

`results/model_organism/`: genome, grammar, freeze manifest, calibration ledger, per-assay subdirectories (per_seed.csv, summary.json, analysis-plan.md, report.md), `profile.md` (results by evidentiary class), and the 50-P and 50-L reports.

## 4. Assay 0 — strain audits (gating, not pass/fail)

- **Identity:** every assay script loads the same module and genome hash; duplicate-equation check (no copied adapters anywhere assay-reachable); runner refuses on mismatch.
- **Machinery audit (Experiment 46 style):** every update equation, its inputs, classified organization/carrier/neither, with file references — certifying the strain's change transitions are organization-only.
- **Idleness:** instantiating an unused mechanism's slot at zero configuration reproduces each assay trajectory bit-for-bit.
- **State provenance:** automated check that no assay initializes a posterior except via neutral prior or replayed history.
- **Parameter-use matrix:** for every genome constant, which assays read it. Constants read by one assay are flagged assay-local (they weaken the compression claim and are reported, not hidden).
- **Compression statistic:** load-bearing constants in the strain vs. the summed count across the source constructions, and the proportion read by ≥ 2 assay families.

## 5. The ten assays (50-H)

Each entry: evidentiary class; configuration; design; primary estimand. All numeric thresholds live in the frozen per-assay analysis plans, inherited from source-experiment frozen values wherever the measure carries over, with provenance labels; none are restated as "provisional" anywhere.

### C1 — what freezes

**Assay 1 — Freeze formation.** *Class: conformance.* One bundle, no protector. Overwhelm × control grid. The write rule is authored, so this assay verifies the installed mechanism operates at its specified joint boundary (write under overwhelm + low control; not under matched controls; attenuation at the no-control edge) — a property test plus grid, reported as conformance. Deriving the write from generic latent-cause dynamics is extension E6, not backbone.

**Assay 2 — Frozen persistence.** *Class: causal contrast.* Closed action–evidence loop vs. matched open-loop replay, corrective evidence delivered through the organism's ordinary update path (no test-time accessibility gate). Primary: paired exposure and revision effects and the controllability dose-response, with the working-avoidance mediation reported as effect sizes, not only threshold counts.

### C2 — regimes

**Assay 3 — Dominance–depth dissociation.** *Class: conformance + model comparison.* One bundle; the four regimes of the two-axis table induced by input statistics. Added per review: a **one-dimensional comparator** (single arousal/global-confidence scalar), capacity-matched, scored on held-out behavior — realizing four configured regimes does not itself show two dimensions are needed; beating the 1-D model on held-out data does.

### C3 — what revises

**Assay 4 — Identity-first revision and the generalization gradient.** *Class: model discrimination and transfer.* Shared root, multiple cue-bound meanings; witnessing vs. matched exposure vs. reversed graph. **Primary: untreated-cue transfer conditional on root revision.** Ordering (identity-before-threat) is secondary — graph direction constrains it strongly, and the reversed-graph arm is the control that carries the causal weight.

**Assay 5 — Co-regulation and access.** *Class: conformance (interaction estimand upgraded per review).* **2×2 design:** regulation present/absent × root-relevant witnessing evidence present/absent. Primary: the interaction — regulation increases uptake of matched evidence. Root change under regulation-only is tested against an equivalence margin, not a bare 0/20 (a zero can be architectural; the margin plus the evidence-present cell make it informative).

**Assay 6 — Redescription discovered.** *Class: model discrimination.* The 44b protocol (structured worlds, selectivity control, held-out margin at matched complexity, complexity audit against the genome) **plus a model-recovery confusion matrix:** worlds generated from each of global down-weight, cue-local, context-split, continuous drift, and change-point generative families; the scorer must recover the generating family on the diagonal and, critically, must not select context-split under the misspecified families it was not built from.

**Assay 7 — Do-over timing.** *Class: conformance (analytic core) + simulation.* The sign of the imaginal evidence follows the root posterior analytically (crossover at q(g) = 0.5 in the current implementation); present that as a derivation, not a simulated discovery. Simulation tests what is genuinely stochastic: timing under limited evidence budgets, premature-application reversal rates, and a **suggestion-only comparator** whose packets help regardless of readiness — the do-over must beat it only post-revision.

### G — the protective system

**Assay 8 — Derived exiling and the two regimes.** *Class: conformance (selection) + causal (registration).* Policy costs and reliabilities are **learned from developmental history** (per §2.4), then selection is tested in held-out worlds — this replaces the near-analytic authored-cost argmin of Experiment 48. Selection-tracks-learned-costs is reported as a property result; the registration toggle (starvation: static prior; confirmation: strengthening; ablation removes it) is the causal endpoint, kept separate.

**Assay 9 — Protector trust battery.** *Class: split per review.* **Analytic invariants** (stakes-permission separation, transfer locality — consequences of where variables enter the equations) are proven and property-tested, not simulated as discoveries. **Learned-history tests** run as simulations with ambiguous, unreliable, and conflicting partner histories: the protector must recover the latent partner type and competence variables from noisy interaction before permission is evaluated. The risk-model obsolescence crossover — provenance: exploratory finding — receives its preregistered prospective test here: competence-dependent sign of the obsolescence shift, frozen before any run.

**Assay 10 — Dyad-gate descent.** *Class: causal contrast (redesigned per review).* One **latent partner process** with disposition ∈ {trustworthy, neutral, adverse} generates *both* the regulation signals and the trust-relevant outcome evidence — evidence favorability is no longer independent of the dyad by construction. Factorial: partner disposition × scaffold {coupled, decoupled}, plus a positive-evidence-without-scaffolding cell. Primary: the interaction — coupled scaffolding with a trustworthy partner produces descent; decoupled with the same partner does not; coupling an adverse partner does not (scaffolding is not a bypass); positive evidence without scaffolding identifies what the scaffold adds. Permission-before-root-revision is demoted to an **audit** (given the gate definition it is architectural); the headline is the interaction, and the deadlock replication (neutral/no-scaffold) is retained as the historical anchor.

## 6. Evidentiary classes and the profile

| Class | Assays |
|---|---|
| Architecture/conformance | 1, 3 (regimes), 5, 7 (analytic core), 8 (selection), 9 (invariants) |
| Causal or mechanism contrast | 2, 8 (registration), 10 |
| Model discrimination and transfer | 4, 6, 3 (1-D comparison) |
| Prospective compositional challenge | 50-P (E3, E4, E5) |

`profile.md` and the paper report by class: *"the frozen strain passed both model-discrimination assays, k of the causal-contrast assays, and m of the conformance checks,"* with effect sizes and intervals. A bare k/10 appears nowhere as a headline.

## 7. 50-P — sealed prospective challenges

Mandatory: **E3 Polarization** (two protectors with opposed mandates over one exile — a configuration expressible in the grammar but used nowhere in calibration) and **E4 Evidence format** (episodic-configural vs. cue-level corrective evidence against an episodically written bundle — a manuscript claim with no simulation history at all). Preferred: **E5 Self-like part** (local monitoring without recursive broadcast).

Sealing protocol: the challenge protocols and criteria are authored by the evaluator (Fable), **not shown to the implementer (Codex)**, and stored outside the repo until strain freeze; their SHA-256 hashes enter the freeze manifest. After freeze, the protocols are revealed verbatim (hash-checked) and run unchanged. The implementation team receives only the public organism interface. If a sealed protocol cannot run without organism changes, that is a reported prospection failure, not a licensed revision.

## 8. Statistical design

- **Analytic/deterministic properties:** proofs plus property-based tests over a broad frozen parameter domain. Twenty seeds do not impersonate replication of a theorem.
- **Stochastic success rates:** world counts chosen from the target interval width — 60–100 worlds where the estimand is a rate (assays 4, 6, 9 learned-history, 10), not a uniform 20. (16/20 has a 95% interval of roughly 0.56–0.94 and only ~63% power at a true rate of 0.80; that was acceptable for single constructions and is not acceptable for the flagship.)
- **Paired contrasts:** same world and component-specific RNG streams across arms, always.
- **Reporting:** effect sizes, intervals, and Monte Carlo uncertainty everywhere; thresholds are decision rules layered on estimates, not replacements for them.
- **Population:** every rate refers to the frozen world-generator distribution in the manifest, named per assay.
- **Robustness grids (50-L adjunct):** where a signature's survival region is the real question (assays 2, 5, 10), a frozen factorial over prior strength, observation reliability, evidence budget, stakes, and world adversity replaces additional random worlds.

## 9. 50-L — lesions and robustness

On the unchanged reference strain, preregistered before 50-P results are inspected:

**Mechanism lesions** (each with its predicted signature cluster written down in advance): context split unavailable; five-channel field → scalar field; registration removed; partner model collapsed; dyad-to-protector coupling severed; freeze write → ordinary learning; trust posteriors collapsed to a single outcome forecast. A convincing shared mechanism removes its predicted cluster and spares unrelated signatures; a block-diagonal architecture fails this visibly.

**Sensitivity matrix:** small perturbations of each genome constant → change in every primary assay metric. Publishes the cross-assay tensions §1 promises (which constants serve several phenomena; which are effectively assay-local).

**Neighborhood sweep:** a preregistered low-dimensional neighborhood of the genome (the constants the sensitivity matrix identifies as shared, jointly sampled), measuring the volume over which each signature survives — is the reference genome central, or a narrow lucky point?

## 10. Outside the strain, unchanged

- **Experiment 46** (wager violation) stands; assay 0's machinery audit extends its certification to the strain. Not rerun.
- **Experiment 45** (formation triad) stands as the §10 distinguishability result. Not rerun.

## 11. Interpretation discipline and the permitted claim

Every verdict is a construction result about one authored strain. A failed assay licenses "this behavior did not survive the shared parameterization," never "the claim is false." Nothing here is clinical evidence; nothing identifies loving contact, legacy burdens, or the parts taxonomy.

The claim the full protocol licenses, if it succeeds: *a single frozen model-organism strain preserved k historical signatures (by evidentiary class), generalized to m prospectively sealed compositional challenges, and lost predicted clusters of signatures under preregistered mechanism lesions across a nontrivial neighborhood of parameter values.* That establishes compatibility, constraint, compression, prospection, and causal localization — and it is the sentence §9 of the paper would earn.

50-H alone licenses only the weaker, still-useful form: *one strain, jointly calibrated on the historical battery, reproduced k signatures on fresh worlds under frozen analysis plans.*

## 12. What would make this round a success

Not a pass count. Success is: the strain freezes without per-assay exceptions; the profile is honest by class; failures localize (the report says *which* joint-regime tension broke what); at least one sealed challenge runs to a verdict either way; and the lesion battery returns interpretable clusters. An 0/2 on sealed challenges with clean 50-H and 50-L results is a publishable finding about retrospective assembly — and the spec commits to publishing it.

---

### Revision log (v1 → v2)

Per external review (GPT-5.6 Pro, 2026-07-25): reframed organism → strain with frozen configuration grammar; extended the freeze package from genome-only to worlds, state provenance, protocols, analyses, environment, and seed escrow; required state provenance by replayed developmental history (no authored posteriors); required one canonical module (no copied adapters); relabeled Phase 0 as training and split the design into 50-H/50-P/50-L with E3/E4 as sealed mandatory holdouts; resolved the frozen-vs-provisional criteria contradiction (all analysis plans frozen before Phase 0); added hypothesis-provenance labels; tightened the 50b rule (exploratory unless pure software error); replaced k/10 with evidentiary classes; added parameter-use, sensitivity, compression, and lesion audits; upgraded statistics (world counts by estimand type, paired streams, intervals, population definitions, robustness grids); redesigned assay 10 as a factorial latent-partner experiment and demoted the ordering criterion to an audit; upgraded assays 5 (2×2 interaction), 6 (misspecification confusion matrix), 7 (analytic core + suggestion-only comparator), 8 (learned costs), 9 (invariants split from learned-history tests; risk-model crossover preregistered prospectively); reclassified assay 1 as conformance.
