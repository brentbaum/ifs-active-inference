## Ranked findings

1. **Sim 4’s “grown protective system” is instantiated directly, including the ordering-producing forecasts. — FATAL**

   1. **Mechanism:** `grow_stack` does not run Sim 1’s formation machinery. It constructs exactly three causes with authored routes, spawn flags, durations, positions, policy counts, mandate counts, and relational forecasts: middle `[2,22,12]`, outer `[8,44,8]`, with the deepest cause inheriting blocker forecasts ([Sim4.jl:134–190](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim4/Sim4.jl:134)). The classifier then reads strings such as `early_acute_overwhelm`, `breakthrough_flood_spawn`, and `chronic_management_accumulation` ([Sim4.jl:477–489](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim4/Sim4.jl:477)). These are taxonomy labels in synonyms.

      The EFE lacks an explicit position term, but position enters through forecast inheritance and update eligibility: a blocked inner cause inherits catastrophic blocker counts and receives zero information gain because contacting it cannot update that forecast ([Sim4.jl:212–246](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim4/Sim4.jl:212)). The initial authored counts make the outer cause the best option; the settled-contact penalty then pushes selection inward. The reported sessions—outer 1, middle 23, deep 29—are the intended count geometry playing out.

      The other headlines are similarly specified: rupture adds 80 counts versus 8 for attunement ([Sim4.jl:273–285](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim4/Sim4.jl:273)); mandate learning is exactly zero; habit and protector practice use different hand-set decay rates; forced access uses `pp=.01 < .09` and pressure ≈1.89 above the 1.35 spawn threshold ([Sim4.jl:417–439](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim4/Sim4.jl:417)).

   2. **Honest fix:** Actually feed a neutral developmental schedule through Sim 1, carry forward whatever number of causes and relational counts it learns, and freeze the classifier before seeing them. Randomize or equalize initial relational forecasts across positions; permute forecasts among layers; remove forecast inheritance; and test whether outside-in ordering survives. Sweep the 80:8 rupture ratio and require asymmetry to arise from accumulated history rather than per-event write sizes.

   3. **What remains:** Given a stack with position-correlated relational forecasts, forecast inheritance, and saturation costs, ordinary optimization can implement outside-in traversal without an explicit `protector_first` objective term. That is an implementation demonstration, not emergence of the stack, taxonomy, ordering, rupture asymmetry, or methods–mission split.

2. **Sim 3 hard-codes both the cascade clock and the generalization axis. — FATAL**

   1. **Mechanism:** The “self → threat → policy” first-passage order is assigned artificial within-trial timestamps: self at `base+1`, threat at `base+2`, policy at `base+3` for H1 ([Sim3.jl:404–420](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim3/Sim3.jl:404)). If all three cross on the same update, the metric declares the desired order by definition.

      Transfer is computed by multiplying the self signal by the parameter later used as the x-axis: `self_to_threat_coupling * cue.root_coupling * self_signal` ([Sim3.jl:238–255](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim3/Sim3.jl:238)). The criterion then sorts and scores monotonicity over that same `root_coupling` ([Sim3.jl:529–549](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim3/Sim3.jl:529)). There is explicitly no perceptual generalization channel. H2 is guaranteed flat because its threat inference returns the untouched threat prior and its policy ignores self-state. Untrained threat-bank leakage is necessarily zero because those banks are never updated.

      Thus the exact output—cascade rate 1.0, monotone gradient 1.0, H2 slope 0, leakage 0—is architectural bookkeeping. The one test that challenged the claimed “structural, not perceptual” margin, A3.2, was actually null: 0.038 against 0.15, yet §9 says transfer was “indifferent to perceptual resemblance.”

   2. **Honest fix:** Use real sequential dynamics without metric offsets; log crossings at distinct updates. Learn root coupling from data instead of supplying it as both causal coefficient and plotting coordinate. Include a conventional feature-overlap pathway, cue-specific uncertainty, misspecified roots, and shuffled root assignments. H1 and H2 should be fitted as competing generative models with matched out-of-sample likelihood, not controls whose transfer routes are enabled versus absent.

   3. **What remains:** A shared latent variable can mathematically transmit a learned change to multiple downstream cues, and softmax/exponential inference can make that transmission nonlinear in depth. Sim 3 demonstrates that implication of the chosen graph; it does not independently discover the cascade, gradient, structural-similarity axis, or H2 reversal.

