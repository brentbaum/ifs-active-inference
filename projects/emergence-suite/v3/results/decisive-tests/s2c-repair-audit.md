# S2-C runner repair differential audit

Authority: Round-26 rulings 26.3–26.4. The original S2-C record remains
`FAIL_APPARATUS_ESTIMAND` and is not edited.

The repair is confined to the S2 apparatus runner. The persistent forced-contact
latch is replaced by a flag that is true on the single probe slice only. The
registered contact endpoint is now contact strictly after that probe. The
low-permission arm conditions the controller's declared policy on requesting
vulnerable contact and samples the action through the ordinary controller-choice
path; it no longer replaces an already selected action.

The replacement-block plumbing, zero-seed conformance proof, trace persistence,
and replacement aggregation are also runner-side additions. No likelihood,
prior, scientific posterior, threshold, ROPE, or registered direction changed.
`internal_policy_posterior` and `access_probability` are unchanged.

All frozen scientific hashes (`ref/v31.py` through `ref/v36.py`) match the
recorded values. The two S2 design-freeze hashes remain
`4e12c4f502586f7e88d222cb92da5ea43ca39ae55765ccf3389b3569ed201180`
and `7b62b78a0c3df6b3f9eea0804cbe83b6a48157e1e590781cceb23fdf66d94e65`.

After the immutable replacement verdict had been written, prediction-table
rendering hit a report-only `dict.get` default-expression `KeyError`. The
conditional label expression was corrected and the table was generated from
the retained verdict. No seed, trace, statistic, criterion, or verdict was
recomputed.
