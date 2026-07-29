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

## Gate-5 manifest-chain verifier stop

The completed Gate-5 execution stopped on
`V2.4.4_manifest_identity`. Its verifier checked the 86-entry V2.4.4 base
manifest without applying the committed freeze-manifest addendum, so it
compared the superseded freeze-readiness hash against the post-sign-off file.
Every scientific, semantic, robustness, cumulative, R0, and unit-suite check
passed. The full `761000:763999` block was already consumed. The stop is
retained pending external repair-class adjudication; no rerun or freeze
packaging followed.
