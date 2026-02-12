# Prevention Strategies & Lessons Learned: Chamberlin 2022 Discovery Modeling

**Author's Note:** This document synthesizes insights from the complete lifecycle of the Chamberlin 2022 (Coherence Therapy) active inference reproduction, from initial design through implementation and extension to gradual discovery modeling. It serves as a reference guide for future Active Inference modelers.

---

## Executive Summary

The Chamberlin 2022 project teaches three critical lessons:

1. **Binary State Extensions Require Interpolation** - When extending binary state factors (modular/integrated) to multi-level (implicit/partial/explicit), interpolate continuously rather than creating hard transitions. This preserves theoretical coherence and prevents "cheat" models.

2. **Know When to Delegate to Experts** - After 2+ failed design attempts or when architectural tradeoffs emerge, consult external experts (Codex Architect). This saves 5-10 hours of iteration and catches design flaws early.

3. **Step-Function vs Gradient Transitions** - Distinguish between *mechanisms* that create discontinuities (binary state change) and *processes* that unfold gradually (precision annealing, interpolated factors). Conflating these leads to over-specification.

---

## Part 1: Design Patterns for Gradual State Transitions

### 1.1 The Interpolation Pattern

**Problem:** The original model showed *instant* behavioral change when schema_mode switched from modular → integrated at trial 51. But the paper describes Discovery as "resembling simulated annealing" - an iterative process.

**Wrong Approach (Cheat):**
```julia
# Trial 50: P(avoid) = 0.96 (modular, context-blind)
# Trial 51: INTERVENTION APPLIED
# Trial 51: P(avoid) = 0.03 (integrated, context-sensitive)
# ...mechanism: schema_mode flipped from 1 → 2
```

This conflates the *mechanism* (schema mode change) with the *clinical observation* (gradual behavioral resolution).

**Correct Approach (Interpolation):**

Introduce a **continuous accessibility factor** that mediates between binary schema mode and behavioral output:

```julia
# New factor: schema_access ∈ {Implicit(α=0), Partial(α=0.5), Explicit(α=1)}
#
# A1 (context_cues) = (1-α) * A_modular + α * A_integrated
# D1 (context_prior) = (1-α) * D_modular + α * D_integrated
#
# This preserves mechanism (gating) while allowing gradual unfolding
```

**Mathematical Formulation:**

For any gated matrix M (A or D):
```
M(α) = (1-α) * M_implicit + α * M_explicit

where:
  α = 0   → fully modular (context-blind)
  α = 0.5 → partial access (sometimes context-sensitive)
  α = 1   → fully integrated (always context-sensitive)
```

**Julia Implementation Pattern:**
```julia
function interpolate_A1(A_modular, A_integrated, alpha)
    # Both A_modular and A_integrated are 3×3×4×2×2 tensors
    # A_modular has uniform context_cues (can't distinguish safe/ambiguous/danger)
    # A_integrated has identity mapping (knows exact context)

    return (1 - alpha) .* A_modular .+ alpha .* A_integrated
end

function get_agent_matrices(agent, access_level)
    alpha = access_level / 3  # Discrete 0, 0.5, 1 (if 3-state factor)

    A1 = interpolate_A1(agent.A1_modular, agent.A1_integrated, alpha)
    D1 = interpolate_D1(agent.D1_modular, agent.D1_integrated, alpha)

    return (A1, D1)
end
```

**Key Insight:** Interpolation is NOT the same as the binary state change. The state change is the mechanism; interpolation is how it manifests behaviorally.

### 1.2 The Scheduling Pattern

**Problem:** Once α increases from 0 → 1, what determines the *speed* of that transition?

**Solution:** Decouple accessibility from behavioral changes by introducing **precision annealing**.

