# Simulation Suite v2 specification: the cumulative model ladder

**Status:** Adopted 2026-07-27 (direction approved by Brent; design per external review, GPT-5.6 Pro). First milestone in execution: V2.0–V2.2.
**Implementation home:** `projects/emergence-suite/v2/`
**Predecessors:** Experiment 50 (integration without unification — block-diagonal, 0/3 sealed composition) and Experiment 51 (archived on `codex/experiment-51`; stopped at Stage A architecture failure with custody intact; its private materials stay unopened, bound to their contract).

## 1. Why a ladder

Experiment 50 proved ten mechanisms can share a parameterization and remain block-diagonal. Experiment 51 tried to declare the whole architecture up front and hit its wall before freezing anything. The correction: **build a small set of probabilistic primitives, prove each primitive, prove each new composition, and only then enact the next step of therapy.** The final whole-therapy simulation (V2.8) is a protocol over mechanisms that already earned their semantics — not another bespoke program.

## 2. Kernel principles (binding at every stage)

- **One generative model.** A finite-state dynamic generative model p(H, θ, s₁:T, π₁:T, o₁:T) with exact inference as the reference implementation. sₜ holds identity, context, cue-meaning, local/global precision, partner, protector, and access states as stages introduce them; θ holds learned likelihoods/transitions/associations; H indexes candidate structures; πₜ is (joint) policy; oₜ includes environmental, bodily, relational, and imaginal observations through **one likelihood interface**.
- **One-posterior rule.** Every scientific quantity is (1) a posterior over a latent, (2) a posterior over a parameter, (3) model evidence for a candidate structure, or (4) a pure readout computed from those. No second mutable layer; "root probability," "permission," "depth," and "trust" are never written after inference.
- **Exact first.** State spaces sized for exact filtering/variable elimination: binary–ternary identity and cues, 2–4 contexts, small discrete precision support, ≤3 protectors, ≤27 joint policies. Approximate inference is a later benchmarked layer, never the first source of complexity.
- **Factor templates, not psychological edge names.** Reusable primitives are ordinary probabilistic operations (conditional categorical / bounded Gaussian likelihoods, precision-modulated likelihoods, hierarchical precision priors, action-controlled transitions, joint-policy outcome factors, joint-vs-marginal cue observations, learned association factors, finite structural comparison, conjugate learning). A `cue_root` edge compiles to a declared CPT or learnable factor — never "project source into target."
- **Dual implementation.** Python exact reference (the oracle) built first; Julia (or scaled Python) production layer validated against reference **parity vectors**. The publication implementation is whichever is most transparent; credibility lives in the semantics and discipline, not the language.

## 3. The composition ratchet — six gates per stage

1. **Semantic proof.** On a minimal graph, verify analytically or by exact enumeration that the primitive means what it claims (e.g., raising a precision state must sharpen the likelihood that actually enters inference — not a reported field).
2. **Recovery.** Generate from the primitive; recover latents, parameters, and candidate-model identity. Confusion matrices and calibration diagnostics required.
3. **Direct composition.** Combine the new primitive with the mechanisms it immediately depends on. Works-alone-fails-here is unfinished.
4. **Selective lesion.** Remove only the new route: its predicted effect disappears; unrelated earlier results survive.
5. **Cumulative regression.** Rerun every earlier open assay on the new version. Regressions retained and explained, never tuned away.
6. **Sealed stage challenge.** After the stage's public interface is fixed but before development against its target behavior, the evaluator seals one novel configuration/world family (hash committed; revealed after the stage freeze; runs without new code or the failure is the finding).

Stage outputs: an open development result, a frozen cumulative regression profile, one prospective composition test.

## 4. The ladder

Implementation dependency order, not therapy order. **V2.0–V2.2 are normative below; V2.3–V2.8 are the adopted plan, to be elaborated stage-by-stage as their turn comes** (progressive contracts, §6).

### V2.0 — Exact generative kernel (apparatus only; no clinical claim)

Adds: typed latents and factors; dynamic time slices; exact inference; conjugate learning; finite model comparison; trace generation; block-level generic evaluation. Tests: chains/forks/colliders/small temporal graphs against independent enumeration; factor deletion and mutation tests; state and parameter recovery; deterministic paired streams; batch evaluation over a full seed block; a check that no scientific state exists outside posterior/parameter stores. The public contract at this stage covers **only the kernel vocabulary** — nothing therapeutic is declared yet.

