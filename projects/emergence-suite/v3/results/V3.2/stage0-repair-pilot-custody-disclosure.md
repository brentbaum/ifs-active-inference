# V3.2 repair-pilot custody disclosure

Status: **PROGRESSION STOPPED BEFORE GATE 1**.

The adjudicated repair succeeded scientifically. The formal repair pilot
consumed `3230000:3231999`, serialized all 2,000 traces during execution, and
sealed their per-record and file hashes before aggregation. Its paired
witnessing gain was `0.800036943234541`, making the prospectively computed
`0.400` SESOI attainable.

Before that formal execution, however, a manual preflight called the paired
attainability helper on seeds `3230000:3230019` and printed aggregate results.
That call did not serialize traces at execution time. Although these were pilot
seeds, not criterion seeds, and the threshold formula was already declared,
this violates the standing rule that every runner serialize traces at execution
time. The later deterministic reconstruction and formal trace seal cannot make
the earlier call prospective.

After the stop decision, a semantic spot check also regenerated seed `3230000`
without trace serialization to print the already-established neutrality errors
(`0.0`, `0.0`) and dormant prior mean (`0.5`). It did not evaluate a threshold
or alter the stop, but is included here because negative custody facts are not
silently omitted.

Negative custody facts must aggregate negatively. Therefore:

- the scientific repair result and fully traced pilot remain published;
- all 2,000 repair-pilot seeds remain barred;
- frozen numeric floors remain recorded but are not used;
- Gate 1 through Gate 5 remain unopened;
- escrow `4020000:4023999` remains untouched.

External adjudication is required before stage progression.
