# V3.0 stage report

Status: **FREEZE_READY_AFTER_AUTHORIZED_GATE_5_SOFTWARE_REPAIR**.

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
- Gate 5 original run: FAIL retained. The code-length-scale robustness cell
  failed only the exact-log-probability verification, with error
  1.2473394093880898.
- Gate 5 repaired instrument: PASS. Under evaluator authorization, the
  existing hyperparameter was forwarded to the parity helper. The repaired
  error is 1.2789769243681803e-13. All non-parity quantities are byte-identical
  to the original run.

Final test status is recorded in `freeze-readiness.md`.
Escrow 4000000–4001999 was not accessed.
