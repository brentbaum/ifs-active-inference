# V2.5a completion Gate-1 diagnosis stub

Gate 1 stopped before Gate 2. No seed in `1020000:1020799` was opened.

The two failed checks are localized to the runner's use of bitwise array
identity for analytically neutral posteriors:

- An all-missing joint episode had log evidence exactly `0.0`, per-slice
  structural log BF exactly `0.0`, and `q(H_cfg)=[0.5,
  0.5000000000000001]`. The deviation from the declared prior was
  `1.1102230246251565e-16`.
- A marginal presentation had `q(H_cfg)=[0.49999999999999956,
  0.5000000000000004]`. Its maximum deviation from the declared prior was
  `4.440892098500626e-16`; `q(G)=[0.5,0.5]`.

Both are far inside the frozen semantic tolerance `1e-10`, but proofs 6 and
8 used `numpy.array_equal`, imposing an undeclared bit-identity criterion.
The likelihood decomposition itself is neutral: every missing component
likelihood is exactly one, and all marginal component likelihoods are
identical. This is an apparatus-first localization only; no repair or
criterion reinterpretation was performed after the failed execution.

The first nontrivial numerical obligations all passed: normalization error
`2.220446049250313e-16`, exact-marginal error
`8.93729534823251e-15`, independent-oracle error
`3.552713678800501e-15`, posterior-odds error
`8.881784197001252e-16`, and partition recombination error
`1.7763568394002505e-15`.

