# V3.4 decisions

1. The partner state is one four-state latent process. Clinical descriptions
   are constructor-only labels and are rejected at the inference boundary.
2. Trust is a posterior query over remaining-after-refusal predictions, never
   a mutable array.
3. Regulation-only observations carry exactly zero root evidence. Root uptake
   occurs only when typed root evidence is present.
4. Broadcast-off scoring preserves the local relational posterior and fixes
   global precision at baseline.
5. The recovery-generator root-bit defect was treated as a pure software
   error under `stage0-repair-authorization.md`; the consumed defective pilot
   remains in the record.
6. Per `gate5-adjudication.md`, the 48-slice primary recovery thresholds are
   blocking. The 32/96-slice robustness cells are descriptive information
   curves. The original transplanted 32-slice FAIL remains unchanged.
