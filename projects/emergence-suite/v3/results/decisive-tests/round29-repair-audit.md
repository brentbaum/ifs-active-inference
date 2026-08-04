# T-CAP1 round-29 repair audit

Classification: **RUNNER_READOUT_ONLY**. The original Census-1 traces and
apparatus stop remain retained.

The repair changes three things only. World and potential-observation random
keys are now arm-invariant; only allocation keys vary by arm. Each arm now runs
paired low (`.02`) and high (`.98`) initial bundle-posterior trajectories and
computes stability and final separation directly. Census-2 classifies cells on
paired `H_excess = H_transparent - H_matched-persistence`; raw hysteresis is
still reported.

The two T-CAP1 scientific productions, all emission and likelihood functions,
and posterior updating retain their pre-repair source hashes listed in the JSON
audit. Frozen v3.6 hashes also remain unchanged. The 324-cell parameter grid,
region boundaries, and all likelihood constants are unchanged.
