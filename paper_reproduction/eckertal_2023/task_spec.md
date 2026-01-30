# Eckertal 2023 Task Spec (Trust Game / Mental Disorders)

Source paper: "Simulating Active Inference of Interpersonal Context Within and Across Mental Disorders" (Scientific Reports, 2023).

Reference implementation: https://github.com/Eckertal/pymdp_depression (branch: sims)
- `gms.py`: Generative model structure
- `library.py`: Agent profile definitions

## 1) Task Overview
- Trust Game paradigm: agent (investor) decides whether to share resources with partner (trustee).
- Partner can be friendly (returns cooperation), hostile (exploits), or neutral (random).
- Agent must infer partner's hidden context from observed behavior and rewards.
- Different mental disorder profiles have biased generative models affecting decisions.

## 2) Hidden State Factors (2 factors)

### Factor 1: Context (3 states)
- `friendly` (cooperative): Partner tends to return cooperation.
- `hostile`: Partner tends to exploit.
- `neutral` (random): Partner has mixed behavior.

### Factor 2: Choice (3 states)
- `share`: Agent chose to share resources.
- `keep`: Agent chose to keep resources.
- `start`: Initial/null state before decision.

## 3) Outcome Modalities (3 modalities)

### Modality 1: Reward
- `high` (1.0): Cooperation returned.
- `low` (0.0): Betrayed/exploited.
- `neutral` (0.5): Neutral outcome (from keeping).

### Modality 2: Behavior
- `social`: Partner showed cooperative behavior.
- `antisocial`: Partner showed exploitative behavior.
- `unknown`: No information (when agent keeps).

### Modality 3: Choice
- Agent observes own choice (deterministic).

## 4) Transdiagnostic Biases Modeled

| Bias | Parameter | Effect |
|------|-----------|--------|
| Uncertainty | biased A | P(share\|friendly) = P(share\|hostile) = 0.5 |
| Fatalism | biased B | Low agency belief - actions don't change context |
| Loss Aversion | biased C | Negative outcomes weighted more heavily (-5.0 vs -2.2) |
| Pessimism | biased D | Prior belief context is hostile (70-80% vs 33%) |

## 5) Clinical Profiles (from paper)

### Healthy (Player1_healthy)
- p_share_friendly = 0.9, p_share_hostile = 0.15
- D: 60% friendly, 35% hostile prior
- C: reward_sensitivity = 2.5, loss_aversion = -2.2
- B: paper_default transitions
- gamma = 16.0

### Type1 Depressed
- Same A as healthy.
- D: pessimistic (15% friendly, 80% hostile).
- C: LOW reward sensitivity (0.8 vs 2.5).
- B: depressed transitions (fatalistic).
- updateB = false (fatalistic belief).

### Type2 Depressed
- Higher loss aversion (-2.5).
- Very pessimistic D (10% friendly, 60% hostile).
- B: static transitions.

### Social Phobia Type1
- Uncertain A (p_share_friendly = 0.6).
- HIGH loss aversion (-3.5).
- B: insecure transitions.
- updateB = false.

### Social Phobia Type2
- High uncertainty in A (0.6 vs 0.4).
- Reduced reward sensitivity (1.2).
- B: defeated transitions.

### Borderline
- EXTREME loss aversion (-4.0).
- Pessimistic D.
- B: depressed transitions.

## 6) Generative Model Components

### A (Likelihood)
- Reward: Maps context x choice to reward outcome.
  - Share + friendly => high P(reward_high)
  - Share + hostile => low P(reward_high)
  - Keep/start => neutral reward
- Behavior: Maps context x choice to observed behavior.
  - Share => social/antisocial based on context
  - Keep/start => unknown (no epistemic gain without sharing!)
- Choice: Deterministic observation of own choice.

### B (Transitions)
- Context factor: Profile-specific transition matrices.
  - paper_default: Friendly stays friendly (90%), hostile less stable.
  - depressed: Friendly becomes hostile (70%), hostile very stable (90%).
  - insecure: High transition to neutral.
  - defeated: Friendly becomes hostile (60%).
  - static: Moderate stability.
- Choice factor: Action-controlled (share/keep actions).

### C (Preferences)
- Reward modality only (others neutral).
- Raw utilities (pymdp converts via softmax for EFE).
- reward_sensitivity (p_r0): Gain from positive outcomes.
- loss_aversion (p_r1): Pain from negative outcomes.
- neutral_preference (p_r2): Value of neutral outcomes.

### D (Priors)
- Context: softmax([p_context_friendly, p_context_hostile, 0.0]).
- Choice: starts in `start` state.

## 7) Policies
- 3 policies: Share, Keep, Start.
- Trial length T = 2 (decide, then observe outcome).
- EFE-based policy selection with gamma precision.

## 8) Key Results to Replicate (Figures 2-4)

### Figure 2A: Friendly -> Hostile (healthy agent)
- 20 trials friendly context, then 20 trials hostile.
- Belief in cooperative context starts high, drops after switch.
- Sharing decreases in hostile phase.

### Figure 2B: Hostile -> Friendly (healthy agent)
- Opposite pattern: beliefs shift from hostile to cooperative.

### Figure 3-4: Profile comparisons
- Different profiles show different belief dynamics.
- Depressed agents update beliefs more slowly (fatalism).
- Anxious agents have higher uncertainty.

## 9) Critical Implementation Details

### What to plot: qs (posterior) vs pD (prior)
- Paper plots INFERRED POSTERIOR (qs) after each trial.
- qs is highly responsive to observations (swings from ~0.05 to ~0.95).
- pD is the slowly accumulating Dirichlet prior (less dynamic).
- Our implementation records both for comparison.

### Environment behavior
- Context stays FIXED within environment (identity B in env).
- Agent's generative model may believe context can change (profile's B).
- Environment samples observations based on true context.

### Observation sampling (env_share_probs)
- Environment uses env_share_probs = (0.8, 0.2, 0.5) for (friendly, hostile, neutral).
- This determines actual P(social behavior | context).

## 10) Parameters from pymdp Reference

### Learning rates
- eta_A = 0.1 (observation model)
- eta_B = 3.0 (transition model)
- eta_D = 1.0 (prior beliefs)

### Precision
- gamma = 16.0 (policy precision)

### Dirichlet scaling
- pA_scale, pB_scale, pD_scale = 1.0 (or lower for faster learning)

## 11) Evaluation Metrics
- Sharing rate over trials.
- Belief trajectories (P(friendly), P(hostile), P(neutral)).
- Response to context switches.
- Comparison across agent profiles.