### V2.1 — Recursive precision and epistemic depth (C2 foundation)

Adds per channel k: local precision state λₖₜ; observations whose likelihood is genuinely controlled by λₖₜ (Gaussian: variance e^{−λ}; categorical: exponentiate-and-renormalize a base likelihood); a global hyper-state Φₜ as prior over the λ collection; an optional broadcast route (local precision posterior → evidence for Φₜ); a return route (Φₜ → future local precision inference).

Open assays: reliable vs unreliable local confidence; local monitoring with broadcast on/off; conflicting channels (locally confident-miscalibrated vs less-confident-calibrated); the four dominance–depth regimes with no regime labels passed to the agent; a capacity-matched scalar / independent-local alternative.

Derived readouts (pure readouts under the one-posterior rule): **dominance** = causal influence of a part/cue on posterior policy or identity inference (intervention or leave-one-factor-out); **depth** = posterior probability of a globally integrated, calibrated precision regime — never a mean of stored numbers.

Composition proof: the inferred global state must alter the weight of evidence delivered to another latent — the thing Experiment 51's "global precision" never did.

### V2.2 — Identity root, cue meanings, structural transfer (C3 core)

Adds: identity root G; multiple cue meanings Mᵢ; learnable cue–root associations; shared-root / factorized / reversed candidate structures; developmental histories independently varying perceptual similarity and root association.

Open assays: recover the true cue–root structure; treat one cue, probe untreated cues; the 2×2 of perceptual similarity × root association; transfer follows root association, not perceptual similarity.

Composition proof with V2.1 (the seam the milestone rides on): identical corrective information delivered under (a) broad calibrated global precision, (b) locally fluent broadcast-off monitoring, (c) narrowed global precision. Expected: cue-level evidence stays usable locally in all three; root-relevant evidence influences G only when precision pathways admit it; untreated transfer follows posterior revision of G. No transfer coefficient, no direct target update.

Self-like part, first computational face: a locally accurate broadcast-off monitor tested for preserved local reporting, reduced global depth, reduced root uptake, reduced structural transfer.

### V2.3 — Formation and active persistence (C1)

Formation as continuous model comparison — transient disturbance vs persistent coupled identity organization — with overwhelm raising event precision, low inferred controllability flattening policy-consequence evidence, and collapsed broadcast removing the contextual evidence that would locate the event as *now*. No boolean write rule. Assays include acute formation, gradual accumulation, overwhelm-with-control, low-control-without-overwhelm, adaptive persistent threat, and closed-loop avoidance vs exact replay, with the avoidance mediator computed from realized actions. Sealed challenge: a novel developmental schedule (chronic misattunement + one acute event × avoidance available/unavailable).

### V2.4 — Context-indexed redescription

Five candidate families over identical likelihoods (global down-weight, cue-local, context split, continuous drift, change point), replacing transition families rather than toggling edges. Full recovery matrix, false-split rates under drift/change-point, held-out scoring, complexity decomposition, misspecification robustness. Sealed challenge: partial drift plus abrupt contextual transition.

### V2.5 — Evidence format and Bayesian model reduction (unburdening)

One evidence interface: episodic-configural vs cue-level as joint vs marginal observations over the same latents, scored under the same likelihood, matched by delivered predictive log-likelihood; no format bonus. Actual model reduction: full burdened coupling vs reduced coupling (capacities preserved), tracked by sequential predictive evidence, complexity contribution, first stable reduced win, and reversals. The do-over is an imaginal observation through the same interface — it may move evidence, it cannot call reduce. Root revision without reduction and reduction dependent on the changed evidential landscape separate witnessing from unburdening. A null format difference is an acceptable theory revision.

### V2.6 — Partner process, co-regulation, one protector

One latent partner process generates both regulation signals and trust-relevant outcomes; partner-type learning; protector forecasts (outcome tolerance, co-protection, partner policy); stakes in the policy objective; **access as a predicted consequence of policy, not a gate boolean**. The co-regulation 2×2 (regulation × root evidence) with the partner signal entering relational precision only. Protector assays: refusal-uninformative-until-response, remaining vs pressure, trust vs permission at matched posteriors, local vs shared-cause transfer, partner switching/ambiguity. The counterfactual-future battery runs only after the common policy model is stable, with role-absence changing forecasted system risk through inferred co-protection and the sign boundary derived from the full utility comparison.

