# V3.7 round-22 generator repair audit

Verdict: **PASS**.

The scientific diff is one generator schedule change in `generate_v3_native_world`: all three `modes_input` coordinates are now sampled from the same Bernoulli(0.5) schedule under every candidate truth. Previously, coordinates at or above the truth's active-mode count were omitted and replaced by zero. Structure-dependent effects now enter only through the unchanged likelihood.

The zero-seed staged ladder enumerated all 56 truth structures. It found one schedule signature, zero schedule disagreement, exact generator/scorer complete-data atom agreement, and maximum normalization error `1.11e-16`. Structure, temporal, partner, danger, action, policy, and channel-emission machinery are unchanged; downstream observations can differ only through the repaired candidate-common mode inputs.

All 25 frozen V3.6 scientific files match the final freeze manifest. The V3.7 oracle and both design-freeze artifacts are byte-identical to their pre-repair versions.
