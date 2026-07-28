# V2.3.3 implementation decisions

1. The scientific primitive contains only potential outcome `Y*`, availability
   `M` under `do(A)`, observed token `O`, and the inherited H/G evidence paths.
   Action-specific beta posteriors describe access only and never enter H.
2. Bank eligibility is a pure readout of the inferred V2.3.2 posterior. The
   constructor never assigns a stratum target or posterior value. Ascending
   intention-to-simulate processing and first-eligible retention are fixed.
3. Closed-loop B and yoked C reuse the same action, potential-outcome, and mask
   bytes. The scientific stores are therefore bitwise identical by construction
   and verified independently.
4. The masked-to-safe lesion is evaluated on the public corrective-safe support.
   Both paired arms receive the same fixed safe token; the lesion changes only
   missingness to delivery.
5. The public precision sweep multipliers are interpreted as the two declared
   table regimes: below baseline remains ordinary, baseline uses the frozen
   corrective profile, and above baseline uses overwhelm. No continuous
   likelihood table was invented.
6. Distributional update tails remain descriptive and non-criterial. They are
   never used to change a scientific, semantic, or custody verdict.
7. The sealed qualification population was not generated. Only the frozen open
   development block below 800000 was processed.