3. **Sim 7 is not one continuously simulated life; it manually bridges pre-scripted component states. — FATAL**

   1. **Mechanism:** Formation is Sim 4’s preconstructed stack, not an agent undergoing Sim 1 formation ([Sim7.jl:201–205](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim7/Sim7.jl:201)). Adult capture is calculated once by inserting the configured `low_E` into the precision formula ([Sim7.jl:143–150](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim7/Sim7.jl:143)). After a melt, transfer is manufactured by replacing the root bank with `[4,34]` before probing ([Sim7.jl:154–162](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim7/Sim7.jl:154)).

      The H2 control cannot melt because root evidence accumulation and BMR are wrapped in `condition == "full-life"` checks ([Sim7.jl:235–247](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim7/Sim7.jl:235)). Its “distinct failure” is therefore condition branching, not the reversed architecture causing failure under identical rules. Taxonomy recovery reads the authored route/source strings and position metadata. Even postformation sampling rates are assigned as `0.04` or `0.02` from the resulting label ([Sim7.jl:108–132](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim7/Sim7.jl:108)).

   2. **Honest fix:** Maintain one state object from childhood through probing. No manual root replacement, no direct low-depth adult assignment, and no condition-specific suppression of evidence or BMR. H1/H2 should differ only in graph direction. Causes, positions, root counts, depth, and transfer must all be inherited from prior events.

   3. **What remains:** The component APIs can be orchestrated into a coherent narrative trace, and their pre-existing signatures remain numerically compatible. Sim 7 is an integration test and visualization, not additional evidence for emergence or a biographical-scale reversal.

4. **Sim 2’s “derived melt gate” adds an extra depth gate, while C3 is the authored routing table. — FATAL for C3 and the claim that the gate is not imposed**

   1. **Mechanism:** Informational content is defined to have exactly zero root weight; only `met-well` and `met-badly` can update root counts ([Sim2.jl:181–183](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim2/Sim2.jl:181), [Sim2.jl:318–330](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim2/Sim2.jl:318)). The content-swap test therefore swaps in a symbol whose root likelihood is flat by definition. A zero melt rate does not test C3; it restates C3 as the likelihood specification.

      More seriously, E_t enters twice. It first controls relational write weight through the D1 precision balance ([Sim2.jl:164–178](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim2/Sim2.jl:164)), then independently controls how much accumulated evidence BMR may see through `rho(E)=E/(E+E0)` ([BMR.jl:102–122](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/BMR.jl:102)). That violates R2’s “exactly one place” constraint. The D2 derivation itself concedes that vanilla BMR contains no E_t and that `a_E=b_F+rho(E)n` is an additional modeling premise ([d2-bmr-opacity.md:71–116](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/derivations/d2-bmr-opacity.md:71)).

      Quantitatively, `rho(.05)=.0476` and `rho(.90)=.4737`, almost a tenfold second gate. Contact under capture accumulates 20.32 “met” counts—more than witnessing’s 15—but never melts. The result therefore says those counts are hidden because the model declares them hidden.

      Discreteness and selectivity are also structural: pruning flips a Boolean and replaces root precision in one event while never deleting threat or policy banks. The 5/60 BMR interval was selected so the event window is 0.083, automatically under the 0.10 criterion.

   2. **Honest fix:** Compare raw-count BMR, access-weighted BMR, and multiple independently motivated accessibility functions. If R2 is retained, E_t may modulate evidence once, not both writing and BMR access. Learn cross-modal routing, or give informational content a nonzero uncertain root likelihood. Import relational root statistics from formation rather than starting every bundle with the fixed `[2,12]` frozen prior.

   3. **What remains:** Conditional on a self-indexed-accessibility premise, fixed content routing, and chosen priors, canonical prior-swap BMR produces a thresholded one-event prune while retaining other banks. The algebra is sound; the relational exclusivity and depth requirement are assumptions.

