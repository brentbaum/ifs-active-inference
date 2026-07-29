# V2.6a Gate-2 apparatus repair diff

Authorization: `gate2-repair-authorization.md`.

- Recovery paths now sample the initial state from the frozen uniform prior
  and every subsequent state from the frozen `0.94/0.02` transition matrix.
- Emission generation, scorer inference, all likelihoods, priors, parameters,
  and thresholds are unchanged.
- Blocking Brier, ECE, and posterior-set coverage are evaluated per slice
  against realized `L_t`, using the unchanged V2.4.4 ten-bin
  maximum-confidence convention.
- Occupancy-majority recovery diagonals remain blocking. Occupancy-label
  Brier, ECE, and coverage remain in the report as descriptive quantities.
- The original Gate-2 files and FAIL verdict are unchanged. The repaired run
  writes new `gate-2-repaired*` files on fresh seeds `1230000:1231499`.
- A public-dummy regression independently reproduces the generated path from
  the frozen initial and transition probabilities.
