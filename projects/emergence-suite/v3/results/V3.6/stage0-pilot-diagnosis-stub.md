# V3.6 Stage-0 pilot honest stop

Verdict: **FAIL — STOP**.

The adjudicated pilot block `3600001:3603999` was consumed exactly once,
ascending and gap-free. Seed `3600000` was not touched. Every runtime event
ledger and per-world record was persisted to
`stage-0-attainability-pilot-traces.jsonl`; the record and whole-file SHA-256
ledger was written and verified before aggregation or terminal output.

The blocking failure is the prospectively declared premature-do-over
equivalence. The paired endpoint was

`q_current_edge_absence(full) - q_current_edge_absence(premature_do_over)`.

Its mean was `0.015139500753264512` and its whole-world bootstrap 95% interval
was `[-0.018567536075274952, 0.04911686181384986]`. The frozen equivalence rule
requires the entire interval inside `[-0.01, 0.01]`; it is not.

For localization only, the other nine comparator contrasts had 95% intervals
strictly in their declared positive directions. Stakes left the scientific
posterior exactly invariant (`max error = 0.0`) and changed policy in the
declared direction (`95% interval [0.10407715430994677,
0.10717623019155693]`). The structure-code-length distribution was also
successfully published. These passing observations do not override the failed
equivalence.

No numeric floors were frozen. Gates 2--5, the diagnosis block, and all three
sealed escrows remain unopened. This stub does not infer whether the failure is
a scientific composition result, a schedule issue, or an implementation
defect. V3.6 returns to the evaluator; no repair is self-authorized.
