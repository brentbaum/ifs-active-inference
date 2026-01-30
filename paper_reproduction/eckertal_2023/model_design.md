# Model Design (Eckertal 2023 / Trust Game)

This document encodes the **exact generative model structure** from the paper and pymdp_depression reference.

## 1) Dimensions
- **Hidden state factors (Nf = 2)**
  - Factor 1: `context` (Ns1 = 3): friendly, hostile, neutral
  - Factor 2: `choice` (Ns2 = 3): share, keep, start
- **Outcome modalities (Ng = 3)**
  - Modality 1: reward (No1 = 3): high, low, neutral
  - Modality 2: behavior (No2 = 3): social, antisocial, unknown
  - Modality 3: choice (No3 = 3): share, keep, start
- **Trial length**: `T = 2` (decide then observe outcome)

## 2) Constants (from trust_game.jl)

```julia
# Context states
CONTEXT_FRIENDLY = 1
CONTEXT_HOSTILE = 2
CONTEXT_NEUTRAL = 3

# Choice states
CHOICE_SHARE = 1
CHOICE_KEEP = 2
CHOICE_START = 3

# Reward observations
REWARD_HIGH = 1      # 1.0 - cooperation returned
REWARD_LOW = 2       # 0.0 - betrayed
REWARD_NEUTRAL = 3   # 0.5 - neutral outcome

# Behavior observations
BEHAVIOR_SOCIAL = 1
BEHAVIOR_ANTISOCIAL = 2
BEHAVIOR_UNKNOWN = 3

# Actions
ACTION_SHARE = 1
ACTION_KEEP = 2
ACTION_START = 3
```

## 3) A: Likelihoods

### Reward (A[1]) - Shape: (3, 3, 3) = (reward_obs, context, choice)

| Choice | Context | P(high) | P(low) | P(neutral) |
|--------|---------|---------|--------|------------|
| start | any | 0 | 1 | 0 |
| keep | any | 0 | 0 | 1 |
| share | friendly | p_share_friendly | 1-p_share_friendly | 0 |
| share | hostile | p_share_hostile | 1-p_share_hostile | 0 |
| share | neutral | p_share_neutral | 1-p_share_neutral | 0 |

**Key**: Share gives HIGH or LOW only (no neutral) - creates risk/reward contrast.

### Behavior (A[2]) - Shape: (3, 3, 3) = (behavior_obs, context, choice)

| Choice | Context | P(social) | P(antisocial) | P(unknown) |
|--------|---------|-----------|---------------|------------|
| start | any | 0 | 0 | 1 |
| keep | any | 0 | 0 | 1 |
| share | friendly | p_share_friendly | 1-p_share_friendly | 0 |
| share | hostile | p_share_hostile | 1-p_share_hostile | 0 |
| share | neutral | p_share_neutral | 1-p_share_neutral | 0 |

**Critical**: Keep/Start => Unknown (no epistemic gain without sharing!)

### Choice (A[3]) - Shape: (3, 3, 3) = (choice_obs, context, choice)
- Deterministic identity: agent sees own choice state.
- Independent of context.

### Post-processing
- A[2] and A[3] have softmax applied over observation dimension (pymdp style).

## 4) B: Transitions

### Context (B[1]) - Shape: (3, 3, 1) - uncontrollable

#### paper_default (gen_B from pymdp)
```
        from_friendly  from_hostile  from_neutral
to_friendly    0.90         0.32         0.50
to_hostile     0.02         0.60         0.30
to_neutral     0.08         0.08         0.20
```

#### depressed (gen_depressedB)
```
        from_friendly  from_hostile  from_neutral
to_friendly    0.20         0.05         0.15
to_hostile     0.70         0.90         0.15
to_neutral     0.10         0.05         0.70
```

#### insecure (gen_insecureB)
```
        from_friendly  from_hostile  from_neutral
to_friendly    0.20         0.10         0.20
to_hostile     0.30         0.40         0.30
to_neutral     0.50         0.50         0.50
```

#### defeated (gen_defeatedB)
```
        from_friendly  from_hostile  from_neutral
to_friendly    0.20         0.15         0.20
to_hostile     0.60         0.80         0.30
to_neutral     0.20         0.05         0.50
```

#### static (gen_staticB)
```
        from_friendly  from_hostile  from_neutral
to_friendly    0.60         0.05         0.10
to_hostile     0.30         0.80         0.60
to_neutral     0.10         0.15         0.30
```

### Choice (B[2]) - Shape: (3, 3, 3) - controllable
- Action-controlled: action k transitions to choice state k.
- Deterministic transitions.

## 5) C: Preferences

### Reward (C[1]) - Shape: (3, T)
Only non-zero at final timestep (T):
```julia
C1[REWARD_HIGH, T] = reward_sensitivity   # paper: 2.5 healthy, 0.8 depressed
C1[REWARD_LOW, T] = loss_aversion         # paper: -2.2 healthy, -4.0 borderline
C1[REWARD_NEUTRAL, T] = neutral_preference # paper: 1.0
```

### Behavior (C[2]) - zeros (uniform preference)

### Choice (C[3]) - zeros (uniform preference)

**Note**: pymdp converts raw C to log(softmax(C)) for EFE computation.

## 6) D: Priors

### Context (D[1])
```julia
D1 = softmax([p_context_friendly, p_context_hostile, 0.0])
```
- Healthy: softmax([0.6, 0.35, 0]) => ~50% friendly, ~40% hostile, ~10% neutral
- Depressed: softmax([0.15, 0.8, 0]) => ~15% friendly, ~80% hostile

### Choice (D[2])
```julia
D2 = [0, 0, 1]  # starts in start state
```

## 7) Policies

### Policy Set
- 3 policies: Share, Keep, Start
- V[t, pi, f] = action for timestep t, policy pi, factor f
- Factor 1 (context): always action 1 (uncontrollable)
- Factor 2 (choice): policy 1=share, policy 2=keep, policy 3=start

### Policy Prior (E)
- Uniform: E = [1/3, 1/3, 1/3]

## 8) Profile Parameters (Paper-Matching)

### healthy_profile_paper()
| Parameter | Value |
|-----------|-------|
| p_share_friendly | 0.9 |
| p_share_hostile | 0.15 |
| p_share_neutral | 0.5 |
| p_context_friendly | 0.6 |
| p_context_hostile | 0.35 |
| reward_sensitivity | 2.5 |
| loss_aversion | -2.2 |
| neutral_preference | 1.0 |
| b_mode | :paper_default |
| update_B | true |
| eta_A | 0.1 |
| eta_B | 3.0 |
| eta_D | 1.0 |
| gamma | 16.0 |

### depressed_profile_paper()
| Parameter | Value |
|-----------|-------|
| p_context_friendly | 0.15 |
| p_context_hostile | 0.8 |
| reward_sensitivity | 0.8 (key difference!) |
| b_mode | :depressed |
| update_B | false (fatalistic) |

## 9) Environment vs Agent Model

### Environment
- Context stays FIXED (identity B matrix).
- Observations sampled based on env_share_probs = (0.8, 0.2, 0.5).
- True partner type set by partner_type parameter.

### Agent's Generative Model
- Believes context can change (profile-specific B).
- Uses A matrix to infer context from observations.
- Updates beliefs via state inference + learning.

## 10) Learning Configuration

### What is learned
- A[1, 2] (reward and behavior modalities).
- B (if update_B = true).
- D[1] (context prior).

### Learning timing
- After final observation (end of trial).
- Uses agent.qs[T] for updates.

### Key function: update_pD_from_qs()
- Updates pD based on current posterior qs.
- Only updates specified factors (typically [1] for context).
