# V3.3 development failures

## Stage 0 — do-over acceleration unattainable

- Pilot block: `3300000:3301999`, fully traced and barred.
- Mean paired proportional speedup: `0.0`.
- First-material times were identical in every paired world.
- All material crossings occurred before the post-revision do-over opportunity.
- Gates 2–5 and escrow were not opened.

## Gate 3 — event-indexed acceleration did not generalize

- Repair pilot block: `3330000:3331999`, fully traced and barred.
- The one-shot repair pilot had a positive but very small mean proportional
  speedup of `0.0005`; its frozen positive floor was `0.00025`.
- Gate 2 passed all recovery, calibration, coverage, exactness, and independent
  oracle criteria on `3302000:3304999`.
- In Gate 3, `799/800` paired worlds had speedup `0`; one had speedup `-0.25`.
  Mean speedup was `-0.0003125`, with 95% whole-world bootstrap interval
  `[-0.0009375, 0.0]`.
- The suggestion-only root-revision sign check also failed: mean
  historical-minus-current root estimate was `-0.007463967250969002`.
- Gates 4–5 and escrow remained unopened.

## Gate 5 — adjudicated findings repeated

Under the committed mixed-verdict continuation, both Gate-3 failures remained
non-blocking and repeated without rescue:

- timely do-over speedup was exactly `0.0`, 95% interval `[0.0, 0.0]`, below
  the frozen `0.00025` floor;
- suggestion root direction was `-0.004940118398975422`, 95% interval
  `[-0.0117681634573112, 0.001722225536766276]`, against the frozen positive
  direction.

Every blocking Gate-4 and Gate-5 criterion passed. These repetitions remain
scientific limitations in the freeze candidate.
