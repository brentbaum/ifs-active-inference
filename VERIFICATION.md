# Trust Game Reproduction Verification Guide

## Ground Truth from Eckertal et al. (2023)

### Simulation Parameters
| Parameter | Value |
|-----------|-------|
| Trial length (T) | 40 |
| Replications (N) | 20 |
| Context switch | Trial 20 (friendly → hostile) |

### Profile Parameters (Table 2)

| Profile | p_context_pos | γ | α | ω | Update B | η_D |
|---------|--------------|---|---|---|----------|-----|
| Healthy | 0.6 | 16 | 2.5 | -2.2 | Yes | 1.0 |
| Depression | 0.2 | 16 | 0.8 | -6.2 | No | 0.1 |
| Social Anxiety | 0.2 | 4 | 2.5 | -6.2 | No | 1.0 |
| Borderline | 0.5 | 16 | 2.5 | -6.2 | Yes | 1.0 |

### Quantitative Results (from paper figures)
| Profile | Coins (Friendly) | Coins (Hostile) |
|---------|-----------------|-----------------|
| Healthy | ~250 | ~90 |
| Depression | ~100 | ~85 |
| Social Anxiety | ~110 | ~90 |
| Borderline | ~200 | ~70 |

---

## Programmatic Verification Tests

Added to `test/test_trust_game.jl`:

### 1. Earned Rewards Tests
- Healthy earns significantly more with friendly vs hostile partner
- Depressed earns less than healthy with friendly partner
- Validates the core behavioral difference

### 2. Belief Dynamics Tests
- Healthy converges to high (~0.9) belief in correct context
- Depression maintains pessimistic beliefs (fatalism/no B updates)
- Social anxiety shows uncertainty effects (low gamma)

### 3. Context Switch Response Tests
- Healthy adapts behavior after switch (friendly → hostile)
- Depression shows minimal adaptation (fatalism)

### 4. Parameter Verification Tests
- All paper profile parameters match Table 2 exactly

Run tests with:
```bash
julia --project=. test/test_trust_game.jl
```

---

## Manual Verification Checklist

Compare generated plots (`figures/trust_game/trust_game_paper_style.png`, `figures/trust_game/trust_game_comparison.png`) against paper Figure 2:

### Visual Pattern Matching

#### 1. Belief Trajectories (Top Panels)
- [ ] **Healthy**: P(friendly) starts ~0.6, rises to ~0.9 with friendly partner
- [ ] **Healthy**: After context switch (t=20), P(friendly) drops, P(hostile) rises
- [ ] **Depression**: P(hostile) starts high (~0.8), stays high (minimal learning)
- [ ] **Depression**: Flat/slow belief changes (fatalism)
- [ ] **Social Anxiety**: More variable beliefs (low gamma = uncertainty)
- [ ] **Borderline**: Starts neutral (~0.5), learns but with high loss aversion effects

#### 2. Sharing Behavior (Marked Actions)
- [ ] **Healthy**: Frequent sharing (blue markers) with friendly, rare with hostile
- [ ] **Depression**: Rare sharing even with friendly partner
- [ ] **Social Anxiety**: Moderate sharing, more variable than depression
- [ ] **Borderline**: Shares initially, reduces sharply after negative experiences

#### 3. Context Switch Effects (t=20)
- [ ] **Healthy**: Clear behavior change visible at transition
- [ ] **Depression**: Minimal change (already low sharing)
- [ ] **Borderline**: Dramatic drop in sharing after switch

### Quantitative Checks (from simulation output)
- [ ] Healthy sharing rate with friendly: >80%
- [ ] Depression sharing rate with friendly: <20%
- [ ] Healthy-Depression difference: >50 percentage points
- [ ] Context switch causes >20% drop in healthy sharing

---

## Key Findings to Verify

### 1. Profile Ordering (Friendly Partner)
Expected sharing rates: **Healthy > Borderline > Social Anxiety > Depression**

### 2. Transdiagnostic Biases
| Bias | Manifestation | Profile(s) Affected |
|------|--------------|---------------------|
| Uncertainty | Low gamma → variable behavior | Social Anxiety |
| Fatalism | No B updates → no learning | Depression, Social Anxiety |
| Loss Aversion | High ω → avoid negative outcomes | All clinical |
| Pessimism | High p_hostile prior → expect bad | Depression, Social Anxiety |

### 3. Belief-Behavior Coupling
- Healthy: Beliefs track reality → adaptive behavior
- Depression: Beliefs stuck → maladaptive (miss opportunities)
- Borderline: Beliefs track but high loss aversion → overreaction

---

## Differences from Paper (Expected)

1. **Stochasticity**: Single runs will vary; paper averages N=20 replications
2. **Initial transient**: First few trials may differ due to initial state
3. **Exact values**: Match patterns, not pixel-perfect numbers

## Files Generated
- `figures/trust_game/trust_game_paper_style.png` - Single profile with phases
- `figures/trust_game/trust_game_comparison.png` - All profiles comparison
- `test/test_trust_game.jl` - Automated verification tests
