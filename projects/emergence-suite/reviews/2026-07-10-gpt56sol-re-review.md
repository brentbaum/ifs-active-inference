# Adversarial re-review of the Phase 4 de-authoring campaign

Date: 2026-07-10  
Reviewer: GPT-5.6-sol  
Scope: committed record through `c2e57a1`, including ancestor `f4bc28c`; the cross-model synthesis was assessed as stated in the task, the `f4bc28c` commit message, and the current T4.11 synthesis note (untracked at review time, so not used as registration evidence)  
Method: code/results review only; no simulation or test execution

## Bottom line

Phase 4 materially improved the record. The old direct aliases, manual state handoffs, authored Sim 4 stack, double depth gate, fake cascade timestamps, and phase-assisted continuous hysteresis are either removed or explicitly dead. Fresh seeds also did useful work: they killed Sim 1's S1.3 rate, Sim 6a robustness, and several broader claims rather than being retuned away.

That is not a clean bill. The campaign introduced a subtler author-the-conclusion pattern: **pilot-shaped mechanism and estimand replacement followed by fresh-seed confirmation**. Fresh seeds protect against seed overfit; they do not protect against building the pilot result into a new probe rule, world contingency table, band definition, aggregation level, or access gate. Sim 1 and Sim 5 still fail the original standard for that reason. Sim 4 now authors a negative result through an exact-access deadlock. Sim 7's state continuity is real, but its strongest surviving correlation is algebraically loaded and two of its three diagnoses are unsupported. The continuous run supports a landscape and falsifies its autonomous transition; it does not positively establish that collapse is closed-loop.

| Area | Verdict | Core reason |
|---|---|---|
| Sim 1 | **STILL-FATAL** | The new capture probe, 128-trial hardening epoch, release bands, and amended criteria were selected from the pilot that killed the prior claim. |
| Sim 5 | **STILL-FATAL** | Labels no longer leak directly, but the world-side settle table encodes the entire learned signature and the 30/70 root-evidence split authors the celebrated null. |
| Sim 6a robustness | **RESIDUAL-CONCERN** | The falsification is honestly scoped, but committed outputs contradict the fixed code and still call the confirmatory run a pilot. |
| Sim 4 | **STILL-FATAL** | The repaired coupling test permits continuous partial access in EFE but permits learning only at access exactly 1.0, creating the deadlock used to diagnose missing concurrency. |
| Sim 7 | **RESIDUAL-CONCERN** | One-state continuity is real; the `r=-0.99` readout is structurally loaded, and the prevalence/probe diagnoses are post-hoc or factually wrong. |
| Continuous T4.8 | **RESIDUAL-CONCERN** | Bistability and autonomous-crossing failure are sound narrow results; the closed-loop synthesis is an untested rescue and the registration chronology is not independently evidenced. |

No reviewed area earns `CLEAN` at the level of the prose claims currently made. Several narrow implementation or numerical claims do.

## 1. Sim 1 — STILL-FATAL

### What is genuinely fixed

The consolidation epoch is **not** a hidden `allow_spawn=false` agent-side gate. The stream is explicitly split into an acute catastrophe-live epoch and a catastrophe-silent ordinary-adversity epoch (`suite/src/sims/sim1/Sim1.jl:340-375`), while every formation trial still calls the same spawn path with `allow_spawn=true` and the unchanged pressure/flatness conjunction (`suite/src/sims/sim1/Sim1.jl:608-632`). Kappa also has a real world-loop route: successful action creates fixed relief windows that suppress later potential hazards only in the closed-loop arm (`suite/src/sims/sim1/Sim1.jl:378-415`). Exact replay therefore gives a legitimate action-to-evidence ablation.

The confirmatory record is also candid about the surviving failure. S1.3 is `0`/falsified, the original A1.5 remains `-115`/falsified, and the replacement A1.5r metrics are reported separately (`suite/runs/sim1/confirmatory/criteria-results.json:42-51`, `suite/runs/sim1/confirmatory/criteria-results.json:138-207`). `status.json` says `theory_result: falsified`, not support (`suite/runs/sim1/confirmatory/status.json:1-8`).

### Fatal defect: capture-not-mass is installed in the probe

The redefined result does not merely *measure* capture. After the prior two-arm claim failed, Step C added per-cause `reflexive_mass` and `total_mass`, then made disconfirming evidence pass through a new D1 gate:

