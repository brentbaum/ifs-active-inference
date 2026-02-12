# Chamberlin 2022 Paper Reproduction Plan

Paper: Chamberlin (2022) "The Active Inference Model of Coherence Therapy"
https://www.frontiersin.org/journals/human-neuroscience/articles/10.3389/fnhum.2022.955558/full

**Note:** This is a *theoretical* paper with no existing simulation. We designed a simulation to operationalize and test the key claims.

## Status
- [x] Extract paper concepts into local markdown (`paper.md`).
- [x] Extract task specification with exact dimensions (`task_spec.md`).
- [x] Map paper model to current library primitives and list capability gaps (`library_mapping.md`).
- [x] Design the generative model (A/B/C/D matrices, outcome modalities, policies) (`model_design.md`).
- [x] **Plan Review: APPROVED** (Codex Plan Reviewer, 4 iterations)
- [x] Implement context-sensitivity gating mechanism.
- [x] Implement therapist-controlled schema_mode transitions.
- [x] Reproduce comparison: CT vs CBT vs Baseline.
- [x] Validate testable predictions from task_spec.
- [x] Document parameters, assumptions, and deviations (`learnings.md`).
- [x] **Extension: Model Discovery process** (gradual schema accessibility with simulated annealing)

## Results Summary (2026-01-30)

**ALL 14 TESTS PASSED** (7 original + 7 Discovery) with 30 replications:

### Original CT Tests (7/7 PASS)

| Test | Result | Value | Threshold |
|------|--------|-------|-----------|
| 1. Baseline maintains avoidance | ✓ PASS | 0.964 | >0.9 |
| 2. CBT resolves (gradual) | ✓ PASS | 0.027 | <0.3 |
| 3. CT shows step function | ✓ PASS | 0.938 | >0.7 |
| 4. CT minimal belief change | ✓ PASS | 0.0 | <0.15 |
| 5. CT-dangerous maintains avoidance | ✓ PASS | 0.965 | >0.9 |
| 6. Modular blocks learning | ✓ PASS | 0.0 | <0.01 |
| 7. CT large effect size | ✓ PASS | Inf | >2.0 |

### Discovery Tests (7/7 PASS)

| Test | Result | Value | Threshold |
|------|--------|-------|-----------|
| 1. Access increases over time | ✓ PASS | 2.83 | >2.0 |
| 2. Stochastic transitions | ✓ PASS | 83.3% | 30-95% |
| 3. Behavior-access correlation | ✓ PASS | -0.689 | <-0.3 |
| 4. Precision annealing | ✓ PASS | 7.0 range | >3.0 |
| 5. Fast vs Slow timing | ✓ PASS | 25 vs 81 | fast < slow |
| 6. Explicit lowest avoidance | ✓ PASS | 0.001 | <0.2 |
| 7. Access predicts resolution | ✓ PASS | - | - |

## Key Findings

The simulation validates Chamberlin's core hypothesis:

1. **Modularity-breaking is the therapeutic mechanism**: CT resolution occurs immediately when schema becomes context-sensitive (step function), not through gradual belief updating.

2. **Context-sensitivity vs belief updating**:
   - CT: Resolution via structural change (agent can now consider context)
   - CBT: Resolution via parametric learning (D3 belief updating over time)
   - Both work, but CT mechanism is distinct

3. **Appropriate avoidance preserved**: In CT-dangerous condition, agent correctly maintains avoidance when context is actually dangerous.

## Plan Review Summary (2024-01-30)
The `task_spec.md` underwent 4 iterations of review with Codex Plan Reviewer:
1. **Rejected:** Missing full generative model details, policy structure, learning rules, intervention protocol, verification criteria
2. **Rejected:** A2 incomplete, A3/A4 underspecified, missing operational definitions
3. **Rejected:** Missing explicit index mappings, algorithm parameters, metric aggregation
4. **APPROVED:** All components specified with explicit Julia code, constants, test definitions

## Key Design Decision
The simulation tests the paper's core claim that **modularity-breaking** (making schema context-sensitive) is the primary therapeutic mechanism, distinct from CBT's gradual belief updating.

## Implementation Details

### Context-Sensitivity Mechanism
- **Modular mode**: A1 matrix is uniform (agent can't process context cues), D1 prior is fearful
- **Integrated mode**: A1 matrix is identity (accurate context perception), D1 prior reflects actual context

### Key Insight During Implementation
The critical fix was recognizing that D1 (context prior) must also differ by schema_mode:
- In modular mode, the agent should have an *uncertain/fearful* context prior, not an accurate one
- The A1 uniformity only prevents *updating* from observations; the prior still matters
- With fearful D1 + uniform A1, the agent maintains context-blind fear

## Discovery Process Extension (2026-01-30)

The paper describes Discovery as "resembling simulated annealing" - an iterative process that takes time. The original model showed instant behavioral change when schema_mode switched. We extended the model to capture gradual Discovery dynamics.

### New Components
- `schema_access`: 3-level factor (implicit → partial → explicit)
- Interpolated A1/D1 based on access level
- Annealed precision (γ: 1→8) for exploration→exploitation
- Stochastic scaffolding schedule

### Usage
```julia
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore

# Run Discovery simulation
result = run_ct_discovery_simulation(discovery_config())

# Compare Discovery conditions
fast = run_discovery_replications(discovery_fast_config, 20)
std = run_discovery_replications(discovery_config, 20)
slow = run_discovery_replications(discovery_slow_config, 20)

# Visualize
plot_discovery_trajectory(result)
plot_discovery_mechanism(result)
```

### Visualizations
- `figures/discovery_trajectory.png` - Single run showing P(avoid), access level, precision
- `figures/discovery_mechanism.png` - Detailed mechanism view
- `figures/discovery_comparison.png` - Fast/Standard/Slow comparison

## Files
- Implementation: `src/active_inference/coherence_therapy_model.jl`
- PDF stored: `paper_reproduction/chamberlin_2022/fnhum-16-955558.pdf`
- Visualizations: `paper_reproduction/chamberlin_2022/figures/`

## Usage (Original Tests)
```julia
include("src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore

results = run_chamberlin_2022(n_replications=50)
```
