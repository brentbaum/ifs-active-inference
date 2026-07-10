# Adversarial review of Sim 8

Date: 2026-07-10  
Reviewer: GPT-5.6-sol  
Claim under review: “therapy-descent ordering (protectors before exiles) can emerge from grown pairwise coupling in a concurrent-activation architecture”  
Scope: `suite/src/sims/sim8/Sim8.jl`, the Sim 8 README and magic-number register, Sim 8 config/criteria and pilot outputs, the concurrent-activation sketch, and Sim 4's three-cycle record  
Method: hostile code/results review plus read-only diagnostic re-execution of the committed pilot model; no model, config, criteria, or result file was changed

## Bottom line

**REJECT the stated paper claim.** The pilot misses its own coupling, descent, and shuffle thresholds. More importantly, the desired later-on-earlier direction is inserted at the cause-birth boundary: a newborn observer writes about causes that were active entering its birth trial, while the reverse record is necessarily zero because the newborn's entering activation is initialized to zero; on aversive high-excess births, that one-way write is additionally amplified. Therapy then turns the authored asymmetry into an order using an outcome-selected score, fixed-size safe writes, and strongly unequal bank sizes. This is not evidence that protector-before-exile ordering emerged from neutral concurrent inference.

The exploratory label and unusually candid iteration log are good recordkeeping. They do not reduce the evidentiary penalty. Sim 8 is the re-review's “pilot-shaped hypothesis laundering” pattern compressed into seven rounds on the same ten seeds.

## 1. The desired direction is written at birth, not discovered — **FATAL**

The code's central symmetry claim is false in the effective state transition.

1. Spawn pressure is accumulated from surprise excess, and a cause is created when that pressure crosses the spawn gate (`suite/src/sims/sim8/Sim8.jl:178-190`). The newborn is appended with entering activation exactly `0.0` (`suite/src/sims/sim8/Sim8.jl:185-187`).
2. The newborn is created **before** the current-trial responsibility calculation and personal writes (`suite/src/sims/sim8/Sim8.jl:192-204`). It therefore exists as an observer on its own birth trial.
3. Internal learning then loops over every observer `j` without multiplying by `j`'s responsibility or activation. It weights only the observed cause `i` by `i`'s activation entering the trial (`suite/src/sims/sim8/Sim8.jl:205-237`). Thus the newborn can immediately write about every older active cause even though the newborn itself had zero entering activation.
4. The reverse write—an older cause writing about the newborn on that same event—is structurally zero because the newborn's entering activation was just appended as zero (`suite/src/sims/sim8/Sim8.jl:187`, `suite/src/sims/sim8/Sim8.jl:231-235`).
5. More generally, responsibility itself uses count mass as its prior, so old causes receive much larger entering activation than young causes (`suite/src/sims/sim8/Sim8.jl:136-145`). The target-weighted internal rule therefore gives observers high-mass banks about old causes and low-mass banks about young causes. `aversion` then converts that exposure asymmetry into directional strength through `n/(n+4)` confidence (`suite/src/sims/sim8/Sim8.jl:252-260`). Even equal conditional risk would be scored more strongly later-about-earlier.
6. When a high-surprise birth event is aversive, its already one-way birth write is further multiplied by `1 + 30 * excess` (`suite/src/sims/sim8/Sim8.jl:181-190`, `suite/src/sims/sim8/Sim8.jl:221-235`). Read-only reproduction confirms that several pilot births, including the load-bearing first birth in seed 1001 and middle birth in seed 1004, receive this amplification. Other births are safe, which limits but does not cure the direction built into entering activation, exposure mass, and confidence.

That is not a merely symmetric lag rule exposed to an asymmetric world. It is an asymmetric birth transition: “later sees earlier on the birth event; earlier cannot see later on that event.” The architecture directly supplies the causal arrow the result is said to grow. No comparison of IDs is needed to author direction when zero-at-birth activation plus update order already implements later-to-earlier.

