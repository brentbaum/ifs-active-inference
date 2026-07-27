# V2.3.2 decisions

- The frozen F and M subclaims are scored independently; neither can rescue
  the other.
- Actions and observation modes are interventions and are excluded from
  environmental evidence.
- The efficacy spike is the exact `eta=0` finite candidate. No epsilon,
  threshold, or posterior clamp is used.
- The formation inference API accepts theory variables only. Schedule
  regularity, timing, ordering, length, seed, and assay labels are absent.
- The Gate-2 stop rule is applied to the frozen seed blocks without
  temperature tuning, seed-stream substitution, or Gate-3 population
  substitution.