### V2.7 — Multiple protectors, exiling, registration, polarization

Joint protector-policy posterior; learned outcome tables conditional on the joint policy vector; cross-protector forecasts; exclusion/oscillation/suppression/engagement as ordinary policy alternatives; registration as an observation channel (off = masked, never a withheld increment). **Polarization must arise from shared outcome predictions** — P1's policy changes the outcome distribution P2 predicts and vice versa; the coupling lives in p(yₜ₊₁ | π₁ₜ, π₂ₜ, Gₜ, Cₜ), no polarization coefficient. Assays: befriend both/one/none; escalation perturbations; two vs three protectors; coalitions; a mediator protector; partner support reaching only one protector; exclusion as cheapest reliable joint policy; registration on/off/masked. Composition lesions: cross-protector outcome dependence → polarization only; partner-to-protector evidence → relational descent only; cue-root association → transfer only; global broadcast → depth-mediated access only. Sealed challenge: a novel three-protector topology with a switching partner and a context-dependent mandate.

### V2.8 — The complete therapeutic trajectory

A generated developmental phase (no assigned mature posterior) followed by the twelve-step protocol: activation, co-regulation, refusal, befriending, permission, contact, witnessing, redescription, do-over, reduction, protector check-in, follow-up. Primary outcomes: depth trajectory, trust/joint-policy trajectory, access timing, root revision, untreated transfer, context-model selection, reduced-model evidence, stress-return, role change, relational-prior change. The ten comparator protocols (regulation-only, cue-level exposure, bypass-protectors, instrumental partner, unreliable partner, broadcast-off monitoring, premature do-over, no registration, no context learning, no reduction) are the result: a mechanistic profile of which steps are necessary, sufficient, redundant, or theory-inconsistent. The correct sequence does not need to win every metric. Before the final freeze: publish the complete final contract, then seal three or four entirely new end-to-end challenges before final calibration.

## 5. Parameter and version discipline

Stage-local parameter blocks (likelihood reliabilities, precision transitions, structure priors, policy costs, trust learning), dimensionless where possible, justified by prior-predictive behavior. A stage may add parameters; **changing an inherited parameter increments the strain version and reruns every previous stage.** Earlier passes count as retained only if they survive in the final strain. At every major freeze: joint (not only one-at-a-time) perturbations, parameter recovery, prior sensitivity, stage lesion map, neighborhood sampling, full profile distribution.

## 6. Progressive contracts and prospection

No all-at-once contract. Per stage: (1) define only the new factor/protocol vocabulary; (2) publish public dummy bundles exercising every new field; (3) audit semantic expressibility; (4) evaluator seals one private stage challenge (hash committed); (5) develop against open targets; (6) freeze the stage; (7) run the sealed challenge; (8) preserve the result; (9) extend the contract. Experiment 51's private materials remain archived unopened.

Roles: **evaluator (Fable)** — sealed challenges, seed escrow, freeze verification, adjudication; **implementer (Codex)** — repo integration, both implementations, runs, no commits; **external reviewers (GPT-5.6 Pro, Sol)** — architecture and claim review; **Brent** — theory and claim decisions. Escrow seeds for v2 live at 800000+; development seeds below 800000.

## 7. How this reaches the paper

§9 reports four computational movements, not nine stage histories: formation and persistence (V2.3); epistemic depth and structural transfer (V2.1–V2.2); redescription and reduction (V2.4–V2.5); protection and therapeutic descent (V2.6–V2.8). Figures: cumulative architecture diagram; root/precision transfer result; model-evidence/redescription result; whole-therapy trajectory; lesion matrix.

## 8. First milestone (in execution now)

V2.0 kernel + V2.1 recursive precision + V2.2 root/transfer, Python exact reference, all six gates per stage. Do not add formation, reduction, partners, or protectors until the seam — local precision → global depth → root evidence uptake → structural transfer — holds, including: precision actually controls likelihood weighting; broadcast changes the global posterior without changing the local calculation; cue–root structure is learned; transfer arises through inference; broadcast-off local fluency separates from global depth; and a sealed novel composition challenge runs without new code.
