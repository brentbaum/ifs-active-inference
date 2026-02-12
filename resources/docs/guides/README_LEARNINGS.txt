================================================================================
CHAMBERLIN 2022 PREVENTION STRATEGIES & LESSONS LEARNED
================================================================================

SUMMARY
-------
This directory contains comprehensive guidance for future Active Inference 
modelers, synthesized from the complete Chamberlin 2022 (Coherence Therapy) 
reproduction project.

THREE CORE LESSONS LEARNED
---------------------------

1. BINARY STATE EXTENSIONS REQUIRE INTERPOLATION
   Problem: Model showed instant behavior change but theory predicts gradual
   Solution: Add continuous accessibility factor (α: 0→1) to interpolate between
             modular/integrated states
   Code pattern: A1(α) = (1-α)*A_modular + α*A_integrated
   Read: PREVENTION_STRATEGIES.md Section 1.1

2. KNOW WHEN TO DELEGATE TO EXPERTS
   Problem: 2+ failed designs (dual-models, hierarchical) before finding simplicity
   Solution: After 2nd failure, consult Codex Architect for tradeoff analysis
   Timeline: Architect review took 2 hours, saved 10+ hours of iteration
   Read: PREVENTION_STRATEGIES.md Section 2

3. DISTINGUISH MECHANISMS FROM PROCESSES
   Problem: Conflating binary mechanism change with gradual behavioral unfolding
   Solution: Separate schema-mode (binary mechanism) from precision schedule 
            (continuous process) from accessibility factor (interpolation)
   Result: Each concern handled independently, fewer "cheats"
   Read: PREVENTION_STRATEGIES.md Section 1.2

DOCUMENT STRUCTURE
------------------

For Different Audiences:

Starting a NEW Active Inference Model?
  └─ Read: QUICK_START_CHECKLIST.md (30 min)
     What you'll get: Phase-by-phase execution guide with diagnostic trees

Want to UNDERSTAND the reasoning behind the checklist?
  └─ Read: PREVENTION_STRATEGIES.md (60 min)
     What you'll get: Design patterns, pitfalls, expert consultation framework

Need to FIND something specific?
  └─ Read: LEARNINGS_INDEX.md (navigation guide)
     What you'll get: Fast lookup by goal, file reference, learning outcomes

Implementing RIGHT NOW?
  └─ Use: QUICK_START_CHECKLIST.md phases in order
     Reference: PREVENTION_STRATEGIES.md sections as needed

FILES CREATED
-------------

1. PREVENTION_STRATEGIES.md (891 lines, 32KB)
   ├─ Part 1: Design Patterns for Gradual State Transitions
   ├─ Part 2: When to Consult External Experts (Codex)
   ├─ Part 3: Warning Signs of Over-Complexity
   ├─ Part 4: Test Design Principles
   ├─ Part 5: Documentation & Knowledge Transfer
   ├─ Part 6: Practical Checklist for New Modelers
   ├─ Part 7: Common Pitfalls & How to Avoid Them
   ├─ Part 8: When to Extend vs When to Stop
   ├─ Part 9: The Chamberlin 2022 Incident Log
   └─ Part 10: Generalization to Other Active Inference Projects

2. QUICK_START_CHECKLIST.md (412 lines, 12KB)
   ├─ Phase 1: Before You Code (1-2 hours)
   ├─ Phase 2: During Implementation (2-5 days)
   ├─ Phase 3: Verification (3-5 days)
   ├─ Phase 4: Documentation (1-2 hours)
   ├─ Quick Diagnostic: When Tests Fail
   ├─ Red Flag Checklist
   └─ Success Criteria Checklist

3. LEARNINGS_INDEX.md (navigation + meta-reference)
   ├─ Document Roadmap (what to read first)
   ├─ Key Insights by Topic
   ├─ Fast Navigation by Goal
   ├─ Key Files Reference
   └─ Learning Outcomes

KEY STATISTICS FROM CHAMBERLIN PROJECT
--------------------------------------

Design Iterations:        2 (before expert consultation)
Expert Consultation:      1 (Codex Architect)
Implementation Days:      1 (surprisingly fast)
Critical Bugs Found:      1 (D1 in modular mode)
Total Tests Passing:      14/14 (7 original + 7 Discovery)
Complexity Reduction:     ~70% (from 3-state factor → 2-state + accessibility)
Time Saved by Early Help: 5-10 hours (avoiding over-complicated designs)
Discovery Extension:      7 new tests, all passing

TOP 5 PREVENTION PRINCIPLES
---------------------------

1. SEPARATE CONCERNS
   - Mechanism (what changes): Binary schema_mode
   - Process (how it unfolds): Precision schedule + accessibility factor
   - Observation (what you see): P(avoid) trajectory
   → Don't mix these in a single factor

2. PRE-REGISTER EVERYTHING
   - Test thresholds (before implementing)
   - Parameter values (before running)
   - Design decisions (document the reasoning)
   → Never tune parameters "to make tests pass"

