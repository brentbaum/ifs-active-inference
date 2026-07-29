# V2.6a development failures

## Gate-1 preflight audit-authoring failure

The first preflight reported proof 14, `readout_purity`, as `FAIL`. The
assertion searched the scoring source for `q_root =`, incorrectly treating
the necessary posterior update itself as authored readout feedback. All
other 15 proofs passed. This was an audit predicate defect: the contract
forbids `co_regulated`, arousal, and transfer readouts from feeding inference.
The formal predicate now searches the inference segment for those readout
names and verifies any readout computation occurs strictly after the final
root-posterior assignment. A second preflight showed that merely requiring
the names to be absent was also overbroad because pure readouts necessarily
must be computed for return. No scientific model, parameter, likelihood,
prior, threshold, or seed changed in either audit correction.

## Preflight seed hygiene

The first gate-1/test preflight used seeds `1202000:1202002`, which belong to
the prospective gate-3 block. No gate-3 criterion was evaluated and no traces
were retained, but deterministic RNG consumption is disclosed rather than
treated as reversible. Formal gate-1 fixtures were moved to the unassigned
public development range `1199900:1199902`. Any future continuation to gate 3
requires evaluator adjudication of the three consumed seeds or a replacement
block.
