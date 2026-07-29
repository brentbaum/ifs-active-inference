# V2.5a development failures

## Stage-0 pilot preflight — process-pool constructor

The first pilot invocation stopped before any world was generated. Python
3.14's `ProcessPoolExecutor` called `os.sysconf("SC_SEM_NSEMS_MAX")`, which
the sandbox denied with `PermissionError: [Errno 1] Operation not permitted`.

Seeds consumed: **zero**. Scientific scores computed: **zero**. Criteria
evaluated: **none**.

The orchestration layer was replaced with the subprocess-partition pattern
already used by the frozen V2.4 runners. No generator, likelihood, prior,
presentation definition, matching definition, threshold, seed, or world
ordering changed.
