## Attempt overview

| Attempt | Retained diagnosis or change | 43A | 43B | 43C | Stress |
|---|---|---|---|---|---|
| 1 | Three-edge draft; only 32 scenes for the 16-cell conditional table. Joint learning and action interaction were unstable. | null | null | not run | null |
| 2 | Independent 256-scene table training plus one `world-outcome` edge. Action interaction emerged, but a two-packet sample exhausted both endpoints and could not transfer to an untreated third component. | null | null | not run | null |
| 3 | Minimal two-edge chain and adaptive-release correction, still with 32 held-out episodes. Stress passed; paired empirical estimates remained noisy. | null | null | not run | support |
| 4 | Increased held-out evaluation to 64 episodes without changing coefficients or thresholds. | support | support | not run | support |
| 5 | Added the gated contextual Dirichlet action table and scaffold removal. The mean post-scaffold gain and first-action criterion passed, but an extra evaluator-only paired-win rule mislabeled 43C. | support | support | null | support |
| 6 | Removed the non-preregistered 43C paired-win rule; no model or data changed. | support | support | support | support |
| 7 | Final deterministic artifact rerun with full traces omitted from the pilot bundle and reserved for confirmation. | support | support | support | support |

All attempts used only seeds `16901:16910`. Confirmation seeds were never opened.

## 2026-07-15 20:03:26

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `null`
- Stage 43B pilot status: `null`
- Stress pilot status: `null`
- No confirmation seeds opened.

## 2026-07-15 20:07:11

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `null`
- Stage 43B pilot status: `null`
- Stress pilot status: `null`
- No confirmation seeds opened.

## 2026-07-15 20:10:20

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `null`
- Stage 43B pilot status: `null`
- Stress pilot status: `support`
- No confirmation seeds opened.

## 2026-07-15 20:11:39

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `support`
- Stage 43B pilot status: `support`
- Stress pilot status: `support`
- No confirmation seeds opened.

## 2026-07-15 20:15:27

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `support`
- Stage 43B pilot status: `support`
- Stress pilot status: `support`
- No confirmation seeds opened.

## 2026-07-15 20:17:01

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `support`
- Stage 43B pilot status: `support`
- Stress pilot status: `support`
- No confirmation seeds opened.

## 2026-07-15 20:18:32

- Seeds: `16901:16910`
- Configuration: repository defaults in `IFSBundleConfig`
- Stage 43A pilot status: `support`
- Stage 43B pilot status: `support`
- Stage 43C pilot status: `support`
- Stress pilot status: `support`
- No confirmation seeds opened.
