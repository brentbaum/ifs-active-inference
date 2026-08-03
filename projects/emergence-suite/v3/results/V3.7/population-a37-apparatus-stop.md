# V3.7 Population A37 apparatus stop

Verdict: **FAIL_APPARATUS_CUSTODY_STOP**. No scientific or calibration criterion was evaluated.

The runner serialized and fsynced seed 3734000, then opened the ordinary parallel dispatch for the remainder of the first stratum. A worker completed seed 3734001, but its returned row contained a nested Python `MappingProxyType`. The multiprocessing transport could not pickle that object and raised `multiprocessing.pool.MaybeEncodingError` caused by `TypeError: cannot pickle 'mappingproxy' object`.

This is runner serialization plumbing, not a scientific-model result. The persisted trace contains exactly one record, seed 3734000. Its SHA-256 is `dbac5c84327413d9e168a824e961a52240da264bd05b7648bcb051508a5df639`. The incremental hash-event ledger also contains exactly one record; its SHA-256 is `cf1a3333c3df06eb3911e07903b18f2c3f8facae4608e3c89aa3636c9a73013a`.

The exception proves that seed 3734001 executed far enough to return a result. Because the process pool may have prefetched work and no worker-side ledger was persisted before IPC transport, the exact set of any additional executed seeds cannot be established from custody artifacts. The block therefore cannot be resumed or reused without evaluator adjudication.

Population C37 and T37 were not opened. The registered prediction was not scored. Execution stops here.
