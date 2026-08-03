# V3.6 Round-15 apparatus-first repair statement

Classification: **GENERATOR_ONLY**  
Scientific interpretation: withheld pending Population A-R1  
A-R1 status: **CLOSED — NOT EXECUTED**

## Defect

The complete-native Population-A constructor selected the three-coordinate
`do(joint_policy)` schedule from the latent active-mode count. Active
coordinates alternated between 0 and 2; coordinates above the truth's active
count were set to 1. The scorer correctly treats joint policy as an
intervention, assigns no action-selection likelihood, and begins from the
unconditional frozen structure prior. The generated experimental design was
therefore informative about the truth while the posterior constitutionally
refused to treat that design as evidence. The complete prior-predictive
generator/scorer identity did not hold.

## Repair

The native constructor now uses `(policy_value, policy_value, policy_value)`
for every active-mode truth. This makes the intervention schedule
candidate-common. It is the same repair regardless of whether it raises,
lowers, or leaves unchanged any future calibration statistic.

The only other existing-file change is runner serialization: future
Population-A rows include `latent_mode_path`, `context_state_path`, prefix
observations, `contact_response_truth`, the intervention schedule, and masks.
That change exposes already-existing state for custody and complete-data
identity checks; it changes no generated value or inference.

## Exclusions

No scientific module, likelihood, prior, threshold, calibration estimator,
posterior aggregation, edge definition, readout, or criterion changed. The
eight frozen native-fixture families continue to pass. A-R1 and all other
seeded batteries and escrows remain unopened.

The exact applied generator diff is in
`results/V3.6/round15-generator-repair-applied.diff`.
