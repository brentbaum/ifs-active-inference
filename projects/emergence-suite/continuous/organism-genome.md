# Experiment 50-H organism genome

`genome.toml` is the sole numeric genome for the strain. Every numeric constant is represented as a `constants.<name>` table with a `value` and a one-line `rationale`; the loader rejects missing rationales, duplicate names, non-finite values, and assay-local numeric overrides.

The genome combines inherited frozen settings with a small number of 50-prospective settings. Provenance is recorded directly in each rationale. Analysis thresholds and world-count commitments are included even though they are not agent-side parameters, so the freeze package has no unrecorded authored numeric choices. Assay configuration files contain topology and intervention labels only.

Phase 0 may replace a value only through an entry in `results/model_organism/calibration-ledger.csv` whose consulted quantity is an apparatus-first dynamic-range measure. In this Stage A freeze candidate, joint calibration retained the listed values; no criterion statistic was consulted.

The strain identifier is `50-H-stage-a-v1`. A runner accepts the genome only when its SHA-256 matches the hash recorded in `results/model_organism/identity.json` and the freeze manifest.
