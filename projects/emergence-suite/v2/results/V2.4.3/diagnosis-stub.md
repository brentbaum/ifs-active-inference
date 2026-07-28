# V2.4.3 Gate-3 stop — diagnosis stub

Status: **official honest stop at Gate 3**. Gates 1–2 passed. Gate 4 was
not run. No threshold, family, likelihood, transition, prior, bridge
equation, or root-transfer mechanism was changed after seeing these data.

Failures retained verbatim from `gate-3.json`:

- `bma_global_downweight`
- `bma_cue_local_relearning`
- `bma_context_split`
- `bma_continuous_drift`
- `bma_change_point`
- `cs_margin`
- `genuine_shuffle_control`
- `bridge_shuffle`

Immediate apparatus localization:

1. Every exact family's whole-world bootstrap upper bound for mean
   generator-family BMA regret exceeded `0.01` nats/token: GW `0.02069`,
   CL `0.02699`, CS `0.03616`, DR `0.02701`, CP `0.03422`.
2. The CS matched point margin had mean `0.03438`, but its 95% interval
   `[-0.00068, 0.07080]` failed the frozen positive-lower-bound criterion.
3. Genuine then/now material redescription passed (`0.7083`) and the formed
   bridge passed (`0.6750`). Genuine single-regime controls passed exactly
   (`0.0` material rate), but conditional-product shuffled controls did not:
   neutral `0.4500`, formed-bank `0.4667`.
4. DR/CP raw-CS and material-redescription controls passed; the dedicated
   96-slice CL recovery (`0.8167`) and material control passed.

These are numeric/scientific failures under the frozen V2.4.3 construct.
Per the stop rule they do not authorize changing `0.80`, `4.0`, `0.60`,
`0.10`, or `0.01`, and no V2.4.4 work follows automatically.

Both finite-information bounds remain unchanged:

- `B_max_inherited_formation = 3.801426508560692`
- `B_max_v24_common_emissions = 6.704414354964107`
