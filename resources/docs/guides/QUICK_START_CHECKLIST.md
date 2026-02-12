# Active Inference Modeling: Quick Start Checklist

**For future modelers: Use this checklist before, during, and after implementation.**

---

## Phase 1: Before You Code (1-2 hours)

### Preparation
- [ ] Read paper 2x (overview + mechanism detail)
- [ ] Write 1-sentence core claim (what falsifies this model?)
- [ ] Identify what changes between conditions (usually 1-2 factors)
- [ ] Check library capability gaps (do any exist?)

### Design
- [ ] Draw state diagram (all factors, transitions, observations)
- [ ] Specify A/B/C/D matrices with real numbers (not placeholders)
- [ ] Identify what gets gated (A matrix? D prior? Learning rate?)
- [ ] List all mechanisms (context-blindness? learning suppression? transitions?)
- [ ] Pre-register test thresholds (write them down before implementing)

### Expert Review (If Complexity > 60)
- [ ] Ask Codex Architect: "Am I over-complicating this?"
- [ ] Key question: "Can any factors be merged?"
- [ ] Red flag: State factor doing >3 jobs → split it

### Checklist Before Coding
```
Factor count:    __ (target: 2-5)
State dimensions: __ (target: avg 2-4 states per factor)
Outcome modalities: __ (target: 3-5)
Learnable params: __ (target: 1-3)
Complexity score: __ (target: 30-80)
Gating locations: __ (target: 1-2 critical gates)
```

---

## Phase 2: During Implementation (2-5 days)

### Week 1: Matrix Construction
```julia
# Day 1: A matrices
- [ ] A1 shape verified
- [ ] A1 values match spec
- [ ] A2-A4 constructed
- [ ] All A columns sum to 1.0

# Day 2: B matrices
- [ ] B matrices match transitions
- [ ] Identity checks pass
- [ ] Control structure clear

# Day 3: C/D matrices + policies
- [ ] C preferences initialized
- [ ] D priors set by condition
- [ ] Policy set defined (usually 4-8 policies)
```

### Week 1: Single Trial Test
```julia
# Before running 100+ trials, test one at a time:

# Day 4: Single trial without agent
- [ ] Run observation model: o = A @ s (works?)
- [ ] Run transition model: s' = B @ s @ u (works?)
- [ ] Shapes all correct?

# Day 4: Single trial with agent (full EFE)
- [ ] Agent infers state from observation
- [ ] Agent selects policy via EFE
- [ ] Policy is deterministic or probabilistic as expected?
- [ ] Action executed correctly?

# PRINT DEBUG INFO:
# - Observation at each timestep
# - Posterior belief
# - EFE for each policy (why was this one chosen?)
# - Action taken
```

### Week 2: Single Condition
```julia
# Test BASELINE condition first (should require no intervention)

# Day 5-6: Run baseline condition
- [ ] Can run 100 trials without errors
- [ ] P(avoid) stable across trials (should be ~0.95 or ~0.05, not fluctuating wildly)
- [ ] D3 unchanged (mechanism test: learning disabled)
- [ ] Visualize: P(avoid) over 100 trials → should be flat line

# If not flat:
#   STOP. Something is wrong.
#   - Check: Is A1 truly uniform in modular mode?
#   - Check: Is D1 fearful enough?
#   - Check: Are A and D mismatched?
```

### Week 2: All Conditions
```julia
# Day 7: Implement remaining conditions (CBT, CT, CT-dangerous)
- [ ] Each condition runs independently
- [ ] Conditions properly isolated (no state leakage)
- [ ] Visualize all 4 on same plot → can you see the differences?

# Early visualization check:
# - Baseline: flat high line (P ≈ 0.95)
# - CBT: decreasing line (P: 0.95 → 0.05, sigmoid shape)
# - CT: step function (P: 0.95 → 0.05 at trial 51)
# - CT-dangerous: flat high line (P ≈ 0.95)
#
# If you don't see these patterns, something is mechanically wrong.
```

### Weekly Checkpoint
```
After each week, answer:
1. Do baseline/CBT/CT/dangerous show visually different patterns? YES/NO
2. Can you explain why mechanically? YES/NO
3. Any parameters or code you don't fully understand? YES/NO
4. If YES to Q3, resolve before moving forward.
```

---

## Phase 3: Verification (3-5 days)