The narrow `born_trial` audit does pass: the stored field is read only in the coupling and descent readouts (`suite/src/sims/sim8/Sim8.jl:349-359`, `suite/src/sims/sim8/Sim8.jl:367-374`). That fact is irrelevant to the defect. Chronological asymmetry enters through cause creation, zero entering activation, and same-trial update order, not through reading the `born_trial` integer inside access or therapy.

This also contradicts the design obligation that direction arise because the older cause's activation is the most predictive feature of distress (`concurrent-activation-sketch.md:29-47`). The implementation does not compare candidate features or learn that activation is most predictive. It exposes only cause activations, and its update order guarantees that the newborn receives the formative older-cause observation unreciprocated.

**Verdict:** **FATAL.** The claimed direction is encoded at the event-order seam.

## 2. The readout converts tiny, birth-loaded contrasts into “protectors first” — **FATAL**

### 2.1 There are no identified protectors or exiles

The paper claim is in a stronger register than the model's variables. Sim 8 has causes and formation times. It never classifies a cause as a protector or exile. “Protector before exile” is scored as newest-to-oldest first selection (`suite/src/sims/sim8/Sim8.jl:367-374`; `suite/configs/sim8-criteria.yaml:24-31`). Newer is being used as a synonym for protector and older as a synonym for exile—the very clinical ordering the paper purports to derive.

`protective_share` is not a learned role. It defines every non-approach action—flee, appease, and attenuate—as protective (`suite/src/sims/sim8/Sim8.jl:263`). Moreover, the model selects one global policy by `argmax`; every cause is then credited with that same policy in proportion to its responsibility (`suite/src/sims/sim8/Sim8.jl:148-168`, `suite/src/sims/sim8/Sim8.jl:193-200`). A cause's “protective share” therefore largely reports how much responsibility it had during globally selected non-approach actions, not a policy that cause independently selected. In read-only reproduction, protective shares were 0.94–0.99 for every cause in seeds 1001, 1002, 1004, 1005, 1009, and 1010. The putative exile is just as “protective” by this definition as the putative protector.

### 2.2 Attribution normalization launders effect size

The internal-bank readout first takes only a positive conditional-minus-baseline contrast and multiplies it by a confidence term (`suite/src/sims/sim8/Sim8.jl:243-260`). Access then normalizes each observer's contrasts across targets (`suite/src/sims/sim8/Sim8.jl:265-282`). This changes the question from “is there enough learned coupling to block this target?” to “where should this observer's blocking be aimed, conditional on any positive contrast existing?” Absolute coupling is largely replaced by a relative share, while magnitude is supplied by the observer's broadly shared personal aversion and near-universal non-approach share.

The `0.01` term is not innocuous zero-division smoothing. Zero is already handled by `total_attr <= EPS && continue`, so the denominator cannot be zero when the division executes (`suite/src/sims/sim8/Sim8.jl:278-280`). The constant is an undocumented shrinkage scale. Observed contrasts are mostly of the same order or smaller: seed 1004's supposedly perfect 6/6 direction includes `0.000923` and `0.001186`; seed 1001's 3/3 includes `0.001037` (`suite/runs/sim8/pilot/pair_metrics.csv:2-11`). Adding `0.01` materially determines how those tiny contrasts become attribution shares. The direction criterion nevertheless counts any positive epsilon as a full directional pair (`suite/src/sims/sim8/Sim8.jl:349-359`). “6/6 directional” consequently says nothing about six substantively sized gates.

### 2.3 Therapy selection and bank sizes already generate much of the ordering

Therapy maximizes `access * aversive_fraction`, then adds a fixed six safe counts scaled by access (`suite/src/sims/sim8/Sim8.jl:287-309`). This has two built-in ordering effects:

- causes born later have much smaller personal banks because responsibility uses normalized cause mass as its prior (`suite/src/sims/sim8/Sim8.jl:136-145`);
- a fixed safe-count write changes a small young bank far more than a large old bank, so the selected young cause rapidly falls below the next candidate.

