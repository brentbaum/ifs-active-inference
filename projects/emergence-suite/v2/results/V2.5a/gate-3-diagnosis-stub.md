# V2.5a Gate-3 honest stop

Blocking failures retained verbatim:

1. `assay2_median_ratio_monotone`: median `m*/n` was
   `[0.0625, 0.0625, 0.0625, 0.0625, 0.052083333333333336,
   0.052083333333333336]`. The association-dose label does not enter the
   frozen root-channel matching likelihood; the two high-dose cells moved
   downward under finite cell variation rather than remaining equal.
2. `assay3_information_matching_within_tolerance`: all 120 scans crossed
   the target, but only 103 were within the frozen `0.01` KL tolerance.
   Error median was `0.005347834072338131`, q95
   `0.19950524242254006`, and maximum `1.2075223097091734`. The nominal
   bridge contrast therefore cannot be called information-matched.
3. `assay3_exact_per_slice_decomposition`: only 56/120 worlds recombined
   within `1e-10`; maximum error was `0.2470998783239713`. In the worst
   retained world (seed `758569`), published increment sum
   `0.20752313512130238` did not equal the terminal contrast
   `-0.03957674320266891`.

This is a localization stub, not a repair or criterion amendment. Gates 4-5
were not opened.
