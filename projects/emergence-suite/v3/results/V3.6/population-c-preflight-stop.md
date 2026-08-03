# V3.6 Population C apparatus stop

Status: **HONEST_STOP_APPARATUS_BLOCK_CARDINALITY_MISMATCH**.

Population A-R1 passed on the authorized final block `3722000:3723999`
(2,000/2,000 worlds serialized; all blocking criteria passed). The serial
sequence then opened Population C on its authorized replacement block
`3694001:3695999`.

The block contains 1,999 seeds. The frozen external-world constructor accepts
only a 2,000-world qualification population or a 6,000-world tournament
population. Its `_external_stratum` preflight therefore raised:

> external population must contain 2,000 or 6,000 worlds

This occurred on the first requested seed, before diagnosticity selection and
before any component RNG draw. No world was generated, no criterion was
evaluated, and no Population-C seed was consumed. The incremental trace file
had already been opened and is retained as a zero-byte custody artifact with
SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.

This is an apparatus mismatch between the evaluator-authorized replacement
interval and the constructor's frozen population-size contract. It is not a
scientific result. No repair, block resizing, retry, or substitution is
authorized here. The tournament, Gate 4, Gate 5, compatibility attestations,
freeze manifest, and all escrows remain unopened pending evaluator
adjudication.