Read-only reproduction of seed 1004 gave personal bank masses of approximately `112.94, 21.40, 8.88, 6.73` from oldest to newest. Initial access-weighted aversion scores were `0.184, 0.363, 0.355, 0.440`. The four-layer order is therefore produced by a gate that suppresses the massive old bank, followed by a fixed write that rapidly moves the tiny new bank. This is a hand-built peeling algorithm, not a neutral clinical readout.

A diagnostic arm setting access to one while retaining the same formed agents, aversive-fraction selector, and fixed write descended in 3/7 evaluable seeds; the committed baseline descended in 4/7. In particular, seeds 1002 and 1005 descend without any coupling gate at all. Seed 1004 does require the gate to turn the no-block first-selection order `2,3,4,1` into `4,3,2,1`, so its trace is not *solely* a bank-size artifact. It is still unearned evidence: the gate is driven by the birth-authored coupling above, and the submitted controls never isolate it from bank exposure, calibration, or the selector's peeling dynamics.

### 2.4 The pilot is narrated around its two best cases

Only seven seeds grew multiple causes; only four of those seven passed descent (`suite/runs/sim8/pilot/summary.json:20-34`). Two passes are trivial two-cause cases (1002 and 1005), and seed 1005 still passes after shuffling (`suite/runs/sim8/pilot/summary.json:47-56`, `suite/runs/sim8/pilot/summary.json:77-85`). Among stacks of at least three causes, only 1001 and 1004 pass, while 1007 and 1009 fail (`suite/runs/sim8/pilot/summary.json:36-45`, `suite/runs/sim8/pilot/summary.json:68-75`, `suite/runs/sim8/pilot/summary.json:98-125`). The README then makes exactly 1001 and 1004 the marquee and declares the chain proven functional (`suite/src/sims/sim8/README.md:110-131`). That is best-case narration, not population evidence.

**Verdict:** **FATAL** for “protectors before exiles.” The roles are aliases for age, the coupling effect-size threshold is absent, and the therapy rule plus unequal bank sizes supplies much of the observed order.

## 3. Seven pilot-conditioned redesigns are tuning at a more powerful level — **FATAL**

“Mechanism structure iterated, constants not tuned” is not an evidentiary distinction. Structural and estimand tuning is more dangerous than scalar tuning because it changes what causal quantity exists and what counts as success. The README records the adaptive path explicitly:

1. nondirectional valence writes led to severity weighting;
2. another null led from an absolute baseline to a conditional-minus-marginal contrast;
3. backwards pairs led to a different write scale;
4. partial direction led to attribution-share blocking;
5. reversal seeds led to the excess gate;
6. destruction of the best trace led to gain 30;
7. the best state is then summarized around seeds 1001 and 1004 (`suite/src/sims/sim8/README.md:22-51`, `suite/src/sims/sim8/README.md:72-124`).

Each change was chosen after inspecting these same pilot outcomes. The final hypothesis is therefore “the seventh mechanism selected for these ten seeds produces the seventh mechanism's favored readout on some of those seeds.” Writing a prediction immediately before rerunning already-observed seeds does not restore prospective status. It only documents the next adaptive move.

The assertion that no constant was tuned is also false in the ordinary methodological sense. The register says 40 sessions were chosen because they are enough for a four-cause chain, the episode schedule was chosen so stacks of at least three can form, and `0.01` was fixed immediately before the iteration-5 run (`suite/src/sims/sim8/magic-numbers.md:11-20`). “Not swept” means no grid search was recorded; it does not mean outcome-independent.

Most damagingly, gain 30 was selected after iteration 6 destroyed seed 1001, expressly to restore the formative write (`suite/src/sims/sim8/README.md:91-108`; `suite/src/sims/sim8/magic-numbers.md:28`). Its claimed derivation is not faithful to the code. The register computes a “personal-bank formative scale” by multiplying `(1 + 60 * arousal / 5.2)` by severity 6, but personal-bank writes do **not** multiply by severity; they use `learning_rate_base * (1 + gain * arousal / scale) * responsibility` (`suite/src/sims/sim8/Sim8.jl:172-203`). The internal write instead uses `internal_write_rate * (1 + 30 * excess)` (`suite/src/sims/sim8/Sim8.jl:221-235`). Gain 30 is therefore neither inherited equivalence nor a unit-preserving derivation. It is an outcome-shaped scale chosen to recover a pilot trace.

