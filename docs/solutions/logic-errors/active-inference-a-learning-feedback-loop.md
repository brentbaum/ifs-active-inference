---
title: Feedback loop from shared A matrix between world model and agent beliefs
category: logic-errors
tags: [active-inference, rxinfer, feedback-loop, generative-model, recognition-model, exposure-therapy]
module: rxinfer_impl
symptoms:
  - "A learning causes beliefs to diverge instead of converge"
  - "Danger belief increases during exposure therapy with safe spider"
  - "Learned A beliefs affect observation generation creating self-reinforcing loop"
severity: high
created: 2026-02-02
---

# Feedback Loop from Shared A Matrix Between World Model and Agent Beliefs

## Problem

During exposure therapy simulation with a safe spider, danger beliefs **increased** from 0.5 to 0.9 instead of decreasing. The agent was learning the opposite of what it should learn from safe experiences.

### Symptoms

- A learning causes beliefs to diverge instead of converge toward truth
- Danger belief increases during exposure therapy with safe spider
- Agent avoids spider even after many safe exposures
- Learned A beliefs affect observation generation, creating self-reinforcing loop

## Root Cause

The bug arose from using a single `matrices.A` for both:

1. **Generating observations** from the environment (world model)
2. **State inference and learning** (agent beliefs)

This created a **self-reinforcing feedback loop**:

```
1. Agent observes fear (sampled from matrices.A)
2. Agent updates matrices.A to reinforce "this state produces fear"
3. Next observation is sampled from the now-modified matrices.A
4. Agent sees even more fear, reinforcing the belief further
5. Danger beliefs escalate (0.5 → 0.9) instead of decreasing
```

The agent was literally changing reality to match its fears, rather than learning that reality was different from its fears.

### The Fundamental Problem

In active inference, there must be separation between:

- **Generative Model (World)**: How the WORLD actually produces observations (fixed)
- **Recognition Model (Agent)**: Agent's BELIEFS about how observations are produced (learnable)

The buggy code used `matrices.A` for both, violating this separation.

## Solution

### Step 1: Create Separate Models at Initialization

```julia
# === SEPARATE GENERATIVE MODEL FROM RECOGNITION MODEL ===
# A_world: Fixed generative model - the TRUE observation likelihoods
#          Used ONLY for sampling observations from the environment
# A_agent: Learnable recognition model - agent's BELIEFS about P(o|s)
#          Used for state inference, EFE calculation, and updated via learning

A_world = deepcopy(matrices.A)  # Fixed - never modified during simulation

# Initialize Dirichlet priors for learning
a_priors = [copy(A_g) .+ 1.0 for A_g in matrices.A]

# A_agent: normalized beliefs derived from a_priors
A_agent = [a_priors[g] ./ sum(a_priors[g], dims=1) for g in 1:length(matrices.A)]
```

### Step 2: Use A_world for Observation Generation

```julia
# Generate observation using A_world (true generative model)
for g in 1:length(matrices.No)
    probs = A_world[g][:, true_state]  # Use FIXED world model
    probs = probs ./ (sum(probs) + 1e-16)
    sampled = sample_categorical(probs)
    push!(obs, sampled)
end
```

### Step 3: Use A_agent for State Inference

```julia
# State inference using A_agent (learned beliefs)
lik = ones(matrices.n_states)
for g in 1:length(matrices.No)
    lik .*= A_agent[g][obs[g], :]  # Use LEARNED agent beliefs
end
qs = qs .* lik
qs = qs ./ (sum(qs) + 1e-16)
```

### Step 4: Use A_agent for Expected Free Energy

```julia
# EFE calculation uses agent beliefs
matrices_agent = (
    A=A_agent,  # Agent's beliefs, not world truth
    B_actions=matrices.B_actions,
    C=matrices.C,
    E=matrices.E,
    T=matrices.T
)
qpi, G = infer_policies(qs, matrices_agent; gamma=gamma)
```

### Step 5: Update A_agent (NOT A_world) During Learning

```julia
# Learning updates agent beliefs only
for g in modalities_to_learn
    for t in eachindex(obs_g)
        a_priors[g] .+= eta .* (obs_g[t] * filtered_beliefs[t]')
    end
    # Update A_agent (NOT A_world!)
    A_agent[g] .= a_priors[g] ./ sum(a_priors[g], dims=1)
end
```

## Why This Works

**The world is the teacher, not the student.** The agent cannot change reality by believing differently. By keeping `A_world` fixed:
- Observations always come from the true world distribution
- Safe spider exposures consistently generate calm observations
- The agent receives consistent disconfirming evidence

**Learning updates beliefs, not reality.** By updating only `A_agent`:
- The agent's model of P(observation|state) improves over time
- Initial biased beliefs ("spiders cause fear") get corrected
- Danger beliefs decrease (0.5 → 0.05) as evidence accumulates

This is analogous to:
- **Supervised learning**: You don't change the training labels based on model predictions
- **Scientific method**: Experiments produce data independent of your hypothesis
- **Therapy**: Reality doesn't change to match fears; beliefs update to match reality

## Verification

After the fix, D learning works correctly:

```
Results after 100 trials (safe spider):
  Approach: 96, Avoid: 4

D learning (danger belief evolution):
  Initial danger belief:  0.5
  Final danger belief:    0.0561
  Change:                 -0.4439
  ✓ Danger belief DECREASED (correct learning!)
```

## Prevention

### Best Practices

1. **Always separate generative model from recognition model**
2. **Use clear naming**: `A_world` vs `A_agent`, or `model_A` vs `belief_A`
3. **Document which matrix is used where** at every call site
4. **Consider immutability** for world models to prevent accidental modification

### Code Review Checklist

- [ ] Observation generation uses fixed world model
- [ ] State inference uses learnable agent beliefs
- [ ] Learning updates agent beliefs, not world model
- [ ] EFE calculation uses agent beliefs
- [ ] Variable names clearly indicate world vs. agent matrices

### Test Cases

```julia
@testset "Safe exposure decreases danger belief" begin
    result = run_exposure_therapy(spider_dangerous=false, n_trials=100)
    @test result.final_danger_belief < 0.5  # Should decrease from 0.5
end

@testset "World model unchanged after simulation" begin
    A_world_original = deepcopy(A_world)
    run_simulation!(A_world, A_agent)
    @test A_world == A_world_original  # World must be unchanged
end

@testset "Agent beliefs converge toward world truth" begin
    initial_error = sum(abs.(A_agent - A_world))
    run_learning!(A_agent, observations)
    final_error = sum(abs.(A_agent - A_world))
    @test final_error < initial_error  # Should improve
end
```

## Files Modified

- `src/rxinfer_impl.jl` - Added A_world/A_agent separation, uniform D prior
- `src/rxinfer_native.jl` - Same separation pattern for native RxInfer models
- `src/IFSActiveInference.jl` - Updated exports
- `test/test_rxinfer.jl` - Updated tests

## Related Documentation

- `src/simulation.jl` - Original implementation correctly separates `model.A` (fixed) from `agent.a` (learnable)
- `src/rxinfer_native.jl` lines 196-229 - Design decision rationale for external vs in-graph A learning
- `key_terms.md` - Definitions of precision, opacity, transparency
- `learning_notes.md` - Notes on precision and sensory channels

## Cross-References

- Commit: `9f8f4b8` - "Fix A learning feedback loop with A_world/A_agent separation"
- Related concept: Dirichlet-Categorical conjugate learning
- Related concept: Expected Free Energy (EFE) calculation
