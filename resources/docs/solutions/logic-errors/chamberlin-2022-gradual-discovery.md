---
# Solution Metadata for Documentation
# Problem type, component, and searchability tags for knowledge base

title: "Gradual Discovery Dynamics in Coherence Therapy Simulation"
problem_type: "model_behavior_validation"
severity: "medium"
status: "resolved"
date_resolved: "2026-01-30"

# Component affected by this problem/solution
component:
  module: "paper_reproduction"
  submodule: "chamberlin_2022"
  files:
    - "paper_reproduction/chamberlin_2022/simulation.jl"
    - "paper_reproduction/chamberlin_2022/test_discovery.jl"

# Symptoms that led to discovery of the issue
symptoms:
  - "Model showed instant behavioral change when schema_mode switched from modular to integrated"
  - "Paper describes Discovery as iterative process resembling simulated annealing"
  - "Clinical data shows behavioral change takes weeks, not single trial"
  - "Mismatch between theoretical description and implementation behavior"

# The core problem statement
problem: |
  The original Chamberlin 2022 coherence therapy simulation produced unrealistic instant
  behavioral change upon schema integration. The paper describes Discovery as a gradual,
  iterative process ("resembles simulated annealing") that requires scaffolding and takes
  time. However, the implementation showed step-function transitions at a single time point
  rather than gradual accessibility across multiple trials.

# Root cause analysis
root_cause: |
  Schema integration (schema_mode: modular → integrated) was modeled as a binary switch
  with immediate effect on both A1 (likelihood) and D1 (prior). The model lacked:
  1. Intermediate accessibility states between fully implicit and fully explicit
  2. Gradual interpolation mechanism for schema properties
  3. Exploration-exploitation dynamics during the discovery process

# Solution implemented
solution: |
  Extended the model with a 3-level schema_access factor (implicit → partial → explicit)
  that interpolates between modular and integrated states via convex combination:

  A1 = (1-α) * A_modular + α * A_integrated
  D1 = (1-α) * D_modular + α * D_integrated

  where α ∈ {0, 0.5, 1} represents accessibility level.

  Added precision annealing (γ: 1→8) to capture exploration→exploitation transition.
  Implemented stochastic scaffolding schedule with configurable discovery speed.

# Implementation details
implementation:
  approach: "hierarchical_interpolation"
  mechanism: "convex_combination_with_precision_annealing"
  key_parameters:
    - name: "schema_access"
      values: ["implicit (α=0)", "partial (α=0.5)", "explicit (α=1)"]
      description: "Continuous accessibility of schema to conscious processes"
    - name: "γ (precision)"
      range: "[1.0, 8.0]"
      description: "Inverse temperature for exploration-exploitation tradeoff"
    - name: "transition_schedule"
      type: "stochastic"
      description: "Probability distribution over trials for moving between access levels"

# Testing and validation
validation:
  test_count: 14
  pass_count: 14
  test_results:
    original_ct_tests: 7
    discovery_tests: 7
  key_tests:
    - "Access increases monotonically (mean 2.83 at end)"
    - "Stochastic transitions: 30-95% reach explicit state"
    - "Behavior-access correlation r < -0.3 (r = -0.689)"
    - "Precision annealing range > 3.0 (1.0→8.0)"
    - "Fast vs Slow timing: 25 vs 81 trials to explicit"
    - "Explicit access produces lowest avoidance (P(avoid) < 0.2)"

# Metrics that improved
metrics_improved:
  - name: "Realism of Discovery timeline"
    before: "Instant change at single trial"
    after: "Gradual 25-81 trials with stochastic variance"
  - name: "Final avoidance behavior"
    context: "Standard discovery"
    value: "P(avoid) = 0.16 (vs instant 0.03)"
    interpretation: "More realistic residual caution"
  - name: "Population coverage"
    metric: "% clients reaching explicit access"
    range: "55-85%"
    note: "Matches clinical heterogeneity"

# Design decisions documented
design_decisions:
  decision_1:
    question: "Should Discovery be modeled as separate therapist agent?"
    answer: "No - exogenous scaffolding schedule is sufficient"
    rationale: |
      Simpler than hierarchical active inference. Captures key dynamics
      (gradual accessibility with stochastic transitions). Can extend
      to dyadic model later if needed.

  decision_2:
    question: "Why interpolation rather than discrete transitions?"
    answer: "Allows modeling partial access and exploration-exploitation tradeoff"
    rationale: |
      Convex combination captures intermediate states where schema is
      sometimes accessible. Precision annealing captures iterative
      hypothesis-testing process described by paper.

# Tags for search/categorization
tags:
  - "coherence_therapy"
  - "schema_dynamics"
  - "discovery_process"
  - "model_realism"
  - "temporal_dynamics"
  - "stochastic_transitions"
  - "simulated_annealing"
  - "behavioral_dynamics"

# Related items in knowledge base
see_also:
  - "smith-2021-cbt-exposure-therapy"
  - "chamberlin-2022-context-sensitivity"
  - "precision_annealing_patterns"
  - "clinical_heterogeneity_modeling"

# References to paper and theory
references:
  - author: "Chamberlin"
    year: 2022
    title: "Coherence Therapy as Active Inference"
    key_quote: "Resembles simulated annealing - an iterative search process"

  - author: "Smith et al."
    year: 2021
    title: "Exposure Therapy as Active Inference"
    contrast: "CBT shows gradual parametric learning; CT shows step-function"

# Impact on reproducibility
impact:
  reproducibility: "High"
  generalizability: "Applies to any phased therapeutic intervention model"
  maintenance_burden: "Low - stochastic schedule is external to core simulation"
  extensibility: "Foundation for modeling therapist-client dyadic dynamics"

# Notes for future work
notes: |
  - Original 7 tests preserved and passing (backward compatibility)
  - Discovery tests are additional, not required
  - Stochastic transitions match clinical observation: not all clients
    reach full explicit access even with effective therapy
  - Precision annealing (γ scheduling) could be replaced with other
    exploration-exploitation schedules (e.g., softmax temperature decay)
  - Could model reconsolidation window (time-limited belief updating
    after reaching explicit access)

---

## Summary

This solution addresses the gap between theoretical description of Discovery in Chamberlin 2022's
Coherence Therapy model and the original implementation's unrealistic instant transitions.

**Problem**: Simulation showed step-function behavioral change at single time point, but paper
describes Discovery as gradual iterative process ("simulated annealing") taking weeks.

**Solution**: 3-level accessibility interpolation (implicit → partial → explicit) with
precision annealing. All 14 tests pass (7 original + 7 new Discovery tests).

**Impact**: Model now captures both instant step-function dynamics (original CT behavior) AND
gradual discovery timeline with stochastic heterogeneity (clinical observation).

See `/Users/brentbaum/dev/research/ifs-active-inference/paper_reproduction/chamberlin_2022/learnings.md`
for detailed implementation notes and design rationale.