5. **Sim 5’s money contrast is an exact condition alias interpreted through a monotone likelihood chosen to produce it. — FATAL**

   1. **Mechanism:** The client’s co-regulation likelihood says, by construction, that observing regulation is progressively more likely at high depth: `[.08,.16,.36,.74,.93]`; dysregulation is its complement ([Sim5.jl:188–200](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim5/Sim5.jl:188)). “Dysregulated” and “fluent-but-threatened” are literally identical simulations: same baseline, parts content, and dysregulated regulation signal. The “regulation ablation” is literally the regulated condition under another name ([Sim5.jl:573–583](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim5/Sim5.jl:573)).

      Parts-language content is the only content that writes root counts; `CONTENT_NONE` writes nothing ([Sim5.jl:262–275](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim5/Sim5.jl:262)). Therefore regulation-only’s zero revision—the celebrated falsification—is guaranteed. Borrowed-then-owned adds regulated-session depth occupancy directly to baseline prior counts until the registered revision threshold is crossed ([Sim5.jl:384–430](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim5/Sim5.jl:384)).

   2. **Honest fix:** Simulate a therapist agent whose regulation state generates noisy physiology and language; have the client learn the mapping. Include misleading bodies, misleading words, unreliable channels, reversed mappings, and independently varied channel precision. The fluent condition must not be a renamed dysregulated tuple.

   3. **What remains:** Given the stipulated likelihood that regulated bodies imply high available depth, Bayesian inference lowers capture and enables the inherited BMR pathway. It demonstrates the consequences of the co-regulation hypothesis, not evidence that co-regulation should have that likelihood or dominate language.

6. **Sim 6a’s collapse is Bayesian, but the direction and recovery are authored in the likelihood and schedule. — SERIOUS**

   1. **Mechanism:** The volatility likelihood was chosen so extreme observations are common under low depth and almost impossible under high depth ([Sim6a.jl:268–297](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim6a/Sim6a.jl:268)). Recovery is continuously pulled toward an explicitly high-depth safety prior. The biography schedule directly switches PE drive from 3.90 to 1.35 to 0.20/0.08 ([Sim6a.jl:374–385](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim6a/Sim6a.jl:374)). The logged `true_depth` does not generate observations; it is assigned alongside the same schedule used to infer depth.

      The identifiability test compares that hand-coded `true_depth` sequence against inference driven by the matching `pe_drive/4.5` sequence ([Sim6a.jl:680–694](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim6a/Sim6a.jl:680)). D1’s 1.9×10⁻¹⁶ error is an algebraic identity because affine log-precision maps were specified; β and γ remain hand-set mapping slopes, despite §9 calling them “not free parameters.” Stage 2 similarly makes safe evidence monotonically increase only reflexive control, so the policy crossover at four observations is parameter geometry ([Sim6a.jl:416–470](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim6a/Sim6a.jl:416)).

   2. **Honest fix:** Generate observations from an independently evolving latent depth, infer the likelihood or calibrate it externally, and evaluate held-out recovery. Include flat, reversed, and non-monotone volatility mappings. Sweep the safety prior, likelihood matrix, β/γ, and policy-control gains jointly rather than ±20% locally.

   3. **What remains:** A categorical Bayesian filter can stably convert volatility observations into a dose-dependent posterior collapse and recovery without directly assigning E_t. The D3 null is legitimate and important: the configured depth range does not produce the claimed S-curve.