**Pattern:**
```julia
# Phase 1: Low precision exploration (γ_min = 1.0)
# - High entropy in policy selection
# - Agent "explores" multiple action patterns
# - Discovers that approach sometimes leads to safe outcomes
# - Represents hypothesis testing ("Is this context really dangerous?")

# Phase 2: High precision exploitation (γ_max = 8.0)
# - Low entropy in policy selection
# - Agent commits to context-appropriate actions
# - Represents consolidation of learning

function get_precision_schedule(access_level)
    alpha = access_level / 3
    gamma_min = 1.0
    gamma_max = 8.0

    # Linear interpolation: low precision when implicit, high when explicit
    gamma = gamma_min + (gamma_max - gamma_min) * alpha

    return gamma
end
```

**Why This Works:**
- **Simulated annealing explanation:** Decreasing γ early allows exploration of bad actions; increasing γ later exploits good discoveries
- **Clinical mapping:** Early Discovery phase = confused, tries multiple interpretations; Late phase = confident in new understanding
- **Non-cheating:** The precision change is *derived from* accessibility, not independent

### 1.3 The Stochastic Scaffolding Pattern

**Problem:** Not all clients reach explicit understanding. Clinical outcome distributions are non-deterministic.

**Solution:** Make transitions stochastic rather than deterministic.

**Pattern:**
```julia
function update_accessibility(current_alpha, therapist_effort, variability=0.1)
    # Drift: therapist interventions push toward higher α
    drift = therapist_effort * 0.01

    # Noise: client-specific factors create stochasticity
    noise = randn() * variability

    new_alpha = min(1.0, max(0.0, current_alpha + drift + noise))
    return new_alpha
end

# Results from 50 replications:
# - 85% reach explicit (fast scaffolding)
# - 65% reach explicit (standard)
# - 55% reach explicit (slow)
# This matches clinical heterogeneity
```

**Verification:**
```julia
@test 0.30 < fraction_reaching_explicit < 0.95  # Biologically plausible range
@test mean_time_to_explicit_fast < mean_time_to_explicit_slow
```

---

## Part 2: When to Consult External Experts (Codex)

### 2.1 Diagnostic Triggers

**Consult an architect when:**

| Symptom | Example from Chamberlin | What to Ask |
|---------|--------------------------|------------|
| **2+ failed attempts** | First tried dual-models, then hierarchical models, then modularity-breaking | "What am I missing architecturally?" |
| **Tradeoff paralysis** | 3-state vs 2-state schema_mode: implicit/explicit/labile vs modular/integrated | "What's the simplest design that still captures the phenomenon?" |
| **Confusing mechanisms** | Instant behavioral change vs gradual unfolding | "How do I model the mechanism separately from the process?" |
| **Library gaps** | Couldn't find gated learning in active inference literature | "Is this a library limitation or a design problem?" |

### 2.2 The Codex Architect Review (Chamberlin Case Study)

**Timeline:**
- **Day 1:** Completed 3-state schema_mode design (implicit/explicit/labile)
- **Outcome:** Worked perfectly on paper
- **Problem (Not Obvious):** Schema mode was doing *too much* - simultaneously gating learning AND changing policies AND affecting observations
- **Consultation:** "This is over-engineered. Can you simplify?"
- **Recommendation:** Binary mode (modular/integrated) + separate accessibility factor (0/0.5/1)
- **Result:** 80% less complexity, all tests still pass

**What Changed:**

Before (Over-engineered):
```julia
# 3-state schema_mode handles:
# 1. Learning enablement (implicit=no, explicit/labile=yes)
# 2. Metacognitive access (implicit=no, explicit/labile=yes)
# 3. Policy selection basis (implicit=marginal, explicit=conditioned)
# 4. Transition dynamics (implicit→explicit→labile→explicit)
# TOTAL: 4 concerns in 1 factor ❌
```

After (Recommended):
```julia
# 2-state schema_mode handles ONLY:
# 1. Mechanism: Context-sensitivity gating (modular vs integrated)
#
# 1-state accessibility factor handles:
# 2. Process: Gradual unfolding (0 → 0.5 → 1)
#
# Precision schedule handles:
# 3. Behavioral dynamics: Exploration → Exploitation
# TOTAL: Each factor has single concern ✓
```

**Decision Framework Used by Architect:**

