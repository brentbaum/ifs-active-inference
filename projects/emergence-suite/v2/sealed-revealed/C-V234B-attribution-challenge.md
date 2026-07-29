# Sealed challenge C-V234-B — counterfactual action attribution challenge (attainability-corrected sealing)

**Second sealing. The C-V234 FAIL is retained as written: five of seven criteria passed; the two failures were evaluator rate floors authored above the information bound of the exact posterior at the frozen 32-slice budget (audit item 4 skipped). A public development-seed pilot (blocks 1330000:1331199, barred hereafter, 300 worlds per rate, non-criterion) measured the Bayes-optimal attainable rates: sham no-false-attribution 0.8833; partial existence-recovery 0.5467. This sealing sets those two floors ~4 standard errors below the piloted attainable point — still excluding superstitious or blind behavior — and changes NOTHING else: identical cells, generators, kwargs, and all other criteria verbatim from C-V234. Fresh escrow 2042000:2043999; the consumed 2040000:2041999 block is closed.**

## Cells (parse instruction binding)

{'parse_instruction': 'Cells declare generate_controlled_world or generate_world kwargs; scoring names frozen attribution readouts (danger posterior, efficacy-existence posterior, efficacy magnitude, prevented-outcome posterior, relief accounting); ast.literal_eval on the exact bracketed text only.', 'cell_1_effective_action': {'escrow': '2042000:2042332', 'n_worlds': 333, 'generator': 'generate_controlled_world', 'kwargs': {'scenario': 'full', 'length': 32}}, 'cell_2_sham_action': {'escrow': '2042333:2042665', 'n_worlds': 333, 'generator': 'generate_controlled_world', 'kwargs': {'scenario': 'irrelevant', 'length': 32}}, 'cell_3_partial': {'escrow': '2042666:2042998', 'n_worlds': 333, 'generator': 'generate_controlled_world', 'kwargs': {'scenario': 'partial', 'length': 32}}, 'cell_4_context_switch': {'escrow': '2042999:2043331', 'n_worlds': 333, 'generator': 'generate_controlled_world', 'kwargs': {'scenario': 'context_switch', 'length': 48}}, 'cell_5_forced_probe': {'escrow': '2043332:2043664', 'n_worlds': 333, 'generator': 'generate_world', 'kwargs': {'identifiable': True, 'length': 32, 'theta_index': 3, 'eta_indices': (4, 4), 'probe_frequency': 0.25}}, 'cell_6_relief_only': {'escrow': '2043665:2043999', 'n_worlds': 335, 'generator': 'generate_controlled_world', 'kwargs': {'scenario': 'relief_sham', 'length': 32}}}

## Criteria
Identical to C-V234 in every clause except the two pilot-corrected floors:
1. Cell 1: unchanged (efficacy-existence unique >= .75; danger separation lower bound > 0; recombination 1e-10).
2. Cell 2: no-false-attribution rate >= .80 (pilot-derived; was .90); action-free danger identity within 1e-10 unchanged.
3. Cell 3: existence recovery >= .45 (pilot-derived; was .60); the full>partial>sham magnitude orderings with non-overlapping CIs unchanged.
4. Cell 4: unchanged. 5. Cell 5: unchanged. 6. Cell 6: unchanged (exact zeros). 7. Semantic + custody: unchanged.

Pass = all seven. Failure interpretations as in C-V234.
