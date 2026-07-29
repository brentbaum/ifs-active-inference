# V2.5a Gate-3 decomposition repair diff

Authorization: `gate3-adjudication.md` section 3. The original Gate-3 execution and FAIL verdict remain unchanged.

The only scientific-code change is in the per-slice joint root trajectory used for the decomposition readout. It now updates with the bank state's declared `association_reliability`, matching the contract-facing composition endpoint, instead of calling the fixed-0.85 root posterior. No generator, endpoint, matching scan, target, marginal trajectory, likelihood table, prior, threshold, seed, or non-decomposition output changed.

Repaired identities within `1e-10`: `120/120`; maximum error `0.0`. Non-decomposition rows byte-identical: `120/120`.
