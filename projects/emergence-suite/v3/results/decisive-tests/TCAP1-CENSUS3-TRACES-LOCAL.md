# T-CAP1 Census-3 local trace custody

The raw Census-3 trace bundle is retained locally because it is 531 MB, above the repository's practical file limit:

- `tcap1-stage1c-census3-traces.jsonl`
- 12,000 rows
- SHA-256 `6d2ac75417b362b298568c5695b4328eb6c4795e5af0c7a7be6730f2df1b99fb`

The committed custody artifacts are `tcap1-stage1c-census3-trace-hashes.json` and `tcap1-stage1c-census3-trace-hash-events.jsonl`. They contain the aggregate trace hash and every per-row hash. The census summary was computed only after all rows and hash events were persisted and fsynced.
