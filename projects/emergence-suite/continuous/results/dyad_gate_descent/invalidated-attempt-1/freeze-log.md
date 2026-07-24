# Experiment 49 freeze log

- Frozen: 2026-07-24 20:28:37.
- Pilot opened once: `14901:14910` (10 worlds per arm).
- Confirmation remained unopened: `14951:14970` (20 fresh, disjoint worlds per arm).
- The first and only pilot used the moderate calibration recorded in `magic-numbers.md`; no alternative calibration profile was run.
- **Permission rises** at the first episode where the protector's `risk_model_permission(..., future=:obsolete)` reaches `0.5`, provided it began below that threshold.
- **Root revision begins** at the first permitted witnessing update where the vulnerable-bundle identity-root posterior reaches `0.62`.
- Within an episode the event order is fixed: dyad observation → optional precision-weighted `TrustEvidence` update → protector permission decision → permitted contact → bundle likelihood update. Episode ties therefore preserve strict event ordering, but the report also logs integer episode lags.
- §8.5 thresholds retained unchanged: coupled contact ≥ `16/20`; no-dyad and decoupled contact ≤ `2/20`; permission precedes revision in every inferential descent.
- Pilot contact counts: coupled `10/10`, no-dyad `0/10`, decoupled `0/10`; authored calibration `10/10`.
- Threshold, parameter, architecture, measure, and vocabulary changes after pilot: **none**.
- Confirmation access guard: the runner refuses `--confirm` unless this log exists and refuses a rerun after the confirmation marker exists.
- Frozen register: *configural* means within-bundle statistical organization; *relational* is interpersonal only; vulnerable-bundle contact is *witnessing* and protector contact is *befriending*. *Organization* means the bundle, couplings, precisions, and field profile; *carrier* means independently parameterized substrate. The dyad scaffold is a learned precision state, not a renamed carrier.