- written reflexivity is the aversive-write-weighted mean (`suite/src/sims/sim1/Sim1.jl:523-540`);
- the probe converts it to depth, exponentially suppresses bundle precision, exponentially amplifies context precision, and returns the context share (`suite/src/sims/sim1/Sim1.jl:542-555`);
- every one of the 96 safe probe updates is multiplied by that share (`suite/src/sims/sim1/Sim1.jl:566-581`).

That is an agent-side test-time accessibility gate introduced after the count-mass contrast ran in the wrong direction. The A1.5r mediator then asks whether the arm that this new rule makes less probe-accessible has the lower probe-accessibility weight (`suite/configs/sim1-criteria.yaml:114-137`). The result is internally consistent, but it is not independent evidence that capture rather than mass caused freezing. It is evidence that a newly installed capture-weighted probe can reverse the mass prediction.

The probe's two scale constants were pilot-swept, while the release bands were selected from the observed pilot transect (`suite/src/sims/sim1/Sim1.jl:76-97`; `suite/src/sims/sim1/magic-numbers.md:105-112`). This is exactly the sort of seam-level authorship the original review attacked.

### The consolidation epoch is world-side, but still outcome-tuned

The distinction matters: it is not a hidden agent gate, but it is a selected intervention. The register says 128 was the first duration that produced a stable, 10/10 frozen kappa profile; zero trials produced revision around 0.33 (`suite/src/sims/sim1/magic-numbers.md:96-104`). It therefore converts a young-spawn failure into a hardened result by giving the new causes exactly the extra ordinary-adversity time needed before probing. Calling the catastrophe channel's silence “not a tuned constant” does not neutralize the tuned epoch length.

The narrow defensible statement is: **under a 72+128 world schedule and the added D1-weighted probe, the configured closed loop produces a fresh-seed arm-by-kappa difference.** The broader “formation claim replicated exactly” is too strong.

### S1.2 and S1.4 are outcome-shaped replacements, not principled confirmations

S1.2 changes the unit of failure from seeds to majority-classified cells after the pilot revealed a stable 20% seed-level corner failure. The new threshold is exactly the pilot value, zero (`suite/configs/sim1-criteria.yaml:18-25`; `suite/src/sims/sim1/magic-numbers.md:113`). Aggregation can now declare the corner absent even though the confirmatory seed-level high/high frozen rate is 0.2167 (`suite/runs/sim1/confirmatory/summary.json:127-137`). “Consistency with region classification” is a coherent reporting convention, but it does not confirm the original individual-level claim.

S1.4 is more plainly a discovered regularity promoted to a criterion. The old omega-extreme claim is declared dead, and the replacement uses the pilot-observed exact kappa edge plus a threshold set below the observed gradient (`suite/configs/sim1-criteria.yaml:34-49`; `suite/src/sims/sim1/magic-numbers.md:108-115`). Fresh seeds show that the implementation's edge is stable. They do not turn that post-output regularity into a prior theoretical prediction.

### Verdict

The action-mediated evidence loop is real, the yoking is useful, the old failures are retained, and S1.3 was honestly lost. But the headline replacement is still authored at the probe and estimand seams. **STILL-FATAL** for the claim that the campaign independently established the formation/capture mechanism; defensible only as a conditional existence result for the final specified architecture.

## 2. Sim 5 — STILL-FATAL

### Direct label leakage is removed

The `condition` string is passed through for rows and aggregation, not consumed by the learned update. World emissions are selected through `emission_model`, sampled into one of four observable joint signals, and then passed to a shared learning path (`suite/src/sims/sim5/Sim5.jl:268-312`, `suite/src/sims/sim5/Sim5.jl:484-520`). The three primary emission tuples are distinct, and fluent-but-threatened is no longer an alias of dysregulated (`suite/src/sims/sim5/magic-numbers.md:12-15`). In that narrow sense, the de-aliasing is real.

The audit metric is nevertheless hard-coded rather than computed: `supplied_condition_labels_used_as_likelihood = 0.0` is written directly into the summary (`suite/src/sims/sim5/Sim5.jl:906-914`). Static inspection supports the zero here, but the criterion itself is not an executable leak detector.

### Fatal defect: the settle table is the signature

The client “learns” a signal-to-settling mapping, but its training labels are sampled directly from the hand-set table `[0.90, 0.60, 0.64, 0.10]` indexed by that same signal (`suite/src/sims/sim5/Sim5.jl:314-334`). The primary conditions were chosen so regulated emits mostly coherent-safe, fluent-threatened emits mostly coherent-threat, and dysregulated emits mostly incoherent-threat (`suite/src/sims/sim5/magic-numbers.md:12-15`). The ordered target is therefore in the world generator before learning begins.

The controls do not test an alternative explanation:

- “unreliable” algebraically mixes each table entry 75% toward 0.5;
- “reversed” returns `1-p` (`suite/src/sims/sim5/Sim5.jl:314-323`);
- the lesion resets counts to the exact uniform prior and blocks later writes (`suite/src/sims/sim5/Sim5.jl:326-339`, `suite/src/sims/sim5/Sim5.jl:507-519`).

It would be surprising if those interventions did **not** shrink, reverse, and erase the learned table. The fresh-seed 18/20, 19/20, and 20/20 results (`suite/runs/sim5/confirmatory/criteria-results.json:6-51`) validate recovery of the supplied contingencies, not emergence of a co-regulation signature from dyadic dynamics. The old monotone agent likelihood has been moved one causal step outward into a world settle table. That is better experimental hygiene, but it still supplies the conclusion the prose claims to discover.

There is a second supplied mapping downstream: the learned settle probability is converted back into depth evidence by mixing a fixed monotone `regulated_coreg_by_depth` vector with its complement (`suite/src/sims/sim5/Sim5.jl:342-353`). Thus both “what this signal causes” and “what settling says about depth” are authored monotone mappings.

### The regulation-only null is mechanically possible both ways, but not earned as necessity

Regulation-only is no longer an architectural zero. Every contact writes a nonzero root increment, and parts-language adds the remainder (`suite/src/sims/sim5/Sim5.jl:431-444`). The 20/20 liveness result is therefore meaningful (`suite/runs/sim5/confirmatory/criteria-results.json:54-63`). Given a larger contact fraction or longer budget, regulation-only could cross BMR; the path is live.

But the experiment fixes contact-only evidence at 30% and parts content at the remaining 70%, explicitly “without forcing it to equal regulation-plus-witnessing” (`suite/src/sims/sim5/magic-numbers.md:24`). The criterion preregisters only nonzero evidence, not statistical power to revise or a two-sided revision outcome (`suite/configs/sim5-criteria-confirmatory.yaml:38-45`). `0/20` is then narrated as “separately necessary, jointly sufficient” even though no evidence-fraction or session-budget boundary is tested. It is an earned **nonzero-but-subthreshold observation at the chosen 30/70 budget**, not an earned necessity theorem.

### Verdict

No direct condition-label leak remains, and the regulation-only path is live. The headline signature is still placed in a world contingency table and recovered by ordinary counting; the celebrated null is placed near a BMR threshold by a hand-set evidence split. **STILL-FATAL** for emergence or causal-necessity claims. Clean only as a demonstration that the client can learn and act on supplied signal/settling contingencies.

## 3. Sim 6a robustness — RESIDUAL-CONCERN

### The falsification is correctly scoped and substantively honest

The robustness generator is genuinely separate from the historical biography schedule. It evolves a reflected latent trajectory, samples availability from an independent RNG, and samples emissions from the chosen generative mapping (`suite/src/sims/sim6a/Sim6a.jl:997-1033`). The agent evaluates theory and null emissions with a fixed response mapping (`suite/src/sims/sim6a/Sim6a.jl:1063-1091`, `suite/src/sims/sim6a/Sim6a.jl:1220-1232`). The four-part signature requires precision loss, inferred-depth loss, capture increase, and recovery (`suite/src/sims/sim6a/Sim6a.jl:1098-1133`).

The confirmatory gate really scales to `ceil(0.8*n)` in the executed code (`suite/src/sims/sim6a/Sim6a.jl:1234-1269`). The fresh results are bad in multiple independent ways: 12/20 decoupled, 5/20 flat-null leakage, 9/20 non-monotone leakage, and only 5/81 jointly surviving cells (`suite/runs/sim6a/confirmatory/summary.json:102-117`). The criteria report does not relabel these as success: the joint result is falsified at 0.0617 and the aggregate status is falsified (`suite/runs/sim6a/confirmatory/criteria-results.json:5-51`; `suite/runs/sim6a/confirmatory/status.json:1-6`).

The README's scope is therefore correct: the Phase 4 run falsifies robustness under decoupling and joint perturbation; it does not logically erase the historical Stage 1 trajectory under its original coupled schedule (`suite/src/sims/sim6a/README.md:156-170`). “Stage 1 stands” must mean only “the old configured trajectory occurred,” not “its mapping is identified” or “its transition generalizes.”

### Residual record defects

The committed confirmatory artifacts were not regenerated after the post-run code fix:

