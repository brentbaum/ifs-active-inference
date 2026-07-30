# V3.4 development failures ledger

## Stage-0 recovery-generator defect

The first pilot produced root accuracy `0.475` and root ECE
`0.30359522775662495`. The generator passed `p(O_G=G)` to a Bernoulli sampler
that required `p(O_G=1)`. The original pilot, stop, and diagnosis are retained.

The authorized repair changed only root-observation generation. On the fresh
pilot, root accuracy was `0.79125` and root ECE `0.019092896412940177`, versus
structure ECE `0.02745597246490784`.

## Original Gate-5 verdict

The original Gate-5 record remains `FAIL`: 32-slice exact-program accuracy was
`0.733` against the 48-slice-frozen floor `0.78`.

The evaluator classified that comparison as an unaudited information-budget
transplant. Under the standing convention the 48-slice primary cell is
blocking and passed at `0.837`; the 32-slice result remains published as the
short-history conjunction bound. No result was changed and no world was
rerun.