### Tier 1: Mechanism Tests
```julia
# These MUST pass. No exceptions.

Test 1: Baseline maintains avoidance
  P(avoid) mean trials 51-100 > 0.9
  └─ Checks: Modular mode blocks learning

Test 6: Modular blocks learning
  D3_final ≈ D3_initial (change < 0.01)
  └─ Checks: Schema is truly protected

Test 4: CT resolves without belief change
  D3 change < 0.15 (mostly unchanged)
  └─ Checks: Mechanism is context-sensitivity, not updating
```

**If any Tier 1 test fails:**
- STOP all other testing
- Print out the failing value
- Trace backward: Is it A1? D1? Learning gate? Precision?
- Fix mechanically, then retest

### Tier 2: Behavioral Tests
```julia
# These should pass 85%+ of the time.

Test 2: CBT resolves gradual
  Fit sigmoid to trajectory, R² > 0.9
  P(avoid) mean trials 51-100 < 0.3
  └─ Checks: Learning produces smooth curve

Test 3: CT shows step function
  Change magnitude > 0.7
  Change timing within ±3 of trial 51
  Change width < 5 trials
  └─ Checks: Behavioral change is rapid, not gradual

Test 5: CT-dangerous maintains
  P(avoid) mean trials 51-100 > 0.9
  No large change-point detected
  └─ Checks: Agent correctly maintains avoidance when dangerous
```

### Tier 3: Comparative Tests
```julia
# Optional: Verify your model is better than alternatives.

Test 7: CT favors step model
  Bayes Factor (step vs sigmoid) > 10
  └─ Checks: Step function model better explains data
```

### Replication & Statistics
```julia
# Run 30-50 replications for each condition

For each replication:
  - [ ] Run full 100-trial sequence
  - [ ] Record P(avoid) trajectory
  - [ ] Record D3_initial and D3_final

Aggregate across replications:
  - [ ] Compute mean trajectory + std
  - [ ] Compute 95% CI bands
  - [ ] Check for bimodal distributions (outliers?)

Visualization:
  - [ ] Plot mean trajectory
  - [ ] Add shaded CI bands (std/sqrt(n) * 1.96)
  - [ ] Mark intervention point (trial 51) with vertical line
```

---

## Phase 4: Documentation (1-2 hours)

### Learnings.md
```markdown
For each design iteration:
- [ ] Problem encountered (1 sentence)
- [ ] Initial approach (what you tried)
- [ ] Why it failed (the mechanism)
- [ ] Root cause (architecture vs spec vs theory)
- [ ] Solution (what changed)
- [ ] Code example (before/after)
- [ ] Lesson for next modeler (actionable)
```

### README
```markdown
Status:
- [ ] Design complete (date)
- [ ] Implementation phase 1 complete (date)
- [ ] Architect review (date)
- [ ] All tests passing (date)
- [ ] Extension implemented (if applicable, date)

Results summary:
- [ ] # tests passing / total
- [ ] Key finding (1 sentence)
- [ ] How to run it
- [ ] How to interpret results
```

### Code Comments
```julia
# For each key parameter, comment:
# - Where does this come from? (paper section? derivation? empirical?)
# - Why this value not others? (thresholds justified?)
# - Sensitivity: Does ±10% change the results?

# Example:
# D1_fearful = [0.1, 0.3, 0.6]
# Source: Chamberlin p12 - "stress creates context-free policies"
# Rationale: Modular schema should have uncertain, fearful prior
# Threshold: 0.6 chosen to make context ambiguous, not terrifying
# Sensitivity: Tested with [0.05, 0.35, 0.60] and [0.15, 0.25, 0.60] - results stable
```

### Regression Test
```julia
function test_regression()
    """Permanent test to prevent future breakage."""
    baseline = run_chamberlin_2022(n_replications=30)

    # Core mechanism tests
    @test baseline.ct_step_magnitude > 0.7
    @test baseline.modular_blocks_learning == true
    @test baseline.baseline_maintains_avoidance == true

    # Numerical stability (allow ±5% drift)
    @test 0.03 - 0.02 < baseline.ct_p_avoid_end < 0.03 + 0.02
end
```

---

## Quick Diagnostic: When Tests Fail

### Test 1 Fails: Baseline P(avoid) not > 0.9
```
Check in order:
1. Is A1 truly uniform in modular mode? (print A1[:,:,:,:,1])
2. Is D1 truly fearful in modular mode? (print D1_modular)
3. Is learning rate η=0 in modular mode? (add @assert eta == 0)
4. Is precision γ reasonable? (should be 4.0+)

Most likely: A1 or D1 incorrect
```

