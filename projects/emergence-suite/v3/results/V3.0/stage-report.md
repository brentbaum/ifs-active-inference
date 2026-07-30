# V3.0 stage report

Status: **STOPPED_AT_GATE_5**. No freeze candidate exists.

- Stage 0: 2,000 barred pilot worlds. Macro accuracy 0.999179, ten-bin
  ECE 0.000112, and 95% posterior-set coverage 0.999786. Frozen Gate-2
  thresholds: accuracy 0.979, ECE 0.03, coverage 0.98.
- Gate 1: PASS. All eleven required semantic obligations passed. The primary
  bounded grammar contains 786,432 complete programs. Independent-oracle
  posterior error was 0; log-evidence error was 4.44e-16.
- Gate 2: PASS on 1,000 public worlds. Macro field recovery 0.999286, ECE
  0.000335, coverage 0.999929, and maximum exact-log-probability error
  1.28e-13.
- Gate 3: PASS. All composition cells recovered; the mixed
  drift-plus-recurrent-context cell compiled through R0 with disjoint cue
  subsets.
- Gate 4: PASS. All five production lesions were selective in 100/100 worlds
  and changed their declared target in 100/100.
- Gate 5: FAIL. The code-length-scale robustness cell failed only the
  exact-log-probability verification. The retained error is
  1.2473394093880898. The verification path used the default prior scale on
  one side; no repair was made.

Test status at stop: V3 tests 12/12 green; frozen V2 tests 180/180 green.
Escrow 4000000–4001999 was not accessed.