1. **Identify conflated concerns** - Does this factor do multiple unrelated jobs?
2. **Separate by mechanism type** - State changes vs continuous processes
3. **Minimal sufficient complexity** - Could this work with fewer states?
4. **Test each level** - Can I remove a factor and still pass tests?

### 2.3 When NOT to Consult

- Simple syntax/API questions (use docs)
- First attempt at a feature (try 2-3x first)
- Trivial bugs (rubber duck debugging)
- Established patterns you recognize (reuse)

---

## Part 3: Warning Signs of Over-Complexity

### 3.1 The "Cheat" Detector Checklist

**Definition of a "cheat":** A model that produces correct behavioral predictions but does so through an interpretively unrealistic mechanism.

**Example from Chamberlin:**
```julia
# This works empirically but is a cheat:
if schema_mode == MODULAR
    γ = 8.0  # High precision (exploitation)
else
    γ = 1.0  # Low precision (exploration)
end

# Problem: Why would the implicit schema have HIGH precision?
# - Precision should INCREASE as understanding increases
# - This reversal is not theoretically coherent
# - Even if it produces correct P(avoid) curves, it's interpretively wrong
```

**Why Cheats Matter:**
1. **Generalization fails** - Works for this setup, fails for variations
2. **Clinical interpretation breaks** - Can't explain why the model does this
3. **Predictions are fragile** - Small parameter changes reverse the effect

### 3.2 Complexity Red Flags

| Warning Sign | Example | How to Fix |
|--------------|---------|-----------|
| **Contradictory parameters** | Modular has high precision + low learning | Separate the concerns (cheat alert) |
| **State factor does >3 things** | schema_mode: gates learning, affects observations, controls transitions | Split into multiple factors |
| **Special casing** | "When integrated, do X; when modular, do Y" in 5+ places | Consider gating parameter instead |
| **Magic numbers** | Why does this threshold equal 0.5 and not 0.7? | Should come from theory, not fitting |
| **Asymmetric dynamics** | Implicit→Explicit fast; Explicit→Implicit never | Justify asymmetry from mechanism |

### 3.3 Complexity Score (Self-Assessment)

**Calculate your model's complexity budget:**

```
Complexity = (# State Factors) × (mean # States per factor) × (# Outcome Modalities) × (# Learnable Parameters)

For Chamberlin:
  State factors: 4 (context, action, threat, schema_mode)
  States: 3, 4, 2, 2 (avg = 2.75)
  Outcome modalities: 4
  Learnable params: 1 (D3 only)

  Complexity = 4 × 2.75 × 4 × 1 = 44

  Budget for paper reproduction: ~30-60 ✓ ACCEPTABLE
  Budget for new phenomena: ~100+ might need delegation
```

If complexity > 80, ask: "Can any factors be merged?" or "Can any outcomes be removed?"

---

## Part 4: Test Design Principles

### 4.1 The Test Hierarchy

**Tier 1: Mechanism Tests** (Tests 1, 4, 6)
- Verify the core claim without worrying about behavioral dynamics
- Example: "Does modular mode block learning?" (yes → D3 unchanged)
- Pass rate target: 95%+ (these must be rock-solid)

**Tier 2: Behavioral Tests** (Tests 2, 3, 5, 7)
- Verify that predicted behavior emerges from mechanism
- Example: "Is P(avoid) change sharp or gradual?"
- Pass rate target: 85%+ (some variance expected)

**Tier 3: Comparative Tests** (Test 8 - Bayes Factors)
- Verify that observed dynamics favor your model over alternatives
- Example: "Does step-function fit better than sigmoid?"
- Pass rate target: 80%+ (requires careful model specification)

### 4.2 Quantitative Thresholds (Chamberlin Example)

**Test 1: Baseline maintains avoidance**
```julia
@test mean(p_avoid_trials_51_100) > 0.9
# Threshold rationale:
#   - In modular mode, should avoid regardless of context
#   - >0.9 shows strong, persistent behavior
#   - <0.9 suggests unintended learning leaked through
```

