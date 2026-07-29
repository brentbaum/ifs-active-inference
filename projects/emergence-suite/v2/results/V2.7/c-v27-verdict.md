# C-V27 immutable sealed verdict

Immutable verdict: **FAIL**.

The raw traces were sealed and hashed before any criterion was evaluated.

## Sealed criteria

- `criterion_1_topology`: **PASS** — `{"normalization_max_error": 6.661338147750939e-16, "topology_recovery": 0.808}`
- `criterion_2_mandate`: **PASS** — `{"mandate_recovery": 0.90875}`
- `criterion_3_coalition`: **PASS** — `{"access_minus_exiling_arm": {"left_count": 800, "lower_95": 0.18821383958381105, "mean": 0.19205099665424719, "right_count": 400, "upper_95": 0.19588815372468332}, "exiling_mass": {"count": 800, "lower_95": 0.4615339597780114, "mean": 0.470087116496346, "upper_95": 0.47864027321468056}}`
- `criterion_4_registration`: **FAIL** — `{"matched_access_max_error": 0.039325046872218494, "matched_descent_max_error": 0.035608965356392075, "support_on_minus_off": {"count": 400, "lower_95": 0.5, "mean": 0.5, "upper_95": 0.5}}`
- `criterion_5_befriending`: **PASS** — `{"access_both_minus_none": {"count": 400, "lower_95": 0.06886168522953866, "mean": 0.07032515289973382, "upper_95": 0.07178862056992898}, "exiling_both": {"count": 400, "lower_95": 2.7665342219004486e-06, "mean": 2.953471065353461e-06, "upper_95": 3.1404079088064735e-06}, "exiling_none": {"count": 400, "lower_95": 0.0014038415324992616, "mean": 0.001504172930801588, "upper_95": 0.0016045043291039143}}`
- `criterion_6_exiling_descent`: **PASS** — `{"exiling_arm_access": {"count": 400, "lower_95": 3.769725941656011e-08, "mean": 3.9359010815423675e-08, "upper_95": 4.1020762214287236e-08}, "exiling_arm_mass": {"count": 400, "lower_95": 0.9999997265285763, "mean": 0.9999997376068924, "upper_95": 0.9999997486852086}, "permit_arm_access": {"count": 400, "lower_95": 0.8999852646848433, "mean": 0.8999853630892056, "upper_95": 0.899985461493568}, "permit_arm_descent": {"count": 400, "lower_95": 0.8149397562210197, "mean": 0.8149398453265085, "upper_95": 0.8149399344319974}, "permit_minus_exiling_access": {"count": 400, "lower_95": 0.8999852254113833, "mean": 0.8999853237301949, "upper_95": 0.8999854220490066}}`
- `criterion_7_semantic_custody`: **PASS** — `{"ascending_gap_free": true, "challenge_hash_verified": true, "constitution_passed": true, "consumed_count": 5000, "forbidden_source": {"exile_force": false, "gate_object": false, "polarization_coefficient": false}, "freeze_identity_passed": true, "one_posterior_audited_worlds": 5000, "released_by": "suite-v2-sealed-hashes.md C-V27 record, commit c8c1063", "scientific_state_violations": []}`

## Verdict classes

- Scientific: **FAIL**.
- Semantic: **PASS**.
- Distributional stress: reported cell-by-cell in the immutable criteria; no pooled replacement.
- Process custody: **PASS**.

Full fast suite: **PASS**.

Named bounds: `{"B_max_v232_formation": 3.801426508560692, "B_max_v24_common_emissions": 6.704414354964107, "B_max_v27_registration": 2.1972245773362196, "B_max_v27_shared_outcome": 3.8}`.
