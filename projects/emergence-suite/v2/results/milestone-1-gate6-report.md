# Suite v2 milestone 1 — Gate 6 report

The three evaluator-revealed challenges were run in stage order against frozen
commit `60ba6e0`. All 85 frozen manifest entries were identity-checked;
`ref/`, contracts, protocols, and the original freeze manifests remain
unchanged. Gate-6 state is recorded only in new addenda.

## Verdicts

| Stage | Challenge | Verdict |
|---|---|---|
| V2.0 | C-V20 | PASS |
| V2.1 | C-V21 | PASS |
| V2.2 | C-V22 | FAIL |

## C-V20

- Exact filtered/smoothed parity maximum error:
  `2.63e-14` across
  `200` checks.
- O2 posterior reliability error:
  `0.0289`.
- Cumulative ≥1-nat structure wins: H1
  `47/50`, H2
  `50/50`.
- Collider mutation margins:
  `[24.615484825430876, 17.50940528883928, 7.3423821274853704]`.

Verdict: **PASS**.

## C-V21

- Crossing precision worlds:
  `60/60`.
- C-dominated integrated classifications:
  `0/60`.
- Paired post-midpoint accuracy effect:
  `0.469`
  with 95% interval
  `[0.415,
  0.524]`.
- Local-calibration intervals overlapped exactly; midpoint/regime information
  was not passed to inference.
- Two runner-side JSON serialization failures occurred after deterministic
  computation and are retained verbatim in the challenge report.

Verdict: **PASS**.

## C-V22

- Mean structure-recovery AUC:
  `1.000`.
- Broad-minus-narrowed root attribution:
  `0.236`
  with 95% interval
  `[0.227,
  0.244]`;
  local cue uptake differed by
  `5.55e-17`.
- Cue-1 structural transfer wins:
  `60/60`.
- Cue-5 floor-clean worlds:
  `29/60`
  (preregistered requirement: all worlds).
- Mediation passed in `11` null-root
  worlds; maximum transfer was
  `0.0082`.

Verdict: **FAIL**. The failure localizes to
absolute calibration of cue 5's learned non-association, not to a root-free
transfer route. In failed worlds, mean absolute association deviation from 0.5
was `0.0486`
versus `0.0161`
in passing worlds; absolute G revision correlated
`0.998` with
transfer.

## Stop

Gate 6 is complete. C-V20 and C-V21 passed; C-V22 failed its cue-5 floor
control with the failure retained and localized. No frozen code or contract was
changed, no seed outside the released blocks was used, and no commit was made.
Work stops here.
