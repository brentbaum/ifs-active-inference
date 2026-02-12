# Learnings (PMC7250191 Reproduction)

## 1) Dirichlet-expectation inference is critical for concept learning
- Using `E[ln A] = digamma(a) - digamma(sum(a))` (SPM style) materially changes inference during learning.
- Without it, novel concepts often fail to “win” in posterior inference, even when counts increase.
- This was the key change to align learning dynamics with the paper.

## 2) Concept columns can permute without feedback
- During unsupervised learning, feature mappings can be learned in the “wrong” column.
- Raw specific-report accuracy can appear low even though learned A matches the generative process up to permutation.
- Evaluation should include feature-aligned accuracy (matching columns by feature signatures).

## 3) Reporting accuracy in the paper is evaluated after learning is disabled
- The paper disables learning at checkpoints and then runs reporting trials.
- We matched this by switching to a reporting model with `allow_reports=true` and no learning.

## 4) The SPM demo uses deterministic feature mappings with a null row
- The first row of size/color/species outcomes is unused (all zeros in A).
- Adding a small floor (exp(-4)) is necessary when using digamma to avoid log(0).

## 5) BMR for D is enough for the paper’s reduction demo
- The supplementary code uses BMR for D only.
- A reduction is optional and not required for core reproduction.

## 6) Evaluation targets from the paper
- Full knowledge ⇒ 100% specific accuracy (32 trials, 4 per animal).
- Granularity removed ⇒ 100% basic accuracy (bird/fish).
- Distance generalization task ⇒ 100% accuracy under fixed A.

## 7) Practical lesson for the library
- Having a `use_dirichlet_expectation` toggle in `AIFSettings` makes the library compatible with SPM-style learning while preserving simpler inference for fixed-A use cases.