The “unassimilable events only” prose is likewise stronger than the implementation. Assimilable aversive events still receive base weight 1; only their *extra* amplification is zero (`suite/src/sims/sim8/Sim8.jl:224-235`). Hundreds of base-weight coexistence writes remain able to alter attribution.

Nor did the targeted repair solve its target. The final log says the backwards attribution in seeds 1009 and 1010 persisted through both the excess gate and gain restoration, directly contradicting the proposed explanation that assimilable mid-cluster events caused those reversals (`suite/src/sims/sim8/README.md:110-123`). Yet the record promotes the state as “best” and moves immediately to another post-hoc mechanism.

Labeling the whole sequence exploratory is correct (`suite/src/sims/sim8/README.md:1-7`; `suite/runs/sim8/pilot/summary.json:1-19`). Claiming in the same record that the causal chain is “proven functional and bidirectionally honest” is not (`suite/src/sims/sim8/README.md:126-132`). Transparency about post-outcome selection does not turn it into evidence.

**Verdict:** **FATAL** for a submitted positive claim. This is pilot-shaped mechanism, scale, and estimand selection.

## 4. The shuffle control destroys exposure mass and observer calibration — **FATAL / NON-DIAGNOSTIC**

The control globally permutes entire `[safe, aversive]` count vectors across all existing ordered pairs (`suite/src/sims/sim8/Sim8.jl:316-323`). But an internal bank contains at least three things at once:

1. the target association;
2. its safe/aversive fraction;
3. its total exposure mass, which directly controls confidence through `n/(n+4)` (`suite/src/sims/sim8/Sim8.jl:252-260`).

Bank mass is strongly coupled to age and entering activation by construction (`suite/src/sims/sim8/Sim8.jl:229-235`). In read-only reproduction, seed 1004's young causes held roughly 33–57 effective observations about the root, whereas the root held only about 2–10 about each young cause. The global permutation moves those masses along with valence. It therefore breaks the age/exposure geometry, not merely the mapping “which part predicts catastrophe about which target.” A degradation can follow trivially from moving a high-confidence bank into a low-exposure pair or vice versa.

Worse, `aversion` evaluates the moved bank against the **recipient observer's unchanged** `witness_baseline` (`suite/src/sims/sim8/Sim8.jl:252-260`). The shuffle thus pairs one observer's conditioned sample with another observer's marginal calibration. It can create or erase contrast without changing anything resembling causal direction. Personal aversion and `protective_share` remain attached to the observer while the conditioned bank moves, producing a second mismatched composite in access (`suite/src/sims/sim8/Sim8.jl:274-282`).

A diagnostic control would preserve, for every ordered pair, its total count mass and every observer's baseline/personal banks, while permuting only target-specific residual risk or direction labels within appropriately exposure-matched strata. The committed control does not.

Even on its own terms it fails: baseline descent is 4 and shuffled descent is 2, for degradation 2 against the registered threshold 3 (`suite/runs/sim8/pilot/summary.json:30-34`; `suite/runs/sim8/pilot/criteria-results.json:41-51`). Calling this proof that coupling carries ordering reverses the registered verdict.

**Verdict:** **FATAL / NON-DIAGNOSTIC.** The shuffle changes bank magnitude, confidence, observer calibration, and target assignment simultaneously, and it still misses its threshold.

## 5. The baseline contrast and “concurrent activation” do not bear the claimed interpretation — **SERIOUS**

### Witness baseline

