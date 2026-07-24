# Experiment 46 magic numbers

- Pilot seeds: `18401:18410` (10 worlds).
- Confirmation seeds: `18501:18520` (20 fresh worlds).
- Witnessing-style corrective-evidence sessions: `12`.
- Corrective-evidence SD: `0.06`.
- Corrective target: `-0.35 ×` each initial coupling.
- Organization-only base coupling learning rate: `0.08`.
- Carrier plasticities (low/high): `0.0` / `0.3`.
- Maximum learning rate: `0.85`.
- Organization matching tolerance: `1.0e-12`.
- Revision-trajectory metric: RMS paired distance over both coupling coordinates and all `12` post-baseline sessions.
- Carrier-inert tolerance: `≤ 0.02`.
- Carrier-active required mean divergence: `≥ 0.1`.
- Power curve: two-sided alpha `0.05`, target power `0.8`, `20` matched pairs.
- Measurement-noise sweep: `0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3`.

Register frozen before confirmation: coupling plasticity is carrier; it is excluded from every organization component and organization measure.
