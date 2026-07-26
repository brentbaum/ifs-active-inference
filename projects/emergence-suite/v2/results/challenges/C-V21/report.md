# C-V21 Gate 6 report

Verdict: **PASS**

Frozen identity: 29 files checked
against `60ba6e0`, zero mismatches.

## Preregistered dissociations

- Tracking: PASS;
  crossings `60/60`
  (95% Wilson interval `0.940`–
  `1.000`).
- Miscalibration containment:
  PASS;
  C-dominated integrated classifications
  `0/60`.
- Broadcast dissociation:
  PASS;
  post-midpoint accuracy effect
  `0.469`
  (95% interval
  `0.415`–
  `0.524`).
  Local calibration intervals overlap exactly because the local calculation is
  paired and unchanged.
- No-label audit: PASS;
  inference received only `['counts', 'local_monitor_observations', 'broadcast']`.

## Failure interpretation

No preregistered dissociation failure was triggered.

## Retained runner execution failure

The first serialization attempt failed after deterministic computation:

```text
Attempt 1:
Traceback (most recent call last):
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py", line 446, in <module>
    result = main()
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py", line 440, in main
    write_json(result_dir / "summary.json", summary)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/common.py", line 110, in write_json
    json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Object of type bool is not JSON serializable
when serializing dict item 'passed'
when serializing dict item 'broadcast_dissociation'
when serializing dict item 'tests'
Attempt 2:
Traceback (most recent call last):
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py", line 464, in <module>
    result = main()
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/run_c_v21.py", line 458, in main
    write_json(result_dir / "summary.json", summary)
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/brentbaum/dev/research/ifs-active-inference/projects/emergence-suite/v2/challenges/common.py", line 110, in write_json
    json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    ~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
TypeError: Object of type bool is not JSON serializable
when serializing dict item 'passed'
when serializing dict item 'broadcast_dissociation'
when serializing dict item 'tests'
```

The successful serialization changed only runner-side NumPy scalar conversion.

No frozen engine, stage, contract, tolerance, or manifest file was modified.