**Test 3: CT shows step function**
```julia
@test change_magnitude > 0.7          # Δ from ~0.96 to ~0.03
@test change_timing in 48:54          # Within ±3 of intervention (trial 51)
@test change_width < 5                # Rapid, not gradual
# Thresholds derived from:
#   - Paper prediction: "immediate cessation"
#   - Statistical significance: Δ > 0.7 = large effect (Cohen's d > 2)
#   - Window: ±3 allows for measurement noise, not indefinite grace period
```

**Test 7: Large effect size**
```julia
ct_pre = [mean(p_avoid[1:50]) for rep in replications]
ct_post = [mean(p_avoid[51:100]) for rep in replications]
d = cohens_d(ct_pre, ct_post)
@test d > 2.0
# Threshold: Cohen's d > 2.0 is "very large" effect
# Alternative would be < 1.0 (which would be weak for therapy)
```

### 4.3 Test Design Anti-Patterns

**Anti-Pattern 1: Moving the Goalposts**
```julia
# WRONG: After implementation, if you're not getting 0.7, drop to 0.5
@test change_magnitude > 0.5  # ❌ Should be pre-registered as 0.7

# RIGHT: Specify before implementing
# Document why 0.7 (not 0.5 or 0.9)
```

**Anti-Pattern 2: Ignoring Variance**
```julia
# WRONG: Using single run
result = run_simulation()
@test result.p_avoid_end < 0.1  # ❌ Vulnerable to noise

# RIGHT: Aggregate across replications
results = run_simulation(n_replications=50)
mean_p_avoid_end = mean([r.p_avoid_end for r in results])
@test mean_p_avoid_end < 0.1
```

**Anti-Pattern 3: Too Many Tests (Over-Fitting)**
```julia
# WRONG: 20 tests designed to make your model pass
# If any of N tests fail, you're likely over-fitting to data

# RIGHT: 5-7 core tests derived from theory predictions
# Each test addresses a distinct claim from the paper
```

### 4.4 Designing Tests for New Phenomena

**Template: Theory → Prediction → Test → Threshold**

```julia
# THEORY (from Chamberlin paper, p3)
# "Discovery alone results in resolution in >50% of cases"

# PREDICTION (Active Inference interpretation)
# "Making schema explicit (α=1) should reduce P(avoid)
#  even without D-matrix updates"

# OPERATIONALIZATION (Discovery tests 1-3)
discovery_fast_config = DiscoveryConfig(
    initial_access = 0,
    scaffolding_rate = 0.02,
    variability = 0.05
)

# TEST (Tier 2 - Behavioral)
@test mean_p_avoid_explicit < 0.2  # When α=1
@test frac_reaching_explicit > 0.8 # Most clients reach it with scaffolding

# THRESHOLD JUSTIFICATION
# - <0.2: Matches paper's claim of "cessation"
# - >0.8: Shows scaffolding is effective
# - Pre-registered before seeing data
```

### 4.5 Handling Test Failures

**When a test fails, use this decision tree:**

```
1. Is this a MECHANISM test (Tier 1)?
   ├─ YES: Stop. Fix the core model. Don't proceed with other tests.
   └─ NO: Continue to 2.

2. Is the failure within 5% of threshold?
   ├─ YES: Increase replications. It's likely noise.
   └─ NO: Continue to 3.

3. Did you implement it correctly?
   ├─ UNCERTAIN: Print the actual value. Visually inspect plots.
   ├─ NO: Fix implementation.
   └─ YES: Continue to 4.

4. Is this failure informative about the model?
   ├─ YES: Document it in learnings.md. Consider model revision.
   └─ NO: Check if threshold was realistic. May need adjustment (rare).
```

### 4.6 Regression Testing

Once a model passes all tests, protect it:

```julia
function test_chamberlin_regression()
    """Ensure future changes don't break core predictions."""

    baseline = run_chamberlin_2022(n_replications=50)

    # Core tests must remain passing
    @test all(baseline.tests_passed[1:7])  # Original 7 tests

    # Numerical stability check
    @test abs(baseline.ct_mean_p_avoid_end - 0.03) < 0.02
end

# Run this whenever you modify:
# - A1 or D1 matrices
# - Context-blind policy evaluation
# - Learning rate gating
```