- current code reports a 16/20 per-grid requirement (`suite/src/sims/sim6a/Sim6a.jl:1302-1307`), but committed `summary.json` still reports `8` (`suite/runs/sim6a/confirmatory/summary.json:114-119`);
- current code hard-codes `analysis = "T4.7 robustness pilot"`, `protocol = "pilot-only"`, and pilot-only metadata even for a confirmatory label (`suite/src/sims/sim6a/Sim6a.jl:1315-1324`, `suite/src/sims/sim6a/Sim6a.jl:1345-1358`);
- committed `status.json` consequently calls the confirmatory run `pilot-only` (`suite/runs/sim6a/confirmatory/status.json:1-6`).

These appear to be provenance/label defects rather than evidence that the old 8-seed gate executed—the joint loop itself uses the 0.8 fraction. But a frozen confirmatory record should be internally self-reproducing, not require prose to explain why its outputs disagree with its code.

The held-out estimator also received a post-attempt architecture upgrade: the first attempt used the historical transition, then the final pilot fit both emissions and transitions after seeing `r≈0.50` (`suite/src/sims/sim6a/magic-numbers.md:72-82`). Retaining attempt 1 is honest, and no confirmatory seed was used for the change, so this is not fatal. It does make the held-out `r=0.706` a validation of the revised estimator family, not an untouched original claim.

### Verdict

**RESIDUAL-CONCERN.** The negative robustness conclusion is real and correctly scoped. The residual is record integrity: stale committed artifacts and pilot labels weaken the claimed Step B freeze. The honest substantive conclusion survives those defects.

## 4. Sim 4 — STILL-FATAL

### The old authored stack is gone

Formation now calls Sim 1's actual evidence, policy, spawn, and update path on one persistent agent; Sim 4 wraps only the returned causes (`suite/src/sims/sim4/Sim4.jl:214-307`, `suite/src/sims/sim4/Sim4.jl:329-385`). Relational forecasts are IID symmetric pseudo-counts, and the readout classifier does not enter EFE (`suite/src/sims/sim4/Sim4.jl:208-212`, `suite/src/sims/sim4/Sim4.jl:360-381`). The provenance criterion reports 20/20 causes grown and zero authored (`suite/runs/sim4/pilot/summary.json:260-264`). The original Sim 4 support remains dead.

### Fatal defect: continuous access is followed by an exact-equality learning gate

The repaired pair strength is at least content-derived: blocker's protective policy mass times the fraction of its writes made while the target was the policy-owning active cause (`suite/src/sims/sim4/Sim4.jl:310-326`). Access then varies continuously with that strength and the blocker's trust (`suite/src/sims/sim4/Sim4.jl:394-413`), and partial access changes expected outcome and information gain in EFE (`suite/src/sims/sim4/Sim4.jl:420-442`).

But an actual therapy event—and therefore every trust update—occurs only if `access >= 1.0 - 1e-9` (`suite/src/sims/sim4/Sim4.jl:533-562`). Any nonzero coupling from any unpermitted blocker yields access below one. The selected cause is then logged as `blocked`, no relational or policy count changes, blocker trust cannot rise, and the same cycle can repeat indefinitely. This is exactly what the README reports for five multi-cause seeds: no therapy contact because mutual or reversed gates had no escape (`suite/src/sims/sim4/README.md:58-66`).

That deadlock is not entailed by “single-active-cause formation.” It is imposed by a new all-or-nothing therapy write rule layered on a supposedly continuous access variable. A probabilistic contact, an access-weighted write (as Sim 7 later uses), or even a small graded trust update would leave the coupling live. None was tested. The current pilot therefore cannot distinguish:

1. a grown coupling with no outside-in direction;
2. a useful coupling trapped by an exact-access therapy gate; and
3. genuinely missing concurrent activation.

### The architectural diagnosis overstates what the audit shows

The record says the coupling “cannot form” because Sim 1 has one active cause (`suite/src/sims/sim4/README.md:117-136`). Yet the implementation explicitly records cross-cause writes whenever `log.cause_id` differs from the pre-trial dominant `active_cause_id` (`suite/src/sims/sim4/Sim4.jl:245-302`), and it obtains nonzero pair strengths sufficient for a history shuffle to destroy seed 1003's one successful order (`suite/runs/sim4/pilot/summary.json:192-203`). The mean later-to-earlier blocking share is 0.465, not zero (`suite/runs/sim4/pilot/summary.json:204-259`).

What the pilot establishes is narrower: **this particular policy-owner/write-recipient coupling has no reliable outside-in directional bias and, with an exact-access therapy gate, yields 1/10 complete descent.** Concurrent activation is a plausible next architecture, not a diagnosis identified uniquely by these data.

