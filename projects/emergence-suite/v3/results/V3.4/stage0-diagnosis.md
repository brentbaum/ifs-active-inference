# V3.4 stage-0 diagnosis — recovery generator/scorer mismatch

## Verdict

`STOPPED_AT_STAGE0_GENERATOR_SCORER_MISMATCH`

Gate 2 was not opened. No seed in `3402000:3419999` was consumed, and the
C-V34 escrow block `4040000:4043999` remains untouched.

The original traced pilot output is retained verbatim in
`stage0-pilot.json`. Its descriptive pass label is invalid for progression:
the pilot exposed a mismatch between the recovery generator and the scorer,
and the subsequently written root-recovery floor is not attainable under the
observed pilot population.

## Apparatus-first localization

The scorer declares a Bernoulli likelihood for a root-evidence observation:

```text
p(O_G = G | G, L, Z) = c(L, Z)
p(O_G != G | G, L, Z) = 1 - c(L, Z)
```

where `c(L, Z) = 0.5 + ROOT_GAIN * precision(L, Z)`.

The recovery generator calls:

```text
bernoulli(root_probability(root_state, root_state, ...))
```

The return value of `bernoulli(p)` is the observed bit `O_G`, so its argument
must be `p(O_G = 1 | G, ...)`. The current expression instead supplies
`p(O_G = G | G, ...) = c` for both values of `G`.

Consequently:

- when `G=1`, the generator correctly samples `O_G=1` with probability `c`;
- when `G=0`, it incorrectly also samples `O_G=1` with probability `c`,
  whereas the declared scorer requires probability `1-c`.

The recovery generator therefore makes root observations favor `G=1`
regardless of the sampled truth. This is a generator/scorer mismatch, not an
inference-calibration result.

The partner path, structure draw, and other observation channels are not
implicated by this localization.

## Pilot evidence

The traced recovery pilot used 800 worlds from `3400000:3400799` and reported:

| Quantity | Observed |
|---|---:|
| root-state accuracy | 0.475 |
| root ECE | 0.30359522775662495 |
| structure ECE | 0.03205292404059635 |
| structure-set coverage | 0.98375 |
| minimum edge accuracy | 0.8775 |
| exact-program accuracy | 0.81875 |
| partner-state accuracy | 0.9690885416666667 |

The near-one-half root accuracy is the expected signature of the localized
error: truth-1 worlds are generally classified correctly and truth-0 worlds
are generally pushed toward root state 1.

The threshold-freezing code then applied an authored lower bound:

```text
root_accuracy_min = max(0.70, floor((pilot_root_accuracy - 0.05) * 100) / 100)
                  = 0.70
```

Thus it froze a 0.70 floor after the exact planned pilot attained only 0.475.
That violates the standing requirement that every rate/effect floor be shown
attainable before criterion worlds. The pilot's
`DESCRIPTIVE_ATTAINABILITY_PASS` label is retained as written but cannot
authorize Gate 2.

## Required repair class

The narrow prospective repair would change only recovery generation of the
root-evidence bit so that it samples the declared scorer likelihood:

```text
p(O_G = 1 | G, L, Z)
```

It would also require a fresh, evaluator-authorized traced pilot block and
fresh threshold freezing. The consumed pilot cannot validate a corrected
generator. No such repair or replacement seed authorization was supplied in
this run, so no repair was made.

## Custody

- Pilot recovery: `3400000:3400799` consumed and traced.
- Pilot assay sets: `3400800:3401999` consumed and traced.
- Gate 2: unopened.
- Gate 3: unopened.
- Gate 4: unopened.
- Gate 5: unopened.
- C-V34 escrow: unopened.

Both V3.4 finite-information bounds remain descriptive declarations:
`B_max_v34_relational = 3.8066624897703196` and
`B_max_v34_root = 1.9736255489018601`.
