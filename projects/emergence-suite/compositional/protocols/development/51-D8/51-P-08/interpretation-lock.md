# 51-D8 open development — self-like local monitoring

Contract: `ifs-ai-experiment-51-contract@1.0.1`
Challenge: `51-P-08`
Decision rules: `budget-valid`, `ordering-observed`, `local-calibration-preserved`, `depth-separates`, `root-revision-selective`

## Success

The same local-monitor variable remains within `0.10` across arms while
broadcast-on exceeds broadcast-off on global depth and terminal root revision
by at least `0.10`. The declared evidence budget and access-before-root audit
also pass.

## Scientific failure

Local monitoring changes when only its outgoing broadcast is severed, global
depth does not separate, root revision is not selective, or event ordering and
budget checks fail. No local-monitor bonus is introduced.

## Semantic inexpressibility

The broadcast lesion, local/global/root trace fields, paired evidence budget,
event ordering, or declared analysis cannot execute through the public
interface.
