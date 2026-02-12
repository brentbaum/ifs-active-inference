# Active Inference Modeling: Complete Learnings Index

**A guide to all knowledge artifacts from the Chamberlin 2022 reproduction.**

---

## Document Roadmap

### For First-Time Readers
1. **Start here:** `QUICK_START_CHECKLIST.md` (30 min read)
   - Purpose: Phase-by-phase checklist for any new Active Inference model
   - What you'll learn: What to do before, during, and after implementation
   - Best for: Everyone starting a new reproduction

2. **Then read:** `PREVENTION_STRATEGIES.md` (60 min read)
   - Purpose: Deep dive into design patterns, pitfalls, and expert consultation
   - What you'll learn: Why designs fail and how to prevent it
   - Best for: Understanding the reasoning behind the checklist

### For Implementation

3. **Reference:** `paper_reproduction/chamberlin_2022/`
   - `learnings.md` - Design iterations and bugs encountered
   - `task_spec.md` - Exact model specification (matrices, tests, parameters)
   - `model_design.md` - Alternative designs considered (historical)
   - `PLAN.md` - Project timeline and status

### For Code Review

4. **Review:** `src/active_inference/coherence_therapy_model.jl`
   - Implementation of CT mechanism and Discovery extension
   - All matrices, learning rules, and intervention protocol
   - Regression test suite (14 tests)

---

## Key Insights by Topic

### Design Patterns

**When you need to extend a binary state to multi-level:**
→ Read: `PREVENTION_STRATEGIES.md` Section 1.1 (Interpolation Pattern)
→ Example: Modular/Integrated → Implicit/Partial/Explicit with α ∈ [0,1]

**When you need gradual behavioral change from instantaneous mechanism:**
→ Read: `PREVENTION_STRATEGIES.md` Section 1.2 (Scheduling Pattern)
→ Example: Precision annealing (γ: 1→8) to model exploration→exploitation

**When you need stochastic outcomes (not all clients reach resolution):**
→ Read: `PREVENTION_STRATEGIES.md` Section 1.3 (Stochastic Scaffolding Pattern)
→ Example: 55-85% reach explicit state depending on therapist effort

---

### When to Consult External Experts

**Decision framework:**
→ Read: `PREVENTION_STRATEGIES.md` Section 2 (Expert Consultation)

**Triggers for delegation:**
- 2+ failed design attempts
- Architectural tradeoffs between 2+ approaches
- Confusing mechanism vs process
- State explosion (>100 combinations)

**How to brief an expert (Codex Architect):**
```
"I'm modeling [phenomenon]. I tried [approach 1] and [approach 2].
Both work but have tradeoffs in [dimension A] and [dimension B].
Which is simpler while still capturing [core claim]?"
```

---

### Detecting Over-Complexity

**Red flag checklist:**
→ Read: `PREVENTION_STRATEGIES.md` Section 3

**Common pitfalls:**
1. State factor doing >3 jobs → Split it
2. Contradictory parameters → Separate concerns
3. Special casing in 5+ places → Generalize with gating
4. Magic numbers without justification → Pre-register before implementing

**Complexity score formula:**
```
Complexity = (# Factors) × (avg States/Factor) × (# Modalities) × (# Learnable params)
Target: 30-80 for paper reproduction
```

---

### Test Design

**Test hierarchy:**
1. **Mechanism tests (95%+ pass)** - Does core claim hold?
2. **Behavioral tests (85%+ pass)** - Do predictions emerge?
3. **Comparative tests (80%+ pass)** - Is this better than alternatives?

→ Read: `PREVENTION_STRATEGIES.md` Section 4 (Test Design Principles)

**Chamberlin tests:**
| Test | Type | Threshold | Passes | Why |
|------|------|-----------|--------|-----|
| Baseline maintains avoidance | Mechanism | P > 0.9 | 7/7 | Modular mode must block learning |
| CT step function | Behavioral | Δ > 0.7 | 7/7 | Large effect, rapid transition |
| Discovery access increases | Behavioral | α̅ > 2.5 | 7/7 | Most clients reach explicit |

---

### Common Pitfalls & Recovery

**Pitfall 1: Instant mechanism vs gradual behavior**
- Problem: Model shows P(avoid) drops 0.96→0.03 in one trial
- Paper says: "takes weeks"
- Recovery: Add interpolation factor (α: 0→1) + precision schedule (γ: 1→8)

**Pitfall 2: Parameter tuning (over-fitting)**
- Problem: Adjusted 10 parameters to make 7 tests pass
- Red flag: Small param change breaks multiple tests
- Recovery: Pre-register ALL parameters before implementation

**Pitfall 3: Learning rate ambiguity**
- Problem: D3 doesn't update in modular mode, but is it due to η=0 or something else?
- Recovery: Test learning-rate-only: Set η=0.5 in modular mode, verify D3 still protected

---

## Statistics Summary

| Metric | Value | Source |
|--------|-------|--------|
| Design iterations before expert consultation | 2 | Coherence Therapy Project Plan |
| Implementation days | 1 | Timeline |
| Critical bugs (broke core tests) | 1 | D1 in modular mode |
| Total tests passing | 14/14 | 7 original + 7 Discovery |
| Complexity reduction from expert review | ~70% | 3-state → 2-state + accessibility |

---

## Key Files Reference

| File | Location | Purpose |
|------|----------|---------|
| PREVENTION_STRATEGIES.md | `docs/guides/` | Comprehensive best practices |
| QUICK_START_CHECKLIST.md | `docs/guides/` | Phase-by-phase execution guide |
| LEARNINGS_INDEX.md | `docs/guides/` | This document (navigation) |
| learnings.md | `paper_reproduction/chamberlin_2022/` | Actual design decisions |
| task_spec.md | `paper_reproduction/chamberlin_2022/` | Complete model spec |
| coherence_therapy_model.jl | `src/active_inference/` | Implementation |

---

## Fast Navigation by Goal

| Goal | Read |
|------|------|
| Understand why Chamberlin failed/succeeded | `PREVENTION_STRATEGIES.md` + `learnings.md` |
| Model a different therapy (CBT, EMDR, etc.) | `QUICK_START_CHECKLIST.md` |
| Debug why tests are failing | `QUICK_START_CHECKLIST.md` "Emergency" section |
| Review code quality | `paper_reproduction/chamberlin_2022/` |

---

## Learning Outcomes

After reading these documents, you should be able to:

1. **Design Phase** - Identify over-complexity, separate mechanism from process, pre-register tests
2. **Implementation Phase** - Build single-trial tests first, verify matrix algebra early
3. **Verification Phase** - Run tests in correct order (Tier 1 → 2 → 3)
4. **Documentation Phase** - Write learnings.md, create regression tests

---

**Last updated:** 2026-01-30
**Audience:** Future Active Inference modelers