---

## Part 5: Documentation & Knowledge Transfer

### 5.1 What to Document in Learnings.md

**Template:**

```markdown
## Design Iteration N

### Problem Encountered
[One sentence summary]

### Initial Approach
[What you tried]

### Why It Failed
[The specific mechanism that broke]

### Root Cause
[The deeper issue - was it architecture, spec, or theory?]

### Solution
[What you changed]

### Code Example
[Before/after code snippet]

### Lesson for Next Modeler
[Actionable insight for future work]

### Verification
[How you confirmed the fix worked]
```

**Example from Chamberlin:**

```markdown
## Design Iteration 2

### Problem Encountered
D1 (context prior) was uniform in modular mode, causing weak avoidance.

### Initial Approach
Set D1 only by schema_mode; keep A1 uniform to enforce "context-blindness."

### Why It Failed
A1 uniform → no information gain from observations (correct)
D1 uniform → agent has no prior belief about context either
Result: Conflicting priors + observations = no strong behavior

### Root Cause
Confounded two separate mechanisms:
- "Can't process observations" (A1 uniform) ✓
- "Doesn't know context initially" (D1 should be fearful, not uniform)

### Solution
D1 context prior must ALSO differ by schema mode:
- Modular: D1 = [0.1, 0.3, 0.6] (fearful, ambiguous)
- Integrated: D1 = [0.01, 0.01, 0.98] (accurate, knows safe)

### Code Example
```julia
# BEFORE (wrong)
if schema_mode == MODULAR
    A1 = uniform  # Can't see context
    D1 = uniform  # (BUG) No prior either
else
    A1 = identity
    D1 = accurate
end

# AFTER (correct)
if schema_mode == MODULAR
    A1 = uniform                     # Can't process observations
    D1 = [0.1, 0.3, 0.6]           # Fearful/defensive prior
else
    A1 = identity                    # Can process observations
    D1 = [0.01, 0.01, 0.98]        # Accurate/informed prior
end
```

### Lesson for Next Modeler
When gating a matrix by state, ask: "What property is being gated?"
- Observation likelihood (A): gates information flow
- Prior (D): gates initial assumptions
- These are DIFFERENT concerns and may need different values

### Verification
- Test 6 now passes: P(avoid) in modular mode → 0.96 (was 0.37)
- All 7 original tests pass after fix
```

### 5.2 The README Evolution

**For paper reproductions, document these milestones:**

```markdown
# Chamberlin 2022: Coherence Therapy Active Inference Model

## Status Timeline

**[Date] Initial Design Complete**
- 4 state factors, 4 outcome modalities
- Context-blindness gating mechanism
- Learning disabled in modular mode
- Estimated effort: 2-3 days (actual: 1 day)

**[Date] Implementation Phase 1**
- All A/B/C/D matrices constructed
- Basic trial loop working
- 4/7 tests passing
- Blocker: Incorrect D1 in modular mode (Issue #XX)

**[Date] Architect Review**
- Consulted on 3-state schema_mode design
- Recommended: Binary mode + separate accessibility factor
- Simplified from 28 LOC control logic → 8 LOC
- Cost: 2 hours, saved 10+ hours of debugging

**[Date] All Tests Passing**
- 7/7 original tests pass with 30 replications
- Matches paper's predicted behavior

**[Date] Discovery Extension**
- Added gradual accessibility (α: 0 → 0.5 → 1)
- Implemented precision annealing schedule
- 7/7 new Discovery tests pass
- Total complexity maintained (not compounding)
```

---

## Part 6: Practical Checklist for New Modelers

### Before You Start

- [ ] **Read the paper 2x** - First pass for overview, second for mechanism details
- [ ] **Identify the core claim** - What would falsify this model? (If unclear, clarify first)
- [ ] **Check library capabilities** - Can existing library do what you need? (If not, plan for it)
- [ ] **Pre-register tests** - Thresholds/criteria defined BEFORE implementation

### During Design

