# C-V23 Gate 6 report

Verdict: **FAIL**

The runner checked all 56 frozen
V2.3 files against commit `dee94c5` with zero
mismatches. It used seeds `807203` through
`807262` in all four cells, with 60 worlds per cell
and component streams paired within seed.

## Preregistered tests

1. **Joint formation boundary — FAIL.**
   Persistent evidence reached the `>= 1 nat` margin in
   `4/60` low-control worlds and
   `11/60` high-control worlds. The
   respective 95% Wilson intervals were
   `0.026`–
   `0.159` and
   `0.106`–
   `0.299`. This comparison
   uses the avoidance-unavailable replay cells, so controllability is the
   only cell difference.
2. **Continuity — FAIL.** Mean
   acute-slice posterior change was
   `0.057537` (95% interval
   `0.042103` to
   `0.072972`). The largest acute
   single-slice change was `0.517766949`, against
   the frozen bound `0.294529387`; there were
   `12` exceedances.
3. **Active persistence — FAIL.**
   Among `4` low-control formed paired
   worlds, unavailable-minus-available realized disconfirming-context
   encounter rate was
   `0.250000` (95% interval
   `-0.032902` to
   `0.532902`). The
   available-minus-replay end evidence margin was
   `1.016697` (95%
   interval `-2.665261`
   to `4.698655`).
4. **Mediation — FAIL.** Across
   `8` formed-world arm observations, the
   correlation between end persistence and realized avoidance was
   `-0.129` (95% interval
   `-0.764` to
   `0.633`). The partial
   correlation with scheduled dose after conditioning on realized avoidance
   was `0.619` (95%
   interval `-0.251` to
   `0.936`).

The matched replay shares every seed-generated context opportunity and
component uniform. Availability changes only whether a realized policy filters
a post-event encounter; the unavailable arm exposes the paired opportunity.
The mediation readout uses realized actions and threat-maintaining world
transitions only. Neither formation status nor any threshold enters inference.

## Failure localization

- `Test 1: the sealed joint formation boundary was not met (persistent evidence margin >= 1 nat in >=45/60 low-control and <=12/60 high-control worlds).`
- `Test 2: the acute-event persistent posterior did not rise with a 95% interval bounded above zero and no individual acute single-slice change above 0.294529387.`
- `Test 3: among low-control formed worlds, avoidance availability did not both reduce realized disconfirming-context encounters and increase the end persistent evidence margin with both paired 95% intervals bounded away from zero.`
- `Test 4: end persistence did not correlate positively with realized avoidance, or scheduled dose retained a non-null partial correlation after conditioning on realized avoidance.`

No frozen engine, stage, contract, parameter, result, tolerance, or manifest
file was modified.
