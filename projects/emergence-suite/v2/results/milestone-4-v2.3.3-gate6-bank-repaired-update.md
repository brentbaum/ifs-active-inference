# V2.3.3 Gate 6 bank repaired-instrument update

`C-V233-M-bank (repaired instrument)` verdict: **FAIL**. The authorized
seed-guard repair passed 82/82 cumulative tests and preserved open seed
760000 byte-for-byte. On the one repaired-instrument run, the 800 candidates
yielded 14 moderate, 33 strong, and 77 very-strong eligible worlds. Moderate
and strong therefore missed the sealed 40-world minimum; very-strong filled
at position 402 (seed 815402). Semantic integrity passed with zero provenance
error, and custody passed with a gap-free 800-row ledger and 800/800 bitwise
rehashes. The original `FAIL_UNEXECUTABLE` remains in the record. The
maintenance bundle and seeds `816001:816900` remain closed and untouched.
