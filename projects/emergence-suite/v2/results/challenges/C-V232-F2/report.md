# C-V232-F2 continuity challenge

Verdict: **FAIL**.

The frozen identity check passed for
`33` files at
`c67e853`. The committed continuity addendum
at `97098db` also matched byte-for-byte. All 100 released seeds,
`813301:813400`, were used: 50 D/P-discriminator worlds and 50
mixed-provocation worlds.

## Full distribution

Single-slice change is
`abs(q_t(P) - q_(t-1)(P))`, using the frozen prior `q_0(P)=0.25` at each
world's first slice.

| Population | n | p50 | p90 | p99 | max |
| --- | ---: | ---: | ---: | ---: | ---: |
| All slices | 5192 | 0 | 0.00866464349193 | 0.420233313444 | 0.573853084033 |
| Acute-event slices | 2200 | 5.79241827459e-05 | 0.124894106635 | 0.504448629302 | 0.573853084033 |

The corresponding world-cluster-bootstrap 95% intervals are retained in
`summary.json`, and every observed slice is retained in `per_slice.csv`.

## Three clauses

1. Acute-event exceedance rate: **FAIL**.
   `66/2200`
   acute slices exceeded `0.3345519502357523`, a rate of
   `0.030000`
   (95% Wilson interval
   `[0.023650,`
   ` 0.037988]`) against the
   `0.015` limit.
2. Multiplied empirical bound: **PASS**.
   `0` slices exceeded
   `1.75 × 0.3345519502357523 = 0.5854659129125665`; the maximum was
   `0.573853084033`. The exceedance-rate 95%
   Wilson interval is
   `[0.000000,`
   ` 0.000739]`.
3. Frozen analytic bound: **PASS**.
   `0` slices exceeded
   `3.801426508560692`; the maximum absolute pairwise slice log BF was
   `2.67055743142`. The
   exceedance-rate 95% Wilson interval is
   `[0.000000,`
   ` 0.000739]`.

## Localization

Per-seed and per-slice localization for every empirical-p99 exceedance and
every clause-(b) or clause-(c) violation is recorded verbatim in
`summary.json`; `per_seed.csv` gives world-level counts and maxima.
