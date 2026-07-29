# V2.3.4 decisions

1. Danger uses a five-point exact support and action efficacy uses an exact
   zero plus four causal slab points. The irrelevant model is the joint
   `(eta_0, eta_1) = (0, 0)` spike; no epsilon surrogate is used.
2. Actions enter only as interventions. There is no action-selection
   likelihood in generation, scoring, recovery, or any lesion.
3. The prevented-outcome indicator `K` is a pure posterior readout over
   `(D, A, P, Y)`. It is neither mutable state nor an input to inference.
4. Relief updates only the candidate-common policy Beta posterior. It has
   exactly zero likelihood contribution to danger or efficacy.
5. Context-specific efficacy is represented by the two declared efficacy
   coordinates. No context-switch heuristic or authored transfer coefficient
   was introduced.
6. The independently authored oracle copies every prior input before
   enumeration. Declared `1e-10` tolerance comparators are used throughout.
7. Gate-2 generation samples directly from the same normalized process scored
   by the engine. Calibration is per-slice over the registered posterior
   quantities.
8. Before Gate 5, prior-relative update magnitude was rejected as a precision
   diagnostic because saturated evidence can make both precisions reach the
   same endpoint. Masking and precision sweeps were preregistered instead as
   excess absolute error relative to the generating danger truth. The assigned
   Gate-5 block remained unopened until the replacement public-dummy screen
   passed.
9. The managed sandbox denied `ProcessPoolExecutor`'s semaphore-limit query
   before any assigned Gate-5 world ran. The runner fell back to ordered
   threads; seed-to-world mapping and scientific computations were unchanged.
10. Escrow `2040000:2041999` is evaluator-owned and was not accessed.