7. **Sim 1’s phase boundary and slow path are largely count-mass geometry, with documented post-pilot tuning. — SERIOUS**

   1. **Mechanism:** Omega directly increases both aversive outcome probability and observation precision, while kappa directly subtracts up to 1.40 from the aversive probability of fleeing ([Sim1.jl:208–227](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim1/Sim1.jl:208)). Arousal then increases the Dirichlet write rate by up to 26 counts per trial ([Sim1.jl:322–328](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim1/Sim1.jl:322)). “Frozen” means count precision ≥260 followed by little KL movement under only 24 fixed-strength probe updates ([Sim1.jl:339–365](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim1/Sim1.jl:339), [Sim1.jl:426–428](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim1/Sim1.jl:426)). High omega plus low kappa is therefore designed to create large count mass, and high kappa is designed to reduce the adverse evidence producing it.

      Between the initial and final Sim 1 commits, the authors changed slow-path omega `.74→.90`, kappa `.18→0`, arousal learning gain `15→26`, KL scale `.12→.025`, and added an aversive threshold `.42` described as sitting just below the chronic seeds. The magic-number register acknowledges that the chronic path is selected to accumulate enough counts ([magic-numbers.md:15–26](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/suite/src/sims/sim1/magic-numbers.md:15)). Shuffle invariance is weak because Dirichlet count accumulation is nearly order-exchangeable.

   2. **Honest fix:** Yoke outcome severity and frequency across controllability conditions so kappa changes action efficacy without also changing evidence exposure. Use posterior predictive behavior as revisability rather than a scaled KL score. Freeze the chronic path, learning gain, and classification scale before pilot outcomes, then test on new paths and seeds.

   3. **What remains:** One configured latent-cause/count learner has a nonlinear hardening boundary and supports acute and cumulative routes to high-concentration beliefs. It does not establish that unassimilability-plus-control uniquely generates the boundary, and the run actually falsified the preregistered ordinary-revisable region.

8. **The continuous “Self attractor” is the behavior of an explicitly Self-producing ODE; hysteresis receives direct phase-specific assistance. — SERIOUS**

   1. **Mechanism:** High depth is sustained by a positive self-loop, a baseline target intercept of 1.08, and authored penalties that make capture a competing basin ([ContinuousSim6a.jl:132–160](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/continuous/src/ContinuousSim6a.jl:132)). These are precisely the dynamical facts the result purports to discover. “Across the entire grid” means only 25 cells varying bundle strength and volatility sensitivity while the load-bearing self-loop gain, intercept, depth cost, and capture penalty stay fixed.

      The hysteresis demonstration changes volatility sensitivity from 1.3 to 0.45 during high-depth evidence and directly forces `target_depth >= .88` ([ContinuousSim6a.jl:366–393](/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/continuous/src/ContinuousSim6a.jl:366)). Return to the Self basin is therefore scripted into that phase.

   2. **Honest fix:** Map bifurcations across the feedback gains, intercept, depth cost, and capture penalty; include no-self-loop and reversed-loop null models. Apply identical dynamics across hysteresis phases, varying only externally generated observations.

   3. **What remains:** The selected ODE admits a high-depth fixed point in 25/25 selected cells and competing capture basins in 6/25. This is a useful existence construction, not support for universal, undamageable Self architecture.

9. **“Preregistered” is not independently supported by the repository chronology, and some load-bearing parameters were selected after pilots. — SERIOUS**

   1. **Mechanism:** Sim 2, Sim 5, Sim 6a, Sim 7, and the continuous model each introduce code/config/criteria and reported outputs in the same commit. Sim 3’s code and criteria commit already reports its numerical results; tracked output follows eleven minutes later. Sim 1 is the exception where criteria precede the final tracked run, but its load-bearing parameters were then tuned as described above. Commit `699aa77` explicitly says “post-redesign”; `712fc7a` introduces Sim 2 criteria and results together; `965a997`, `e2b70b2`, `44b9fe9`, and `54537e2` do likewise.

      This does not prove dishonest threshold selection, but it means §9’s categorical “Every result below was preregistered—thresholds fixed before the runs” is not evidenced. At best these are internal registrations committed after exploratory execution.

   2. **Honest fix:** Commit and timestamp criteria, configs, code hash, analysis code, and seed policy before executing confirmatory runs. Preserve pilots separately; use fresh hidden seeds or an immutable generated dataset; prohibit parameter changes after the preregistration hash.

   3. **What remains:** The history documents redesigns and retains several non-supports. It supports transparency about iteration, not the stronger evidentiary meaning of preregistration.

