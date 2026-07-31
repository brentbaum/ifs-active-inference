# V3.5 Gate 3 diagnosis stub

Gate 3 stopped honestly. No Gate-4 seed was opened.

- Registration policy movement was small and inside the frozen equivalence
  ROPE: mean `0.00056568`, 95% interval `[0.00020889, 0.00092213]`.
- The scientific structure posterior was not equivalent. The per-world
  maximum absolute structure-probability difference averaged `0.11144131`,
  with 95% interval `[0.10178371, 0.12148971]`, above the frozen `0.01` ROPE.
- Apparatus-first localization: the delivered registration channel is scored
  by the active-slot mode-conditional likelihood, whereas masking contributes
  likelihood one. It therefore supplies real mode evidence and, through the
  existing mode/root and outcome factors, changes structural weights. The
  failure is not an exact-arithmetic, trace, pairing, or sign-convention error.
- All nineteen mechanically frozen nonzero contrasts passed their point floors
  with lower 95% bounds above zero. Stakes left the scientific posterior
  exactly invariant (`0.0` maximum error); dormant-mode interventional
  influence was zero to `4.44e-16`.

This stub does not propose or implement a repair. The frozen criterion and the
observed failure are retained for evaluator adjudication.