The contrast is not an obvious coding bug: conditioned and baseline banks use the same outcome weight, and each cause begins accumulating its baseline only after it exists (`suite/src/sims/sim8/Sim8.jl:118-120`, `suite/src/sims/sim8/Sim8.jl:224-235`). But it is mislabeled as “what j's world is like.” Every observer's baseline is updated at full weight on every subsequent event, regardless of whether `j` is active or responsible (`suite/src/sims/sim8/Sim8.jl:226-228`). The conditioned bank is weighted by the *target's* activation, also regardless of the observer's activation (`suite/src/sims/sim8/Sim8.jl:229-235`). It is therefore a global post-birth event marginal versus a target-activation-weighted event fraction, not an observer-specific experiential baseline.

During therapy, safe evidence is added to conditioned banks but not to `witness_baseline` (`suite/src/sims/sim8/Sim8.jl:303-309`). That may be a chosen gate-relaxation intervention, but after the first contact the readout is no longer the advertised conditional-versus-marginal contrast under a common write rule.

### Soft responsibility

Soft responsibility is numerically present, so it would be inaccurate to call the implementation literal winner-take-all. It is nevertheless strongly mass-dominated. Responsibility uses total affect-count mass as its prior (`suite/src/sims/sim8/Sim8.jl:136-145`), giving old causes a rich-get-richer advantage. Across read-only reproduction of the seven multi-cause seeds, the mean maximum responsibility ranged from 0.77 to 0.95 and the effective number of active causes ranged only from 1.11 to 1.63; roots ended with 75%–95% of personal bank mass.

The policy side is more cosmetic still. `policy_scores` weights causes by count mass, not the current posterior responsibility, and collapses their contributions to one `argmax` action (`suite/src/sims/sim8/Sim8.jl:148-168`). All causes then learn that one action (`suite/src/sims/sim8/Sim8.jl:193-200`). Sim 8 therefore has fractional concurrent attribution but no concurrently selected part policies. Its decisive newborn internal write does not even require the newborn observer to have nonzero responsibility.

**Verdict:** **SERIOUS.** `born_trial` itself is readout-only and soft responsibilities are real fractional values, but the baseline is not observer-specific, mass priors make concurrency shallow, and global winner-take-all action selection makes “concurrent-activation architecture” a much stronger description than the implementation earns.

## 6. The registered pilot result is null, not support — **FATAL FOR THE PAPER REGISTER**

Sim 4 ended after three cycles with outside-in ordering at 1/10 under all three contact rules and explicitly retained missing concurrency only as a candidate explanation (`suite/src/sims/sim4/README.md:139-175`). Sim 8 tests that candidate adaptively; it does not inherit confirmation from Sim 4's falsification.

The Sim 8 registration requires at least eight directional seeds, at least eight descent passes, and shuffle degradation of at least three (`suite/configs/sim8-criteria.yaml:16-39`). The observed values are 4, 4, and 2, labeled `null`, `null`, and `weak_support` respectively (`suite/runs/sim8/pilot/criteria-results.json:17-51`). There are only seven evaluable stacks, so the two eight-seed criteria were not merely missed; after formation they were arithmetically unreachable (`suite/runs/sim8/pilot/summary.json:20-34`).

The pairwise sign statistic also overweights deep stacks: seed 1004 contributes six of the pilot's 14 directional pair wins, while a two-cause seed contributes one. The summary partly avoids this by averaging per-seed fractions, but the marquee “6/6” remains a selected within-seed fact from one of ten pilot worlds (`suite/runs/sim8/pilot/pair_metrics.csv:6-11`; `suite/runs/sim8/pilot/summary.json:68-75`). Seed 1009 supplies the matched warning: another four-cause stack has only 2/6 directional pairs and selects the oldest first (`suite/runs/sim8/pilot/summary.json:118-125`).

**Verdict:** **FATAL FOR THE PAPER REGISTER.** The only prospective criteria say null/null/weak support, and the post-pilot mechanism itself contains the desired arrow.

## One-sentence honest claim

**In a repeatedly pilot-redesigned exploratory simulator, a lagged and excess-amplified internal-bank rule followed by access-times-aversion selection produced newest-to-oldest first selection in 4 of 7 multi-cause pilot seeds versus 2 of 7 after a confounded whole-bank permutation, demonstrating behavior of the chosen rules but not emergence of protector-before-exile therapy ordering.**
