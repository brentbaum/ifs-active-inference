# T-CAP1 Census-2 dynamics map

Status: **COMPLETE_NON_CRITERIAL_DYNAMICS_CENSUS_2**. This is a public, non-criterial census.

All 8000 worlds used arm-common latent paths. Regions are classified on paired `H_excess = H_transparent - H_matched-persistence`; raw H remains descriptive. Counts: `{"clear_hysteresis": 17, "near_boundary": 124, "no_hysteresis": 183}`.

## Frozen parameter panel

- **no_hysteresis**: cell 0, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.85, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.6}`, mean H_excess `-0.011911294077182367`
- **near_boundary**: cell 6, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.99, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.6}`, mean H_excess `0.06950136634382581`
- **clear_hysteresis**: cell 7, `{"allocation_persistence": 0.0, "bundle_transition_persistence": 0.99, "coupling_strength": 0.0, "cue_intensity": 0.25, "meta_observation_reliability": 0.8}`, mean H_excess `0.1119231662293037`

The excess-hysteresis grid spans all three frozen regions.

The explicit paired-initial-condition readout found two stable fixed points in
`2/8000 = 0.00025` transparent-feedback worlds and in `0/8000` represented,
matched-persistence, or no-feedback worlds. Thus region coverage in H-excess
does not by itself imply prevalent bistability; both results are retained.

The first lexicographic clear-region representative has coupling strength
`0.0`. This is reported verbatim and is not interpreted as evidence that
bundle-to-allocation feedback caused that cell's excess-H classification.

Trace SHA-256: `6ed237ad637d55480c221fa2d02f0044f29cf45d6bb24e7b672c74a147efc4b7`.
