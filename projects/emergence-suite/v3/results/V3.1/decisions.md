# V3.1 decisions

1. V3.1 uses the 128-program region of the V3.0 grammar formed by one optional
   mode and six ordinary edges. No named formation candidate was introduced.
2. T/D/P descriptions are exact posterior-region sums and never enter
   inference.
3. `G_A` is learned from a typed policy-proposal observation. Intervened
   actions themselves have no selection likelihood.
4. Censoring removes only outcome evidence. Missing outcomes contribute
   exactly zero outcome-structure BF.
5. The initial efficacy pilot's safe baseline was construct-inadequate. The
   correction used an unconsumed, prospectively barred pilot tail before any
   criterion seed and retained the initial result.
6. Gate 3 stopped on the preregistered control revisability miss. No tuning or
   later gate execution followed.