3. TEST IN TIER ORDER
   - Tier 1: Mechanism tests (95%+ pass rate) - Core claim holds?
   - Tier 2: Behavioral tests (85%+ pass rate) - Predictions emerge?
   - Tier 3: Comparative tests (80%+ pass rate) - Better than alternatives?
   → Fix Tier 1 failures before testing higher tiers

4. KNOW YOUR COMPLEXITY BUDGET
   Complexity = (# Factors) × (avg States) × (# Modalities) × (# Learnable Params)
   - Paper reproduction target: 30-80
   - If > 80: Ask "What can I remove or gate?"
   - If complexity jumped, consult architect

5. DOCUMENT DESIGN FAILURES
   → For each iteration: Problem → Approach → Why it Failed → Root Cause → Solution
   → Someone will repeat your mistakes; help them avoid it

QUICK DIAGNOSTIC DECISION TREE
-------------------------------

Q1: Is this your first Active Inference model?
    YES → Read QUICK_START_CHECKLIST.md Phase 1 first
    NO → Skip to Q2

Q2: Have you already tried 2+ design approaches?
    YES → Consult Codex Architect before continuing
    NO → Proceed with implementation

Q3: Are your tests failing?
    YES → See QUICK_START_CHECKLIST.md "Quick Diagnostic: When Tests Fail"
    NO → Proceed to verification

Q4: Can you explain why every parameter has its value?
    NO → You may be over-fitting; see PREVENTION_STRATEGIES.md Section 7.2
    YES → Proceed to documentation

Q5: Do you want to extend the model?
    YES → See PREVENTION_STRATEGIES.md Section 8 (When to Extend vs Stop)
    NO → Document completion and create regression test

MOST COMMON PITFALLS (From Experience)
--------------------------------------

1. Instant mechanism vs gradual behavior
   → Solution: Add interpolation factor (α) + precision schedule (γ)
   → See: PREVENTION_STRATEGIES.md Section 7.1

2. Parameter tuning instead of pre-registration
   → Solution: Write thresholds BEFORE implementing
   → See: PREVENTION_STRATEGIES.md Section 7.2

3. State factor doing 3+ different jobs
   → Solution: Split into separate factors/parameters
   → See: PREVENTION_STRATEGIES.md Section 3.2

4. Not checking if learning gate actually works
   → Solution: Add assertion: @assert eta == 0 if schema_mode == MODULAR
   → See: PREVENTION_STRATEGIES.md Section 7.4

5. High variance in replication results
   → Solution: Check for bimodal distribution, increase replications to 50+
   → See: PREVENTION_STRATEGIES.md Section 7.5

READING TIME ESTIMATES
----------------------

Quick Start (Decision: Should I continue?):        10 min (LEARNINGS_INDEX.md)
Immediate implementation support:                   30 min (QUICK_START_CHECKLIST.md)
Understanding the why behind the checklist:        60 min (PREVENTION_STRATEGIES.md)
Case study of actual project:                      20 min (learnings.md from Chamberlin)
Complete reference:                               120-150 min (all documents)

NEXT STEPS
----------

1. For new modelers:
   - Read: QUICK_START_CHECKLIST.md Phase 1
   - Decide: Proceed with own project or review Chamberlin first?

2. For current Chamberlin extenders:
   - Read: PREVENTION_STRATEGIES.md Section 8 (When to Extend)
   - Reference: paper_reproduction/chamberlin_2022/learnings.md

3. For code reviewers:
   - Check: src/active_inference/coherence_therapy_model.jl
   - Verify: Regression test passes
   - Reference: test expectations from task_spec.md

4. For documentation:
   - Template: PREVENTION_STRATEGIES.md Section 5.1 (Learnings.md format)
   - Checklist: QUICK_START_CHECKLIST.md Phase 4 (Documentation Phase)

SUPPORTING FILES IN REPOSITORY
-------------------------------

Paper Reproduction:
  /paper_reproduction/chamberlin_2022/
  ├─ learnings.md (217 lines) - Design decisions and bugs encountered
  ├─ task_spec.md (1036 lines) - Complete model specification
  ├─ model_design.md (282 lines) - Alternative designs considered
  ├─ PLAN.md (129 lines) - Project timeline and status
  └─ fnhum-16-955558.pdf - Original paper

Implementation:
  /src/active_inference/coherence_therapy_model.jl (~400 lines)
  - Complete working implementation
  - All tests passing (14/14)
  - Regression test suite

Comparisons:
  /paper_reproduction/smith_2021/
  - CBT baseline for comparison with CT

CONTACT & QUESTIONS
-------------------

If you find this guidance incomplete or unclear:
1. Document the gap in /paper_reproduction/chamberlin_2022/learnings.md
2. Add the missing guidance to PREVENTION_STRATEGIES.md or QUICK_START_CHECKLIST.md
3. Update LEARNINGS_INDEX.md to reference new material

================================================================================
Last Updated: 2026-01-30
Status: Complete and ready for use
================================================================================
