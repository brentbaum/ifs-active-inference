# Assay 8 analysis plan — Derived exiling and registration

Status: **frozen before Phase 0**. Evidentiary class: conformance for selection, causal for registration.

- Design: learn policy costs and reliabilities from developmental history, test selection in held-out worlds, then pair registration on/off/ablation while holding the selected policy and contact stream fixed.
- Primary estimands and unit: rate that selection tracks the lowest learned expected cost; paired relational-prior change for registration on minus off; static off/ablation property. One seeded developmental history/world is the unit.
- Aggregation: selection rate with binomial interval and paired mean prior changes. Expected-cost ties count as selection failures. No contact attempts is retained and contributes zero registration change.
- Effect size, threshold, and population: tracking ≥ `assay8_selection_rate = 0.80`; on-minus-off change ≥ `assay8_registration_margin = 0.10`; off and ablation remain within `static_tolerance = 1e-12`. Confirmation uses 80 held-out worlds.
- Analysis population and failures: all generated histories/worlds. Missing histories, direct posterior initializers, unmatched streams, and non-finite beliefs count as primary failures.
- Outcomes: primary—learned-cost selection and registration contrast. Descriptive—policy-specific learned costs/reliabilities and attempt counts.
- Hypothesis provenance: selection and registration regimes are **Original prediction** from Experiment 48 (`results/exiling_emergence/report.md`); replacing authored costs with learned developmental beliefs is **50 prospective**.