- [ ] **Draw state diagrams** - All factors, transitions, and observations on paper
- [ ] **Specify matrices explicitly** - A/B/C/D matrices with real numbers, not placeholders
- [ ] **Identify gated components** - What changes between conditions? (Usually just 1-2 factors)
- [ ] **Check for conflation** - Does any factor do >3 jobs? If yes, split it
- [ ] **Separate mechanism from process** - Binary state change vs continuous unfolding

### During Implementation

- [ ] **Test matrix algebra first** - Verify A, B, C, D shapes and sums before full simulation
- [ ] **Test single trial** - Before running 100 trials, test one at a time with prints
- [ ] **Test single condition** - Verify baseline works before adding therapy conditions
- [ ] **Check for unintended learning** - Does D change when it shouldn't? (Use assertions)
- [ ] **Visualize early** - Plot P(avoid) trajectory after first 5 replication

### Verification

- [ ] **Run Tier 1 tests first** - Mechanism tests must pass before behavioral tests
- [ ] **Check effect sizes** - Not just "significant," but "practically large"
- [ ] **Visual inspection** - Do plots match theory predictions (not just numbers)?
- [ ] **Sensitivity analysis** - How do small parameter changes affect results?
- [ ] **Regression test** - Create a permanent test suite to prevent regressions

### Documentation

- [ ] **Learnings.md completed** - Document each design decision and lesson
- [ ] **README updated** - Status, timeline, how to run, how to interpret
- [ ] **Code commented** - Why this value? Where does it come from?
- [ ] **Figures documented** - What does each figure show? How to interpret?

---

## Part 7: Common Pitfalls & How to Avoid Them

### 7.1 The Instant vs Gradual Confusion

**Pitfall:** You model instant mechanism change (binary state flip) but paper predicts gradual behavioral change.

**Red Flags:**
- Test shows P(avoid) drops from 0.96 to 0.03 in a single trial
- Paper says "takes weeks" for behavioral change
- You rationalize with "Well, the mechanism is instant, the process is gradual"

**Fix:**
1. **Interpolate** - Add continuous accessibility factor between binary states
2. **Test separately** - Verify mechanism test (binary change) and behavioral test (gradual unfolding) independently
3. **Document the distinction** - Clearly separate mechanism (A1 gating) from process (precision annealing)

### 7.2 The Parameter Tuning Trap

**Pitfall:** You have 10 free parameters and 7 tests; you adjust parameters until tests pass.

**Red Flags:**
- Tests pass only after "optimizing" parameters
- Small changes to one parameter break multiple tests
- You can't explain why this value is 0.5 instead of 0.7

**Fix:**
1. **Pre-specify parameters** - Decide values BEFORE running simulation
2. **Derive from theory** - Where does each number come from? (Paper, prior work, first principles)
3. **Treat parameters as fixed** - Only adjust if fundamental misunderstanding found
4. **Sensitivity analysis** - Show that results hold over ±10% parameter range

### 7.3 The State Explosion Problem

**Pitfall:** You add one new factor to model a single phenomenon, but it creates 3-4 new state combinations.

**Red Flags:**
- State space grows from 12 → 48 combinations
- You're using <20% of state combinations in simulation
- You can't manually enumerate all A matrix entries

**Fix:**
1. **Ask: Is this a state factor or a parameter?** - Can it be continuous or gated?
   - State factor: Creates new observations/transitions
   - Gated parameter: Affects computation, not state
2. **Use gating instead** - `α * A_explicit + (1-α) * A_implicit` instead of 3-state factor
3. **Aggressive elimination** - If a state is never visited, remove it

### 7.4 The Learning Rate Ambiguity

**Pitfall:** You set η=0 in modular mode, but it's unclear whether learning is "disabled" or "zero" due to other factors.

