# T-CAP1 Stage 1 public dynamics census

Status: **COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS_PANEL_SPAN_NOT_ATTAINED**.
No prediction or threshold was sealed.

**Apparatus disposition:** the retained census is accompanied by
`tcap1-stage1-diagnosis-stub.md`. Between-control comparisons are not qualified
because control-arm bundle paths were not all common, and the required
initial-posterior sensitivity replay was not executed.

The census used 8000 public worlds across 324 parameter cells. Region counts: `{"clear_hysteresis": 324, "near_boundary": 0, "no_hysteresis": 0}`.

## Frozen parameter panel

- **no_hysteresis**: no occupied cell; reported without substitution
- **near_boundary**: no occupied cell; reported without substitution
- **clear_hysteresis**: cell 0, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.85, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.6}`, mean transparent H `0.32544498899641106`

The requested three-region panel is therefore **not complete**. The smallest
cell-mean transparent hysteresis was `0.08085224401195291`, just above the
predeclared clear-region boundary of `0.08`. Redefining the regions or tuning
the grid after seeing these worlds would violate the census discipline, so the
two absent panel entries remain explicitly null. This is retained as
`PUBLIC_CENSUS_DYNAMIC_RANGE_NOT_SPANNED`.

Trace SHA-256: `c1cecb3232f43578ba45395a0b4b730469535ae44128f4677c268a845449f64e`. All seven controls plus the primary transparent arm are present.