### Verdict

The original positive descent claim remains dead. The new negative conclusion is also authored by an unfair all-or-nothing operationalization, and the “single active cause” diagnosis is not uniquely supported. **STILL-FATAL** as evidence about whether a de-authored grown coupling can produce descent. The only clean claims are zero authored causes and failure of this exact implementation.

## 5. Sim 7 — RESIDUAL-CONCERN

### The one-state audit trail is real

`LifeState` holds one cause vector, one depth posterior, and one co-regulation count matrix (`suite/src/sims/sim7/Sim7.jl:103-119`). `Sim4.grow_stack` is called once per model/life; the returned arrays are retained (`suite/src/sims/sim7/Sim7.jl:176-201`). Adult, therapy, and held-out events use the same `update_life!`, with held-out learning disabled rather than a separate dynamics branch (`suite/src/sims/sim7/Sim7.jl:227-275`, `suite/src/sims/sim7/Sim7.jl:318-385`). H1/H2 differ by one node index in `GraphDirection` (`suite/src/sims/sim7/Sim7.jl:23-30`, `suite/src/sims/sim7/Sim7.jl:142-153`). The bank identity rate of 1.0 is therefore credible (`suite/runs/sim7/pilot/criteria-results.json:5-27`).

There is no post-melt `[4,34]` replacement and no configured `low_E` assignment. On the original stitching defect, the rebuild passes.

### “Carried, not recomputed” is true for banks and false as an interpretation of `r=-0.99`

The banks are carried. Capture is necessarily recomputed at each event, and its formula directly contains the childhood variable used in the correlation:

- `written_reflexivity * probe_depth_scale` enters two exponentials that set base root/context precision (`suite/src/sims/sim7/Sim7.jl:135-139`);
- adult capture is the resulting root share times danger probability (`suite/src/sims/sim7/Sim7.jl:142-156`);
- the focal cause is selected at initialization by maximizing that same written-reflexivity-dependent capture score (`suite/src/sims/sim7/Sim7.jl:168-193`).

The criterion then correlates the input of that formula with its later output (`suite/src/sims/sim7/Sim7.jl:554-557`). `r=-0.99` is therefore not independent evidence that biography carried childhood reflexivity into adult capture. It is the expected monotonic consequence of retaining childhood reflexivity as a fixed parameter inside every later readout, amplified by selecting the maximally captured cause. “Evolved not recomputed” in the README (`suite/src/sims/sim7/README.md:59-63`) is misleading: state evolved, but capture was recomputed from a formula already containing the predictor.

The bimodality is also thresholded from this loaded score: four lives exceed the hand-set 0.30 capture threshold and six do not (`suite/src/sims/sim7/magic-numbers.md:18-24`; `suite/runs/sim7/pilot/summary.json:107-121`). It is a descriptive property of ten pilot lives, not a confirmed population structure.

### The three diagnoses are not equally sound

1. **Prevalence = world-schedule calibration: unsupported.** The 4/10 result could depend on the adult schedule, but it also depends on Sim 4's pilot-tuned formation schedule, focal-cause selection, D1 scales, and the 0.30 threshold. No calibration or sensitivity result isolates the world schedule (`suite/src/sims/sim7/Sim7.jl:278-300`; `suite/src/sims/sim7/magic-numbers.md:13-24`). Calling it “not mechanism” is an excuse until that decomposition exists.

2. **Probe failure = inherited absolute metric: factually wrong.** The fixed probe already computes relative reduction: `(before-after)/before` (`suite/src/sims/sim7/Sim7.jl:158-165`). The actual problem is that therapy writes enormous new safe mass—write size 18 for up to 96 sessions (`suite/src/sims/sim7/magic-numbers.md:11-19`)—while the counterfactual probe adds a fixed evidence budget. A larger carried bank will move less under any fixed-count probe even when the output is expressed as a relative probability reduction. The README and synthesis misidentify this as Sim 1's superseded *absolute* standard (`suite/src/sims/sim7/README.md:64-70`; `reviews/synthesis-2026-07-10.md:105-107`).

3. **H1/H2 likelihood lacks a direction-discriminating relational target: substantially right.** Held-out likelihood is computed from safe/danger observations using `p_safe = 1-capture` before the event (`suite/src/sims/sim7/Sim7.jl:227-234`), while both models receive the same world schedule (`suite/src/sims/sim7/Sim7.jl:278-295`, `suite/src/sims/sim7/Sim7.jl:541-552`). The reversed result legitimately says this predictive target does not favor H1. “Contact-transfer structure is needed” is a proposal suggested by Sim 3, not yet demonstrated at life scale.

