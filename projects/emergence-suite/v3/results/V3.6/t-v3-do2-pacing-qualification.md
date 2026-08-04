# T-V3-DO2 pacing qualification

Verdict: **TWO_PROSPECTIVE_PACING_DESIGNS_UNABLE_TO_ESTABLISH_DYNAMIC_RANGE**.

Worlds: 4,000. Grid cells: 108. Selected: `null`.

The apparatus-only grid was evaluated once in its precommitted lexicographic
order. No imagery or do-over arm was generated, and no scientific timing
criterion was evaluated.

## Construct-condition accounting

| Construct condition | Cells passing | Cells evaluated |
|---|---:|---:|
| Interior crossing | 45 | 108 |
| Early floor | 108 | 108 |
| Endpoint dynamic range | 27 | 108 |
| Distributional spread | 90 | 108 |
| Event availability | 11 | 108 |
| Detectable opportunity | 0 | 108 |

The detectable-opportunity rate never reached the required 0.80. Its maximum
over the frozen grid was 0.001473. Thus no schedule could pass all six
conditions, even when its median crossing and event-availability conditions
passed. For example, grid cell 107 had `T=128`, diagnosticity `0.8`, correction
cadence `16`, half-length candidate-common masking, and precision `3.0`. Its
median crossing was 67 slices (`0.5234 T`), event availability was `0.9253`,
and early crossing was `0.0`, but endpoint success was `0.9373` and detectable
opportunity was `0.0`.

## Custody

- Seeds: `5200000:5203999`, ascending and gap-free.
- Persisted rows: 4,000, before aggregation.
- Trace SHA-256: `63caf43484c4676bcd4b487cf5e737e9d0f395478fdf39d4b1c9462ef6a8baef`.
- Trace-hash-event SHA-256: `bb51727dfee874a7505f8b587d663c608713c89f3e35b57d7ac54b0d20eb6b33`.
- Escrows opened: none.
