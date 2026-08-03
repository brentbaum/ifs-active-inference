# V3.6 Round-15 repair readiness

Status: **READY FOR EVALUATOR VERIFICATION BEFORE A-R1**.

All ten replacement preconditions pass. The accepted generator-only repair is
limited to making the native `do(joint_policy)` schedule candidate-common.
The only companion change serializes already-existing complete path state in
future Population-A rows.

| Precondition | Result |
|---|---:|
| Generator-only localization retained | PASS |
| Direction-independent apparatus statement | PASS |
| Authorized source diff only | PASS |
| Scientific/likelihood/prior/threshold/calibration hashes unchanged | PASS |
| Full Layer-B ladder, 128 T=1..4 cells | PASS |
| Twelve-component complete-data identity | PASS |
| Independent 90-digit posterior identity | PASS |
| Eight-family round-13 fixture battery | PASS |
| Matched-dummy differential audit | PASS |
| Seed-map and custody records | PASS |

Maximum staged-path error was `1.582067810090848e-14`. Maximum complete-data
component and recombination errors were `8.881784197001252e-16` and
`3.552713678800501e-15`. The 90-digit maximum posterior error was
`8.817394227044636961490944291270954018545398530904377260540376626279155591175E-15`.

The V3 suite passed `79/79`; the cumulative V2 suite passed `180/180`.

No seed was consumed. A-R1 (`3722000:3723999`), Population C, the tournament,
seeded Gate 4, Gate 5, and every escrow remain closed. The evaluator must
verify this package before authorizing A-R1.