### Therapy melt is real but highly assisted

All four threshold-captured lives reduce capture, and the record correctly refuses the 4/10 prevalence gate (`suite/runs/sim7/pilot/criteria-results.json:30-63`). But therapy supplies up to `18 * access` evidence units per session (`suite/src/sims/sim7/Sim7.jl:353-369`), safe evidence is more accessible as capture falls (`suite/src/sims/sim7/Sim7.jl:238-249`), and the mean witnessing mass is 1440.8 (`suite/runs/sim7/pilot/summary.json:117-121`). That is a strong positive feedback intervention, not yet a robust life-scale melt result.

### Verdict

**RESIDUAL-CONCERN.** The one-state implementation and H1/H2 branch cleanup are genuine. The substantive surviving `r=-0.99` claim is algebraically loaded, and two diagnoses launder failed criteria into repair instructions without sufficient evidence. Because the record still labels the life-scale criteria falsified, this is not as severe as the remaining Sim 1/5 positive overclaims.

## 6. Continuous T4.8 — RESIDUAL-CONCERN

### The narrow direct results are sound

The autonomous transition test removes the historical phase switch. The latent path is reflected and independent of continuous state (`continuous/src/T48Robustness.jl:266-285`); the resulting external load drives unchanged theory-response dynamics (`continuous/src/T48Robustness.jl:288-316`). The signature requires a Self baseline, capture during the low-depth excursion, and persistent capture after latent recovery (`continuous/src/T48Robustness.jl:319-358`). It is 0/10 even at zero observation noise, so spontaneous collapse-and-stay-collapsed is cleanly falsified for this drive (`reviews/2026-07-10-t48-continuous-robustness.md:92-122`).

The landscape claim is also a legitimate conditional numerical fact. Every cell integrates the same autonomous vector field from a 9x9 initial-state grid, requires converged endpoints, and calls a cell bistable only when both endpoint classes occur (`continuous/src/T48Robustness.jl:131-185`). Connectivity is ordinary 6-neighbor connectivity (`continuous/src/T48Robustness.jl:187-263`). The result—66/125 connected cells containing the historical default—is supported (`reviews/2026-07-10-t48-continuous-robustness.md:73-90`).

It must remain narrow. The vector field explicitly contains the self-support loop, capture-volatility loop, and capture penalty required to create competing basins (`continuous/src/T48Robustness.jl:131-150`). “Bistability exists in this selected ODE and coarse grid” is unattackable. “The theory's landscape survives” is only an existence construction.

The claimed sharp death above safety 0.60 is also too strong for a coarse grid containing only 0.60, 0.80, and 1.00 in that region (`continuous/configs/t48-pilot.yaml:29-35`). The result localizes the boundary to `(0.60,0.80]`; it does not show a sharp boundary at 0.60.

### “Collapse is closed-loop” is a rescue narrative, not the tested result

T4.8 tests autonomous latent drive and finds no crossing. Discrete 6a finds a non-specific, fragile decoupled transition. Sim 1 finds a working action-to-evidence loop in a different count learner. No experiment adds and removes the *same* closed-loop action-evidence mechanism in the continuous or discrete collapse model while holding the landscape and drive fixed.

The synthesis nevertheless moves from “autonomous implementations failed” to “everything enacted survived” and then to a clinical causal claim that people are held in by successful avoidance and released by relationship (`reviews/synthesis-2026-07-10.md:71-89`). That is affirming the consequent across non-equivalent models. The evidence supports:

> Autonomous drift did not produce the registered transition in the tested decoupled implementations; one separately configured Sim 1 action-evidence loop did produce a conditional freezing interaction.

It does **not** yet support:

> Collapse is a closed-loop phenomenon in every setting tested.

The latter would require an explicit loop rescue in Sim 6a/continuous, followed by loop ablation and fresh-seed or bifurcation comparison. Until then, “landscape + loop” is a research hypothesis generated by the failures, not a survivor.

### Registration and committed-record concern

The T4.8 report says criteria, code, and results were created in a pilot with “no git commit” (`reviews/2026-07-10-t48-continuous-robustness.md:3-9`); commit `f4bc28c` then introduces criteria, implementation, and outputs together. Its metadata says `preregistered_before_run: true` but records parent hash `00ecc59`, when none of the T4.8 files existed (`continuous/results/t48_continuous_robustness_pilot/metadata.json:1`). That is an assertion of preregistration, not independent repository chronology.

