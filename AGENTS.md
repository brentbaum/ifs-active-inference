# Agent Instructions for IFS Active Inference

This file provides guidance for AI agents working on this codebase.

## Project Overview

Julia implementation of Active Inference models for computational psychiatry, focusing on:
- **Spider phobia exposure therapy** (Smith 2021)
- **Trust game social cognition** (Eckertal 2023)
- **Concept learning** (PMC7250191)
- **Coherence Therapy** (Chamberlin 2022)

## Repository Structure (PARA)

```
ifs-active-inference/
├── projects/
│   ├── library/                        # Julia package (active inference engine)
│   │   ├── Project.toml
│   │   ├── Manifest.toml
│   │   ├── src/
│   │   │   ├── IFSActiveInference.jl
│   │   │   ├── active_inference/
│   │   │   │   ├── ActiveInferenceCore.jl   # Main module
│   │   │   │   ├── core.jl                  # Types and utilities
│   │   │   │   ├── inference.jl             # State inference
│   │   │   │   ├── efe.jl                   # Expected Free Energy
│   │   │   │   ├── policy.jl                # Policy inference
│   │   │   │   ├── learning.jl              # Dirichlet learning
│   │   │   │   ├── agent.jl                 # Agent loop
│   │   │   │   ├── spider_model.jl          # Smith 2021
│   │   │   │   ├── trust_game.jl            # Eckertal 2023
│   │   │   │   ├── concepts_model.jl        # PMC7250191
│   │   │   │   ├── coherence_therapy_model.jl # Chamberlin 2022
│   │   │   │   └── visualization.jl         # Plotting
│   │   │   └── ...
│   │   ├── test/
│   │   └── scripts/
│   │
│   ├── ifs-paper/                      # Novel IFS-Active Inference paper
│   │   ├── outline-v1.md
│   │   ├── claims.md
│   │   └── draft-critique.md
│   │
│   └── reproductions/                  # Paper reproductions
│       ├── chamberlin_2022/            # Most documented
│       ├── smith_2021/
│       ├── eckertal_2023/
│       └── pmc7250191/
│
├── resources/                          # Reference material
│   ├── papers/                         # Literature being read
│   ├── glossary.md                     # Key terms
│   ├── learning_notes.md               # Study notes
│   └── docs/
│       ├── concepts/
│       ├── guides/
│       └── solutions/                  # Knowledge base
│
├── archive/                            # Completed/inactive work
│   ├── library-validation/             # Completed validation phase
│   ├── results/                        # Old simulation outputs
│   ├── superseded/                     # Old plans and specs
│   └── figures/                        # Generated plots
│
├── README.md
└── AGENTS.md                           # ← You are here
```

## Before Starting Work

### Check Existing Learnings

**IMPORTANT**: Before implementing new features or fixing issues, check the documented learnings:

1. **Solution Knowledge Base**: `resources/docs/solutions/INDEX.md`
   - Searchable by category, component, and tags
   - Contains root cause analysis and verified solutions

2. **Design Patterns & Best Practices**: `resources/docs/guides/LEARNINGS_INDEX.md`
   - Navigation guide to all knowledge artifacts
   - Common pitfalls and how to avoid them
   - When to consult external experts

3. **Paper-Specific Learnings**: `projects/reproductions/[paper]/learnings.md`
   - Design decisions and bugs encountered for each reproduction

### Key Insight from Chamberlin 2022

The most important lesson learned: **Both A1 (likelihood) AND D1 (prior) must be schema-mode-dependent**.

```julia
# WRONG: D1 accurate even in modular mode
D1 = [0.01, 0.01, 0.98]  # Knows context is safe

# CORRECT: D1 fearful in modular mode
if schema_mode == CT_SCHEMA_MODULAR
    D1 = [0.1, 0.3, 0.6]  # Bias toward dangerous
end
```

A trauma-formed schema assumes danger *because it was formed in danger*.

## Running the Julia Package

```bash
# From repo root:
julia --project=projects/library

# In REPL:
using Pkg; Pkg.instantiate()
```

### Chamberlin 2022 (14 tests)

```julia
include("projects/library/src/active_inference/ActiveInferenceCore.jl")
using .ActiveInferenceCore

# Run all 14 tests (7 original + 7 Discovery)
results = run_chamberlin_2022_full(n_replications=30)
```

### Quick Validation

```julia
# Just original CT tests
run_chamberlin_2022(n_replications=10)

# Just Discovery tests
run_chamberlin_2022_discovery(n_replications=10)
```

## Running Tests

```bash
julia --project=projects/library projects/library/test/runtests.jl
```

## Design Patterns

### 1. Interpolation Pattern (Gradual State Transitions)

When extending binary states to multi-level:

```julia
# α ∈ {0, 0.5, 1} for implicit/partial/explicit
A1 = (1-α) * A_modular + α * A_integrated
D1 = (1-α) * D_modular + α * D_integrated
```

### 2. Precision Annealing (Exploration → Exploitation)

```julia
γ = γ_min + (access_level - 1) / 2 * (γ_max - γ_min)
# γ_min = 1.0 (exploration), γ_max = 8.0 (exploitation)
```

### 3. Stochastic Scaffolding (Not All Reach Resolution)

```julia
if rand() < transition_probability
    schema_access += 1
end
# Results in 55-85% reaching explicit (matches clinical reality)
```

## When to Consult External Experts

Delegate to Codex Architect when:
- 2+ failed design attempts
- Architectural tradeoffs between approaches
- State explosion (>100 combinations)
- Mechanism vs process confusion

## Adding New Paper Reproductions

1. Create `projects/reproductions/[paper_name]/`
2. Add `PLAN.md`, `learnings.md`, `task_spec.md`
3. Implement in `projects/library/src/active_inference/[paper]_model.jl`
4. Export from `ActiveInferenceCore.jl`
5. Document solution in `resources/docs/solutions/[category]/`

## Common Mistakes to Avoid

1. **Don't** set D priors independent of gating mechanism
2. **Don't** tune parameters after seeing test results (pre-register)
3. **Don't** confuse instant mechanism with gradual behavioral change
4. **Do** check `resources/docs/guides/LEARNINGS_INDEX.md` before starting
5. **Do** run tests after any model changes
6. **Do** document learnings in `projects/reproductions/[paper]/learnings.md`

## Test Thresholds

| Test | Threshold | Rationale |
|------|-----------|-----------|
| Baseline maintains avoidance | P(avoid) > 0.9 | Modular must block learning |
| CT step function | Δ > 0.7 | Large effect at intervention |
| CT minimal belief change | D3 change < 0.15 | Resolution via context, not belief |
| Discovery access increases | mean > 2.5 | Most should reach explicit |
| Behavior-access correlation | r < -0.3 | Higher access → lower avoidance |

## Questions?

Check `resources/docs/guides/LEARNINGS_INDEX.md` for navigation to specific topics.
