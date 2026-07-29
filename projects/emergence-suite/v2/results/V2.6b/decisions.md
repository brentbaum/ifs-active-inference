# V2.6b decisions

1. `T_outcome`, `T_coprotection`, and `T_partner` are three separate exact
   binary posteriors. The learnable policy-outcome success parameter has a
   three-point exact posterior.
2. The frozen `ref.v26a.score` supplies partner-state inference,
   co-regulation, future precision, and root uptake. The frozen
   `ref.v234.score` supplies danger and action-efficacy inference. Neither
   primitive was reimplemented.
3. Refusal without a delivered partner response has likelihood one for
   `T_partner`. The protector cannot infer partner policy from its own refusal.
4. Stakes enter only the expected-cost policy calculation. Inferred action
   efficacy enters only counterfactual future risk.
5. `block`, `test_contact`, and `permit_contact` form one exact finite policy
   posterior. Permission mass and contact probability are pure readouts;
   there is no gate, permission, access, or protector-role scientific field.
6. Contact probability is the exact policy-consequence mixture over the
   frozen per-policy contact probabilities. Policy selection is never an
   evidence likelihood.
7. Protector-present and protector-absent futures receive the identical hope
   constant. Their differential is fully determined by danger, inferred
   efficacy, co-protection trust, and the V2.6a future-precision forecast.
8. The independent oracle copies every prior, support, and cost input before
   enumeration. All semantic comparisons use the declared `1e-10` tolerance.
9. Every rate/effect floor and ceiling was piloted on the four public blocks
   declared in the parameter file before its assigned gate opened. All pilot
   blocks are permanently barred from criterion evaluation.
10. The managed sandbox denied process-pool semaphore inspection, so ordered
    thread execution was used. Seed order and scientific computations were
    unchanged.
11. Escrow `2050000:2052999` was not accessed.