The committed T4.8 change also did not include the T4.8 README or magic-number sections; at `f4bc28c`, the committed README ends after the historical Stage 3 contract and the committed register contains only Stage 3 constants (`f4bc28c:projects/emergence-suite/continuous/README.md:1-55`; `f4bc28c:projects/emergence-suite/continuous/magic-numbers.md:1-24`). Those explanations exist only as uncommitted workspace changes at review time and were not treated as evidence here. Unlike Sims 1/5/6a, T4.8 has no Step B freeze plus fresh-seed confirmatory. This does not invalidate the 0/10 failure, but it denies the bistability result the stronger confirmatory standing implied by “every sim went through the two-step protocol.”

### Verdict

**RESIDUAL-CONCERN.** Clean for the narrow statements “selected ODE is bistable on 66/125 registered cells” and “registered autonomous excursion crosses in 0/10.” Not clean for the cross-model closed-loop synthesis, the claimed boundary sharpness, or two-step preregistration standing.

## Strongest three surviving claims, ranked

These are deliberately narrower than the synthesis. They are the strongest because each can be defended without clinical translation, causal generalization, or the word “emergent.”

### 1. The selected continuous ODE has a connected bistable region on the registered coarse grid

**Claim.** Under the final T4.8 vector field, endpoint classifier, tolerance, and 5x5x5 beta/gamma/safety grid, 66/125 cells contain both a Self and capture endpoint and form one 6-neighbor-connected component containing the historical reference cell.

**Why unattackable.** This is a direct property of the stated equations and analysis, not a claim that the equations are true of humans. Both attractors use the same autonomous dynamics and are found from multiple initial conditions (`continuous/src/T48Robustness.jl:131-185`, `continuous/src/T48Robustness.jl:213-263`). The result file reports the exact finite-grid fact (`continuous/results/t48_continuous_robustness_pilot/summary.json:1`). Attack can narrow its interpretation, not negate the computation without finding an implementation error.

### 2. Sim 6a's Phase 4 robustness claim is falsified under its own fresh-seed standard

**Claim.** The four-part collapse signature is not robust to the registered decoupling, null mappings, and joint perturbation grid: 12/20 theory signatures, null leakage up to 9/20, and joint volume 5/81.

**Why unattackable.** The failure appears in three logically different criteria, uses fresh disjoint seeds, and is retained despite a pilot that looked better (`suite/runs/sim6a/confirmatory/criteria-results.json:5-51`). Output-label defects do not improve the numbers. Any rescue is a new model or weaker claim, not reinterpretation of this confirmatory.

### 3. Sim 7 now implements one continuously mutated state rather than a stitched biography

**Claim.** For each H1/H2 simulated life, cause arrays, depth posterior, and co-regulation counts are created once, retain object identity, and pass through one update function; H1/H2 differ by one graph-direction index.

**Why unattackable.** The construction and mutation path are visible in code, held-out probes disable learning rather than substitute state, and object identity is audited (`suite/src/sims/sim7/Sim7.jl:103-133`, `suite/src/sims/sim7/Sim7.jl:176-275`, `suite/runs/sim7/pilot/criteria-results.json:5-27`). This does not validate carried capture, prevalence, or therapy. It does retire the old manual-handoff defect.

Sim 3's two-way identity-before-threat, Sim 1's A1.5r family, and Sim 5's learned signature do **not** make this list. Sim 3's replacement estimand was added after a 1,969-combination pilot sweep and directly follows its H1 update order (`suite/src/sims/sim3/magic-numbers.md:39-70`; `suite/src/sims/sim3/Sim3.jl:317-350`). Sim 1 and Sim 5 fail for the reasons above.

## Weakest load-bearing point still standing

The weakest load-bearing point is the synthesis claim that **co-regulation changes the regime while witnessing uniquely supplies the evidence, separately necessary and jointly sufficient** (`reviews/synthesis-2026-07-10.md:30-36`). It bears the program's positive therapy interpretation, and both sides are compromised:

- Sim 5's regime signal is generated by the authored settle table, and “witnessing supplies the evidence” is enforced by the 30/70 root-evidence split (`suite/src/sims/sim5/magic-numbers.md:15-24`).
- Sim 2's fresh confirmatory directly falsifies relational uniqueness: informational content melts 100% of bundles, the no-information-melt criterion is falsified, and the relational-minus-informational advantage is zero (`suite/runs/sim2/confirmatory/criteria-results.json:138-183`). Its primary non-witnessing selectivity criterion is also falsified at 0.770 versus 0.10 (`suite/runs/sim2/confirmatory/criteria-results.json:5-27`).

