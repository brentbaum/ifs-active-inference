# V2.3.2-formation continuity empirical bound

**POST-GATE-6 FREEZE ADDENDUM.** This note supplies an omitted audit quantity. It does not alter the c67e853 freeze manifest, any frozen stage artifact, or the sealed-written C-V232-F verdict.

The frozen `ref.v232_formation.open_assays()` battery was rerun over its complete development seed block, 751000–751299. For every `score_history` trajectory actually invoked by that entrypoint, the recorded single-slice rate was

`abs(q_t(P) - q_{t-1}(P))`,

where `P` is the persistent candidate and the first change in each trajectory uses that call's declared prior (`q_0(P) = 0.25` throughout this battery). The pooled population includes 408 trajectories and 10,016 changes: 300 primary profiles, 100 high-control T profiles, four matched-statistic permutations, and four no-event trajectories of lengths 16, 64, 80, and 160.

Using `numpy.quantile(changes, 0.99, method="linear")` with NumPy 2.4.3:

- Empirical p99 single-slice change: **0.3345519502357523**
- Maximum observed single-slice change: **0.4327478291686412**

The machine-readable addendum contains the exact pooling definition and SHA-256 hashes of the frozen engine, parameter block, analysis plan, Gate-3 report, stage report, and base manifest. Its own SHA-256 is:

`8e45107a68fc84e6c723d9e9e5f2265cdacf6913908e5be2b3e6d5525f766d5b`
