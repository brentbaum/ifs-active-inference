# DT-S2-DESCENT post-verdict apparatus stop

Status: **STOP_PENDING_EVALUATOR_ADJUDICATION**.

The original immutable `s2-verdict.json` and literal prediction-scoring records
remain retained and unedited. A post-verdict review found three related S2-C
apparatus/estimand defects:

1. `forced_done` is set at the one authorized forced-contact probe
   (`scripts/run_decisive_s2.py:226,235`) but is never reset. The later contact
   predicate uses `(allowed or forced_done)` (`:243`), so the one-slice
   intervention improperly authorizes every later controller contact.
2. The registered outcome is **later** contact probability. The aggregate uses
   `eventual_contact`, whose first-passage event includes the forced probe itself
   (`:244,270,384,388-389`). The forced arm therefore has contact rate `1.0` by
   construction, making the registered direction impossible to score.
3. The `low_permission_request` arm overrides the controller with
   `request_access` (`:234`), while the registered bypass arm requests contact
   while permission is low. This is a plan-fidelity mismatch, not evidence
   against the bypass prediction.

These defects are confined to the paired S2-C runner and its aggregates. S2-A
and S2-B use separate cells and do not invoke any S2-C arm override. Their
recorded statistics remain reproducible from their persisted traces, but the
overall Study-2 scientific disposition is withheld pending evaluator ruling.

No repair was applied. No seed was regenerated, retried, rescored, or reused.
Study 3 and all escrows remain unopened.

Retained immutable hashes:

- `s2-verdict.json`: `222c77445750f2917ebad268fe11278241c5423686f3d21d4c53f53ed64bf4a9`
- `s2-prediction-scoring.json`: `55c44809c72e586fe30f67d48d35a727aaa79a945f628dba9475343efd3a40b6`
- trace bundle: `6ba91de86e3c2c8b2a1e042910c59132cb8b54eb7180c13b14277805c7b2345b`
