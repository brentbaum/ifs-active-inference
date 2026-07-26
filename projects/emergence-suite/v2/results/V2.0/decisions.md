# V2.0 decision log

- “One generative model” is implemented as one typed `FiniteModel` and factor
  interface used by every protocol, not one fixed graph topology.
- Exactness uses sum-product elimination; the independent oracle directly
  iterates the Cartesian state product and does not call factor algebra.
- Finite model complexity is the gap between maximized likelihood and
  parameter-integrated evidence on a nested Bernoulli pair.
- Protocol metadata is immutable and non-scientific. Scientific results are
  retained only in the three permitted stores; report metrics are pure
  serialization-time readouts.
- Development seed blocks are contiguous and stage-specific: 1200–1263.

