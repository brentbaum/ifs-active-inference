# Library Mapping + Gaps (Eckertal 2023 / Trust Game)

This file maps paper requirements to current library capabilities and notes gaps.

## 1) Core Task Requirements (from paper)
- Trust game with investor (agent) and trustee (environment).
- Agent chooses to share or keep resources.
- Environment returns cooperation (friendly) or exploitation (hostile).
- Agent infers hidden context from observations.
- Multiple clinical profiles with biased generative models.
- Multi-phase simulations with context switches.

## 2) Mapping to Our Library

### Trial structure
- Supported via `AIFModel(...; trial_length=T)` with T=2.
- Timestep 1: make decision.
- Timestep 2: observe outcome.

### Hidden factors
- Factor 1 (context): 3 states, uncontrollable, inferred.
- Factor 2 (choice): 3 states, controllable by policy.

### Outcomes
- Modality 1: reward (high/low/neutral).
- Modality 2: behavior (social/antisocial/unknown).
- Modality 3: choice (deterministic own-choice observation).

### A matrices
- Built via `build_trust_game_A(profile)`.
- Uses profile's p_share_friendly/hostile/neutral.
- Softmax post-processing matches pymdp.

### B matrices
- Built via `build_trust_game_B(profile)`.
- Uses profile's b_mode to select transition matrix.
- Supports: paper_default, depressed, insecure, defeated, static, heuristic.

### C matrix
- Built via `build_trust_game_C(profile, T)`.
- Only reward modality has preferences.
- Uses profile's reward_sensitivity, loss_aversion, neutral_preference.

### D matrix
- Built via `build_trust_game_D(profile)`.
- Softmax over [p_context_friendly, p_context_hostile, 0].
- Choice factor starts in start state.

### Policies
- Built via `build_trust_game_policies(T)`.
- 3 policies: share, keep, start.
- Uniform prior E.

## 3) Key Implementation Components

### AgentProfile struct
- Encapsulates all profile-specific parameters.
- A biases: p_share_friendly/hostile/neutral.
- D biases: p_context_friendly/hostile.
- C biases: reward_sensitivity, loss_aversion, neutral_preference.
- B biases: b_mode, context_stability, update_B.
- Learning: eta_A, eta_B, eta_D.
- Precision: gamma.

### Paper-matching profiles
- `healthy_profile_paper()`: Matches Player1_healthy.
- `depressed_profile_paper()`: Type1 depressed.
- `depressed2_profile_paper()`: Type2 depressed.
- `social_phobia_profile_paper()`: Type1 social phobia.
- `social_phobia2_profile_paper()`: Type2 social phobia.
- `borderline_profile_paper()`: Borderline personality.

### TrustGameEnvironment
- Tracks true partner type (:friendly, :hostile, :neutral).
- Context stays fixed (identity B in environment).
- Observations sampled from env_share_probs.

### Simulation functions
- `run_trust_game_simulation()`: Single-phase simulation.
- `run_trust_game_phases()`: Multi-phase with context switches.
- `run_trust_game_comparison()`: Compare multiple profiles.

### Results structures
- `TrustGameResults`: sharing_rate, beliefs, choices, rewards.
- `PaperStyleResults`: Detailed beliefs including pD trajectories.

### Visualization
- `plot_trust_game_paper_style()`: Paper-style figure with phase shading.
- `plot_trust_game_sharing()`: Sharing rate over time.
- `plot_trust_game_beliefs()`: Belief evolution.

## 4) Reference Implementation Mapping

| pymdp_depression | Our Library |
|------------------|-------------|
| gms.py | build_trust_game_A/B/C/D |
| library.py | *_profile_paper() functions |
| gen_B/gen_depressedB/etc | b_mode parameter |
| Player1_healthy | healthy_profile_paper() |
| softmax(C) for EFE | Raw C, converted in EFE |
| qB_pol (posterior) | qs (agent.qs[t]) |
| Dirichlet prior | pD (agent.pD) |

## 5) Key Implementation Details

### qs vs pD plotting
- Paper plots qs (posterior after observation).
- qs is highly responsive (swings ~0.05 to ~0.95).
- pD is slowly accumulating Dirichlet concentration.
- Our `PaperStyleResults` records both for comparison.

### Action selection
- `deterministic_actions=true`: argmax over action distribution.
- Matches pymdp's action_selection='deterministic'.

### Observation sampling
- Environment uses env_share_probs for P(social | context).
- Default: (0.8, 0.2, 0.5) for (friendly, hostile, neutral).

### Learning updates
- After final observation (t=T).
- `update_pA!()` for observation model.
- `update_pB!()` if profile.update_B.
- `update_pD_from_qs!()` for context prior.

## 6) Gaps / Missing Features
- None identified for core reproduction.
- All paper profiles implemented.
- All B transition matrices implemented.

## 7) Test Coverage
- Healthy agent learns friendly context.
- Healthy agent learns hostile context.
- Context switch triggers belief reversal.
- Depressed agent updates more slowly.
- Profile parameters match paper values.
