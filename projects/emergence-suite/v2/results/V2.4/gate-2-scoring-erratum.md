# V2.4 Gate-2 scoring erratum

This is an analysis-only annotation. The original `gate-2.json` and its
verbatim failure list remain unchanged.

The Gate-2 runner computed multiclass Brier as the mean, over worlds, of the
sum across five candidate classes:

`mean(sum((q-y)^2, axis=classes)) = 0.39580583437468875`.

The standing suite convention, used by V2.3.2 formation in
`ref/v232_formation.py`, is the mean over worlds and classes:

`mean((q-y)^2) = 0.39580583437468875 / 5`

`                 = 0.07916116687493775`.

Thus Brier passes the frozen `<=0.15` criterion on the inherited scale.
This correction requires no world rerun and changes no posterior, confusion
count, calibration value, or parameter result.

Gate 2 remains **FAIL**. Three recovery diagonals are below the frozen
`0.60` minimum:

- global down-weight: `0.56`;
- cue-local relearning: `0.49`;
- continuous drift: `0.59`.

The original Brier flag is retained as a software-scoring failure, not
silently removed. No Gate-3 seed was opened.