The synthesis cites Sim 2 as convergence while omitting the confirmatory C3 failure. That is not a marginal caveat; it removes the “witnessing uniquely supplies evidence” half of the claimed seam. Until relational routing is learned or externally calibrated and defeats a live informational route on fresh data, the program has no defensible unique-therapy mechanism—only specified routes through which relational evidence can work.

## New author-the-conclusion patterns introduced by Phase 4

### 1. Pilot-shaped hypothesis laundering

The protocol permits a failed pilot claim to be replaced before confirmatory by a new estimand chosen from that pilot's output:

- Sim 1: new D1 capture probe, 128-trial hardening epoch, pilot-defined release bands, seed-to-cell aggregation change, and observed attenuation edge (`suite/src/sims/sim1/magic-numbers.md:96-115`).
- Sim 3: strict cascade dies; a two-way ordering that the frozen architecture performs 10/10 becomes the replacement confirmatory claim after a 1,969-combination sweep (`suite/src/sims/sim3/magic-numbers.md:39-70`; `suite/configs/sim3-criteria.yaml:54-87`).
- Sim 4: one failed coupling is converted into a positive architectural diagnosis without testing the exact-access gate that can itself create failure (`suite/src/sims/sim4/Sim4.jl:533-562`).

Fresh seeds answer “does the pilot-shaped implementation reproduce?” They do not answer “was this the theory's prediction before the pilot?” A valid amendment must be labeled exploratory unless its mechanism and estimand have independent prior derivation.

### 2. Audit-by-assertion

Several critical audit outcomes are literal summary constants rather than derived checks. Sim 5 writes `supplied_condition_labels_used_as_likelihood = 0.0`; Sim 7 writes condition-branch and replacement counts as zero (`suite/src/sims/sim5/Sim5.jl:906-914`; `suite/src/sims/sim7/Sim7.jl:608-612`). The code currently agrees with the claims, but a future leak could leave the audit green. Audit criteria should be computed from call graphs, parameter equality checks, mutation provenance, or explicit runtime guards—not declared in the result tuple.

### 3. Honest-record shielding

Retaining dead criteria is good provenance. It becomes shielding when the record treats retention itself as evidence that the replacement is valid. The synthesis says retained originals prove goalposts were not quietly moved (`reviews/synthesis-2026-07-10.md:97-104`), while Sim 1 and Sim 3 openly move them and then promote the replacements as confirmed survivors. The move is visible, not absent. Transparency lowers the risk of deception; it does not lower the evidentiary penalty for post-output hypothesis selection.

### 4. Diagnosis inflation

Failed criteria are repeatedly converted into confident causal diagnoses without identifying tests:

- Sim 4 failure becomes “requires concurrent activation,” despite the exact-access deadlock.
- Sim 7 prevalence becomes “world calibration,” despite multiple unseparated load-bearing scales.
- Sim 7 probe failure becomes “absolute metric,” despite relative-reduction code.
- T4.8 autonomous failure becomes positive evidence for closed-loop causation.

The honest statement is often “this implementation failed, and here is a candidate explanation.” The record too often writes “this failure taught us the explanation.”

### 5. Confirmatory artifacts that do not reproduce the frozen code

Sim 6a's committed confirmatory summary says 8 when current code says 16 and its status still says pilot-only (`suite/runs/sim6a/confirmatory/summary.json:114-119`; `suite/runs/sim6a/confirmatory/status.json:1-6`). T4.8 commits criteria, implementation, and outputs together while metadata self-certifies preregistration (`continuous/results/t48_continuous_robustness_pilot/metadata.json:1`). Phase 4 improved seed separation but did not yet establish an immutable, independently checkable registration artifact chain.

## Final accounting

Phase 4 succeeds as a falsification and code-hygiene campaign more than as confirmation of the theory. It genuinely retires several egregious authored mechanisms, makes important paths live, preserves negative results, and establishes three narrow facts: the selected continuous landscape is bistable, the discrete robustness claim fails, and Sim 7 now carries one state.

It does **not** yet establish the synthesis's positive center. The best-supported scientific posture is:

1. the specified models can contain capture-like and Self-like regimes;
2. autonomous transition into capture was not robustly obtained after de-authoring;
3. one specified action-evidence loop can generate a conditional freezing interaction when paired with a pilot-built capture probe;
4. relational interventions can alter state under supplied contingency and routing assumptions;
5. unique witnessing, therapy descent, life-scale graph superiority, and closed-loop necessity remain unearned.

That is a smaller program than the synthesis claims, but it is finally one whose surviving core can be defended line by line.
