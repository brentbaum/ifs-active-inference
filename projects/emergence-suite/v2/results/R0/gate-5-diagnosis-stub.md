# R0 Gate-5 diagnosis stub

**Status:** blocking stop after the first Gate-5 execution  
**Observed verdict:** `FAIL`  
**Stage:** V2.G0 apparatus only  
**Escrow accessed:** no  
**Diagnosis-reserved seeds accessed:** no

## Immutable observed result

`run_v2g0_gates.py 5` executed the full public Gate-5 block
`1004000:1009999` once and wrote `gate-5.json`.

The recorded results are:

- all 6,000 R0 custody worlds executed with zero RNG-custody failure;
- no tracked pre-R0 file differed from the current committed tree;
- the complete old-plus-new unit suite passed:
  `126` tests in `422.145s`;
- the V2.4.4 base-manifest-only audit reported one mismatch;
- escrow was untouched.

The immutable top-level verdict is `FAIL`.

## Failure localization

The Gate-5 verifier reads `results/V2.4.4/freeze-manifest.json` but does not
apply the committed `results/V2.4.4/freeze-manifest-addendum.json`.

The base manifest records:

```text
results/V2.4.4/freeze-readiness.md
d4a2ba54f505759a37242ee02973a299af5d2bb3b1886dd97d72f87f98acea1a
```

The later committed addendum supersedes that entry with:

```text
results/V2.4.4/freeze-readiness.md
f350531534e38718f2c31973e1d96416e51de6d080fad441cae8ebe7c97c83f2
```

The current file hash is exactly the addendum hash:

```text
f350531534e38718f2c31973e1d96416e51de6d080fad441cae8ebe7c97c83f2
```

Git reports no modification to that file and no modified pre-R0 file. The
failure therefore localizes to incomplete manifest-chain verification, not a
change to a frozen artifact.

## Provisional taxonomy

**Provisional classification:** pure software error in the Gate-5
byte-identity verifier.

A prospective repair would overlay the committed V2.4.4 manifest addendum on
the base manifest before hashing, record both custody files, and leave every
world, scientific result, inherited file, gate criterion, and seed unchanged.
No repair or rerun is performed here.

## Stop custody

- Original Gate 3 `FAIL` remains retained.
- Authorized repaired Gate 3 is recorded as `PASS` with byte identity.
- Gate 4 is recorded as `PASS`.
- Gate 5 remains recorded as `FAIL` pending adjudication/repair authorization.
- Gate-5 seeds `1004000:1009999` have been consumed by the recorded execution.
- Diagnosis block `1010000:1019999` is untouched.
- C-V2G0 escrow `2000000:2000499` is untouched.

