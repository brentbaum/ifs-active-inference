# V3.1 repaired Gate-4 diagnosis stub

Status: **GATE 4 FAIL — IDENTITY-EDGE SELECTIVITY**.

The authorized lesion-support repair passed its required semantic checks:

- candidate-common masking error for the deleted mode channel: `0.0` at
  tolerance `1e-10`;
- all mode-slot-lesioned evidences and posterior probabilities were finite;
- maximum normalization error was `7.33e-15`;
- the mode-slot target disappeared exactly.

All 2,000 assigned Gate-4 seeds were consumed once in six disjoint cells. Five
lesions passed. The identity-edge lesion failed its survival criterion:

- part-like posterior mass after lesion: exactly `0.0` in 333/333 worlds;
- finite normalized posterior: 333/333;
- `W→Y` posterior change below `0.20`: 182/333 worlds
  (`0.5465465465465466`), below the blocking `0.90` survival floor.

Apparatus-first localization: the lesion removes `M1→G`, `G→W`, `G→A`, and
`G→Y` productions from the hypothesis space. It does not delete `W→Y`.
Nevertheless, exact finite model comparison renormalizes over the restricted
candidate space. Posterior mass on the retained `W→Y` production can therefore
move when competing identity-bearing programs disappear. The current
selectivity statistic treats an absolute `W→Y` posterior movement above
`0.20` as loss of an undeclared consequence.

This record does not decide whether that movement is a genuine nonselective
lesion effect or whether the survival statistic confuses posterior
renormalization with production deletion. No threshold was changed, no
additional criterion seeds were scored, and Gate 5 was not opened.
