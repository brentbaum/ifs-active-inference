# C-V36A sealed challenge verdict

Immutable sealed verdict: **PASS**.

## Criterion results

1. **PASS** — root_evidence_uptake mean full-minus-ablation 0.454680771473, whole-world bootstrap 95% CI [0.446185807699, 0.462889784553] over 800 same-seed pairs.
2. **PASS** — root_transfer mean full-minus-ablation 0.318040435111, whole-world bootstrap 95% CI [0.311459672944, 0.324229094212] over 700 same-seed pairs.
3. **PASS** — q_current_edge_absence mean full-minus-ablation 0.612935058767, whole-world bootstrap 95% CI [0.598481665998, 0.62768379585] over 700 same-seed pairs.

4. **PASS** — all required single-mode readouts were finite in every world. Cross-mode fingerprints are descriptive only:

   - `opposed_D_0_1`: mean 0; median 0; 5th–95th percentile [0, 0]; range [0, 0].
   - `opposed_D_1_0`: mean 0; median 0; 5th–95th percentile [0, 0]; range [0, 0].
   - `allied_D_0_1`: mean -0.00220580519979; median -0.000135048401804; 5th–95th percentile [-0.012346969413, -3.21028487927e-06]; range [-0.0699585266764, 0.0014868924615].
   - `allied_D_1_0`: mean -0.00178308816776; median -9.72502501916e-05; 5th–95th percentile [-0.00938660219003, -2.0638796937e-06]; range [-0.0672043792892, 0.00305840565487].

5. **PASS** — 3,000 unique seeds were consumed once, ascending and gap-free. The raw trace and event-ledger hash stream were fsynced before aggregation. Escrow 4103000:4109999 is retired unconsumed.

## Verdict classes

- Scientific: **PASS**
- Semantic/reporting: **PASS**
- Custody: **PASS**

## Interpretation

The immutable result above is retained as written. The three paired cells localize the regulated-evidence, cue-only-transfer, and structural-pruning pathways at single-mode scale. The fourth cell reports posterior-model-averaged cross-mode fingerprints without imposing a zero floor, exactly as sealed.

Raw trace SHA-256: `f951200ecf0cafc97e7ebece6c25fb85951e88da1efb24cc7ab57b7014078c93`.  
Event-hash ledger SHA-256: `7c031b63f6fa5400901620379599d8f0116e0eb0ee220fd321863b73496dc47b`.