### Test 3 Fails: CT doesn't show step function
```
Check in order:
1. Is intervention applied at trial 51? (add println when intervention fires)
2. Does intervention change schema_mode? (check agent.state[4])
3. Does changed mode affect A1? (print A1 before/after intervention)
4. Is EFE recalculated after intervention? (should happen automatically)

Most likely: Intervention not being applied OR not affecting behavior
```

### Test 2 Fails: CBT doesn't show sigmoid curve
```
Check in order:
1. Is learning enabled in integrated mode? (η > 0?)
2. Is learning rate too high? (try 0.3 instead of 0.5)
3. Is there unintended structure? (e.g., does precision change too?)
4. Are you computing D3 update correctly? (check Dirichlet update formula)

Most likely: Learning rate or update mechanics
```

### Test 6 Fails: Modular mode still learns
```
Check in order:
1. Is there a pathway to update D3 when modular? (grep for "D3" in inference code)
2. Is learning rate gating actually being used? (add @assert at update site)
3. Is there a different learning mechanism? (e.g., A matrix updating secretly)

Most likely: Learning gate not applied or applied incorrectly
```

---

## Red Flag Checklist

If you see any of these, STOP and investigate:

- [ ] **P(avoid) shows extremely high variance** (std > 0.15)
  → Indicates bimodal distribution or instability
  → Usually means mechanism is broken

- [ ] **Test passes on first 10 replications, fails on replication 25**
  → Indicates randomness leak or numerical instability
  → Check for uninitialized variables, seed issues

- [ ] **Changing a parameter from 0.5 to 0.6 breaks multiple tests**
  → Indicates over-fitting or fragile design
  → Usually means you're balancing on a knife edge

- [ ] **You can't explain why a parameter has its current value**
  → Indicates accidental tuning (even if you don't realize it)
  → Pre-register all parameters before implementing

- [ ] **Baseline condition doesn't show flat P(avoid) line**
  → Indicates core mechanism is broken
  → Fix before testing other conditions

- [ ] **CT condition shows P(avoid) change at wrong time (not trial 51±3)**
  → Indicates intervention isn't being applied correctly
  → Add debug prints, check agent state directly

---

## Success Criteria Checklist

- [ ] All Tier 1 mechanism tests pass
- [ ] All Tier 2 behavioral tests pass with 85%+ success rate
- [ ] Test thresholds were pre-registered (written before implementation)
- [ ] Learnings.md documents all design decisions
- [ ] Code is commented (parameters justified)
- [ ] Regression test created
- [ ] Can explain every design choice mechanistically
- [ ] Paper's core claim is operationalized and tested
- [ ] Results match paper's predictions

---

## Emergency: If Everything Fails

1. **Revert to working state** (git checkout or last backup)
2. **Identify what broke** (run just the changed code)
3. **Consult Codex Architect** - Your 3rd failed attempt, time for expert
4. **Document the failure** (learnings.md: what did you try? why did it fail?)
5. **Start simpler** - Can you model just the mechanism (ignoring noise)?

---

## Post-Implementation Reflection

After all tests pass:

```markdown
## Model Completion Reflection

**What went well?**
- [List 2-3 things that worked as expected]

**What was harder than expected?**
- [List 2-3 surprises or blockers]

**Design decisions I'm confident about:**
- [List 2-3 core design choices and why]

**Design decisions I'm uncertain about:**
- [List anything that feels hacky or unjustified]

**For the next modeler:**
- [Top 3 lessons that would save them time]

**Open questions:**
- [What would break this model?]
- [What would improve it?]
```

---

## Metrics Snapshot

**After 30-50 replications, you should be able to fill in:**

| Metric | Baseline | CBT | CT | CT-Dangerous |
|--------|----------|-----|-----|--------------|
| P(avoid) pre | > 0.9 | > 0.7 | > 0.9 | > 0.9 |
| P(avoid) post | > 0.9 | < 0.3 | < 0.3 | > 0.9 |
| D3 change | < 0.01 | > 0.3 | < 0.15 | - |
| Step magnitude | < 0.1 | < 0.3 | > 0.7 | < 0.1 |
| Curve shape | flat | sigmoid | step | flat |

---

**Remember:** If a test fails, it's telling you something about your model. Listen to it.

**Last updated:** 2026-01-30