**Red Flags:**
- Test says "D3 unchanged" but you're not 100% sure if it's the zero learning rate or something else
- If you set η=0.5 in modular mode, does D3 still not update? (It should, if there's no other blocking)

**Fix:**
1. **Add mechanism test** - Explicitly test learning rate gating:
   ```julia
   # In modular mode with η=0.5 (forced high learning)
   @test D3_final ≈ D3_initial  # Should still be protected

   # In integrated mode with η=0.0 (forced no learning)
   @test D3_final ≈ D3_initial  # Should be frozen
   ```
2. **Document the hierarchy** - Is learning blocked by: schema_mode? state conditional rate? both?
3. **Test interaction** - What if both are present? Which takes precedence?

### 7.5 The Replication Bias

**Pitfall:** You run 30 replications and report means; you don't check variance or outliers.

**Red Flags:**
- P(avoid) shows mean=0.5 but std=0.6 (bimodal distribution)
- One replication has P(avoid)=0.0, others have 0.5 (outlier)
- Tests pass "on average" but fail in 20% of replications

**Fix:**
1. **Report full distribution** - Not just mean, also percentiles (25th, 75th)
2. **Visualize with confidence bands** - Plot mean ± 1.96*SE as gray ribbon
3. **Check for bimodality** - If some replications diverge wildly, it's a sign of instability
4. **Increase replications if high variance** - If std > 0.1, run 50-100 reps, not 30

---

## Part 8: When to Extend vs When to Stop

### 8.1 The Extension Decision Tree

After implementing a model that passes all tests, you might want to extend it. Use this framework:

```
Do you have evidence that the original model is missing something?
├─ NO: STOP. Document what you built. It's complete.
└─ YES: Continue to next question.

Did you consult the paper AND an external expert (Codex)?
├─ NO: Do that first. Don't extend based on intuition alone.
└─ YES: Continue.

Can you describe the new phenomenon in 1-2 sentences?
├─ NO: Your idea is not clear. Stop and clarify.
└─ YES: Continue.

Can you design a test that would FAIL if the extension is wrong?
├─ NO: The extension is unfalsifiable. Don't implement it.
└─ YES: You're ready to extend.
```

### 8.2 The Chamberlin Discovery Extension

**Was it justified?**

```
1. Evidence of missing something?
   ✓ YES - Paper says "takes time," model shows instant change

2. Consulted experts?
   ✓ YES - Codex Architect recommended against nested agents,
           suggested interpolation + annealing

3. Clear description?
   ✓ YES - "Model discovery as gradual accessibility (α: 0→1)
            plus precision annealing (γ: 1→8)"

4. Testable hypothesis?
   ✓ YES - "Access level predicts P(avoid) with r < -0.3"
```

**Result:** Extension added 7 more tests, all passed. Original 7 tests still passed. Complexity increased modestly (1 new factor, 1 new schedule).

### 8.3 When to Stop Extending

**Red flags that you've over-extended:**

| Warning | Example | What to Do |
|---------|---------|-----------|
| Original tests start failing | Precision schedule breaks baseline test | Revert change, separate concerns |
| Complexity scoring > 100 | Added therapist agent, now intractable | Remove therapist, keep simple |
| Can't explain a parameter | Why is γ_max=8 not 9? | Pre-register all parameters |
| New extension not tested | Added multi-schema support, no tests | Don't merge until tested |

**Golden rule:** If extending a model breaks the original tests or requires explaining new magic numbers, revert and simplify.

---

## Part 9: The Chamberlin 2022 Incident Log

### Bug 1: Incorrect D1 in Modular Mode (Critical)

**What happened:**
- D1 was uniform in both modular and integrated modes
- Expected: Modular mode P(avoid) ≈ 0.96, Got: ≈ 0.37
- Test failed: "Baseline maintains avoidance"

**Root cause:**
- Conflated "can't process observations" with "has no prior"
- A1 uniform + D1 uniform = weak behavior (no information source)

**Fix:**
- D1_modular = [0.1, 0.3, 0.6] (fearful)
- D1_integrated = [0.01, 0.01, 0.98] (accurate)

**Lesson:** When gating a matrix, ask separately what each element should do.

### Bug 2: Learning Rate Applied in Both Modular and Integrated (Medium)

**What happened:**
- Test 6 failed: "Modular blocks learning"
- D3 changed even in modular mode

**Root cause:**
- Set η=0 in modular mode, but forgot to check it in inference loop
- Inference code was using a global η_base instead

**Fix:**
- Wrapper function: `get_learning_rate(schema_mode)` called before D updates
- Assertion: `@assert eta == 0 if schema_mode == MODULAR`

**Lesson:** When you gate a parameter, add assertions to catch leaks.

### Bug 3: Instant Behavior Change Doesn't Match Paper (Design)

**What happened:**
- Tests passed (P(avoid) drops from 0.96 to 0.03 at trial 51)
- But paper says Discovery "takes time"
- Consultant flagged: "This is a mechanism change, not a process. Is your model capturing gradual discovery?"

**Root cause:**
- Mechanism (schema_mode flip) ≠ Process (behavioral change)
- Model was correct about mechanism, but missing process layer

**Fix:**
- Added schema_access factor (0 to 1)
- Added precision schedule (1 to 8)
- Separated concerns explicitly

**Lesson:** Passing tests doesn't mean the model is right. Match mechanisms to theory.

---

## Part 10: Generalization to Other Active Inference Projects

The lessons from Chamberlin 2022 apply broadly:

### For Hierarchical Models
- **Don't conflate levels** - Separate computational hierarchy from conceptual hierarchy
- **Test each level independently** - Verify low level before building high level
- **Document the cascade** - How do high-level decisions propagate?

### For Multi-Agent Models
- **Agent-environment separation** - Don't mix agent learning with environment dynamics
- **Explicit communication protocol** - How do agents exchange information? Pre-specify it
- **Test dyadic stability** - Does the system reach steady state? How sensitive to initial conditions?

### For Parameter Learning Models
- **Pre-specify learning rates** - Don't tune η to make tests pass
- **Verify learning signal** - Is the prediction error actually large when you expect it?
- **Check convergence** - Parameter learning should stabilize, not oscillate

### For Novel Phenomena
- **Simple first** - Model the phenomenon with minimal apparatus
- **Architect review** - After 2 failed attempts, consult an expert
- **Test before publishing** - More tests = more robust knowledge

---

## Appendix: Quick Reference Checklist

### Design Phase
- [ ] State diagram drawn and reviewed
- [ ] Matrix dimensions verified (shapes match)
- [ ] Gating mechanism identified and isolated
- [ ] Mechanism vs process separated
- [ ] Architect consulted? (If complexity > 60)

### Implementation Phase
- [ ] Matrices explicitly constructed with real numbers
- [ ] Single-trial test passes
- [ ] Single-condition test passes
- [ ] All 4 conditions run without errors
- [ ] Visualizations show expected pattern

### Verification Phase
- [ ] Tier 1 tests (mechanism): 100% pass
- [ ] Tier 2 tests (behavioral): 85%+ pass
- [ ] Tier 3 tests (comparative): 80%+ pass
- [ ] All tests pre-registered (not fit post-hoc)
- [ ] Sensitivity analysis: ±10% parameter range acceptable

### Documentation Phase
- [ ] Learnings.md completed (each design iteration)
- [ ] README updated (status, timeline, results)
- [ ] Code comments explain parameters and thresholds
- [ ] Figures have captions explaining what they show
- [ ] Regression test created (prevent future breakage)

---

## References

**Chamberlin 2022:** "The Active Inference Model of Coherence Therapy"
- Paper: fnhum-16-955558.pdf
- Hypothesis: Modularity-breaking (not belief updating) is therapeutic mechanism
- Test: ST function vs sigmoid learning curves

**Smith 2021:** "Active Inference and Trauma" (CBT comparison)
- Used as baseline to contrast with CT
- Shows gradual belief updating vs instant behavior change

**Ecker et al. 2012:** Coherence Therapy (clinical work, not active inference)
- Source of "Discovery," "Juxtaposition," "Reconsolidation" concepts
- Clinical validation that CT is distinct from CBT

**Codex Architect Consultation:** Design phase review (2026-01-28)
- Recommended: Binary mode + separate accessibility factor
- Saved ~10 hours of iteration

---

**Document Version:** 1.0
**Last Updated:** 2026-01-30
**Author:** Research Team (synthesized from learnings.md, task_spec.md, model_design.md)
**Status:** Complete
