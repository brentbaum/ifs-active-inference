# V3.4 stage-0 software-repair diff

Authorization: `stage0-repair-authorization.md`.

The scientific likelihood, priors, thresholds, structure space, and scorer are
unchanged. The repair changes only the Bernoulli parameter used when the
recovery generator emits the binary root-evidence observation:

```text
before: p passed to Bernoulli = p(O_G = G | G, L, Z)
after:  p passed to Bernoulli = p(O_G = 1 | G, L, Z)
```

Therefore the repaired generator emits `O_G=1` with probability `c` for
`G=1`, and with probability `1-c` for `G=0`, exactly as the frozen scorer
declares.

The regression test enumerates both root values, all four partner states, all
16 structures, and both broadcast values. It verifies that the generator's
Bernoulli parameter equals the scorer's `p(O_G=1)` and that the two observed
outcome probabilities sum to one within `1e-10`.

The consumed defective pilot and its stop record remain unchanged. The
corrected pilot uses only the evaluator-authorized replacement block
`3430000:3431999` and writes distinct `stage0-pilot-repaired-*` traces and
results.
