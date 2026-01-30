# Library Mapping + Gaps (PMC7250191)

This file maps paper requirements to current library capabilities and notes gaps.

## 1) Core Task Requirements (from paper)
- Two time points per trial: observe features then report category.
- Hidden state factor 1: animal identity (8 known + optional spare slots).
- Hidden state factor 2: report choice (specific animal or basic bird/fish).
- Outcome modalities: size (big/small), color (gray/colorful), species feature (wings/gills), feedback.
- Learning: A and D via Dirichlet updates; B identity; reporting disabled during learning.
- Preference ordering (C) for feedback: correct specific > correct basic > incorrect.
- Generalization task: apply feature knowledge to a different query (distance question).
- Bayesian model reduction to prune redundant concepts (using Dirichlet evidence).

## 2) Mapping to Our Library
- **Trial structure**: supported via `AIFModel(...; trial_length=T)` with T=2.
- **Hidden factors**:
  - Factor 1: animal identity (8 + extra slots).
  - Factor 2: report action (11 states: start + 8 specific + bird + fish).
- **Outcomes**:
  - Modality 1: size (3 outcomes in code, first is null)
  - Modality 2: color (3 outcomes in code, first is null)
  - Modality 3: species feature (3 outcomes in code, first is null)
  - Modality 4: feedback (start, correct specific, incorrect, correct basic)
- **A matrix**: per‑animal deterministic feature combo; spare columns start flat/uniform.
- **B matrices**:
  - Animal factor: identity matrix.
  - Report factor: controlled by policy/action selection.
- **C matrix**: set preferences over feedback outcomes only; other modalities uniform.
- **D matrix**: flat or weak prior; learned via `pD` updates.
- **Learning**: `update_pA!` + `update_pD_from_qs!` per trial.
- **Dirichlet expectation for inference**: added `use_dirichlet_expectation` to use `E[ln A]` (digamma) as in SPM.
- **Policy restriction**:
  - Learning phase: only allow “stay / no report” policy.
  - Reporting phase: enable all report policies.
 - **Precision**:
   - action selection uses alpha=128 in Concepts_model.m
   - policy precision uses beta=1 (gamma=1/beta in SPM conventions)

## 3) Gaps / Missing Features
- **BMR for A** (optional in paper) not implemented; only D reduction is supported.
- **Supplementary parameters** are now captured in `task_spec.md` from Concepts_model.m.

## 4) Open Items
- Obtain supplementary code to fix numerical parameters.
- Decide how to represent “generalization question” (distance) in the model:
  - Option A: new feedback modality with deterministic mapping from size/color.
  - Option B: new report factor (yes/no) with its own C preferences.
