# V2.4.1 Gate-3 reporting erratum

This is an analysis-only completeness annotation. It does not alter or
rerun a world, change a criterion, or remove any of the four failure labels
in `gate-3.json`.

The Gate-3 runner stopped correctly, but its compact report did not emit
every frozen subcriterion. The following obligations are therefore retained
as **unscored failures**, not inferred passes:

- Assay 6 did not emit or score the genuine-CS held-out margin over the best
  pre-held-out matched-complexity comparator.
- Assay 8 did not emit or score that held-out margin.
- Assay 8 did not emit the required outcome breakdown for each initial
  formed-bank strength stratum.

The scored failures already make the Gate-3 verdict unambiguously FAIL:

- Assay 3 had only 45/80 matched GW worlds and 3/80 matched CP worlds,
  below the frozen 60/80 power gate. Its reported margins were positive;
  the failure is underpowered matching, not an adverse margin.
- Assay 6 selected CS in 0.7917 of genuine-context worlds, but the transfer
  interval was `0.0750 [-0.0075, 0.1575]` and the present-indexing interval
  was `0.0750 [-0.0075, 0.1500]`; both lower bounds failed to exclude zero.
- Assay 7 selected CS in 0.5500 of shuffled controls and 0.4583 of
  fixed-context controls, both above the 0.10 ceiling. Cue-local recovery
  was 0.5833, below 0.60.
- Assay 8 selected CS in 0.6083 of shuffled controls and 0.3583 of
  single-regime controls, both above 0.10. The transfer interval was
  `-0.1573 [-0.2341, -0.0812]`, opposite the preregistered positive
  direction. Genuine-CS selection (0.8417), historical retention (exact
  zero), and clone identity passed.

Semantic integrity remained intact: the maximum complexity-recombination
error was `4.2633e-14`, and misspecification update identities remained
below `1e-10`. Accordingly, the corrected verdict classes are scientific
outcomes **FAIL**, semantic integrity **PASS**, distributional stress
**DESCRIPTIVE_ONLY**, and process custody **PASS**.