10. **The shipped falsifications and nulls mostly occur where failure was permitted; the headline pathways are architectural zeros or aliases. — SERIOUS**

   1. **Mechanism:** Sim 1’s failures were an arithmetically unreachable >80% KL criterion and a box-shaped attenuation metric; continuous Stage 3 failed because high-dose collapse saturated; Sim 5’s regulation-only “falsification” was guaranteed because no-content writes zero root evidence; Sim 6a’s D3 null tested curve geometry outside the main collapse claim. Sim 3’s A3.2 null is genuinely relevant but is not honored in §9’s stronger prose.

      By contrast, the supposed killer controls could barely fail: informational content has zero root likelihood; H2 threat inference ignores self; no perceptual generalization channel exists; mandate learning is zero; competence banks are never pruned; fluent-threatened and dysregulated are identical; the regulation ablation and regulated condition are identical.

   2. **Honest fix:** Design adversarial tests where all pathways remain active and only their learned weights, causal direction, or predictive adequacy differ. Compare against explicit alternative models using held-out likelihood or model evidence. A falsification should be able to overturn a headline without requiring a bug.

   3. **What remains:** The evaluation harness can emit `null` and `falsified`, and the authors did not delete those outputs. That is process evidence, but it does not show that the principal conclusions faced comparably live failure modes.

## Verdict

**Survive substantially as stated:**

- The narrow computational facts: E_t is a posterior readout in Sim 6a rather than directly assigned; categorical filtering can produce stable collapse/recovery; canonical BMR can generate a discrete prune while retaining separate banks; and the D3 capture-curve criterion is null.
- The final caveat that the simulations cannot establish how human change works.
- Sim 1’s weaker claim that the configured learner permits both acute and cumulative hardening routes.

**Need major weakening:**

- §9’s Sim 1 paragraph should say the boundary occurs under a tuned environment–learning–metric combination; it should disclose that no ordinary-revisable region met the criterion.
- Sim 2 should be presented as a conditional implementation of an added accessibility premise and an authored relational likelihood, not a derivation showing that only relational witnessing can melt.
- Sim 5 should say that the stipulated co-regulation likelihood makes same-words/different-bodies diverge; it does not demonstrate that the body channel naturally dominates.
- Sim 6 should say collapse follows from the chosen volatility likelihood and safety prior. β and γ are hand-set generative-map parameters. The continuous fixed point exists only in the selected ODE and grid.

**Should not be claimed:**

- Sim 3’s cascade as emergent: the timestamp metric encodes the order.
- Sim 3’s generalization gradient, H2 reversal, zero leakage, or structural-over-perceptual result as discriminating discoveries: they are direct consequences of the supplied coupling graph and absent alternative channel; A3.2 was null.
- Sim 4’s “grown protective system,” blind taxonomy recovery, emergent protector-first ordering, emergent rupture asymmetry, habit–protector split, or methods-not-mission result. These are initialized or assigned.
- Sim 7 as “one agent, one life, only the world scripted,” or as new evidence. Its strongest legitimate status is an integration test showing that manually bridged component states can reproduce the intended narrative.
- §9’s concluding sentence that the clinical shape arises “from the three ingredients the account permits itself.” Several decisive ingredients are additional: formation-coded metadata, position-correlated relational priors, root-routing tables, the `rho(E)` BMR-access premise, monotone co-regulation and volatility likelihoods, condition-specific control flow, and metric definitions that encode ordering.