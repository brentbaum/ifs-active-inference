# DT-S1-IDGEN prediction-scoring formatter errata

The first seed-free report-formatting invocation wrote
`s1-prediction-scoring.json` and then stopped while constructing its Markdown
table because Python eagerly evaluated a `dict.get` default that referenced a
missing `falsifier` key on prediction rows. The repair changes only that label
selection to an explicit key branch.

No scientific module, world, trace, statistic, criterion, immutable verdict,
or prediction outcome changed. No seed was generated, consumed, rerun, or
rescored. The Markdown table was regenerated from the already immutable
`s1-verdict.json`.
