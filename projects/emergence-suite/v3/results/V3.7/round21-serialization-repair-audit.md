# V3.7 round-21 serialization repair audit

Verdict: **PASS**.

The repair is confined to the worker-row serialization boundary. `calibration_state` is computed through the unchanged V3.7 scorer, then its nested immutable mapping views are copied into plain dictionaries, lists, and scalars before the row crosses the multiprocessing boundary. No probability, posterior, prediction, classification, or criterion changes.

Supporting apparatus changes add the permanent pickle round-trip proof, expose the same row constructors to zero-seed dummies, and select the evaluator-authorized A37-R1 replacement block. The regression test round-trips both exact worker-row shapes through pickle and compares the complete nested value for equality.

All 25 frozen `ref/v3*` files covered by the final V3.6 manifest match their recorded SHA-256 values. `ref/v37.py` and `ref/v37_oracle.py` retain their pre-repair hashes. Both design-freeze artifacts are bitwise unchanged.
