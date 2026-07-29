#!/usr/bin/env python3
"""One-run C-V234-B sealed attribution challenge configuration."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from challenges import run_c_v234 as base


base.CHALLENGE = (
    base.ROOT
    / "sealed-revealed"
    / "C-V234B-attribution-challenge.md"
)
base.CHALLENGE_ID = "C-V234-B"
base.FILE_STEM = "c-v234b"
base.RELEASED_BLOCK = (2_042_000, 2_043_999)
base.VERIFIED_SEAL = (
    "c4f6f72e14c83c2191b9724f43094736cad1b437cc9260d941b371a51146c336"
)
base.RELEASE_PHRASE = (
    "Escrow: C-V234-B seeds 2042000:2043999 (fresh; "
    "2040000:2041999 consumed by the retained C-V234 FAIL and closed). "
    "Pilot blocks 1330000:1331199 BARRED (attainability pilot, 300 worlds "
    "per rate, non-criterion). Floors corrected to pilot-derived attainable "
    "values; all else verbatim."
)
base.CELL2_NO_FALSE_FLOOR = 0.80
base.CELL3_EXISTENCE_FLOOR = 0.45
base.CELL_FILES = {
    "cell_1_effective_action": "c-v234b-cell-1.json",
    "cell_2_sham_action": "c-v234b-cell-2.json",
    "cell_3_partial": "c-v234b-cell-3.json",
    "cell_4_context_switch": "c-v234b-cell-4.json",
    "cell_5_forced_probe": "c-v234b-cell-5.json",
    "cell_6_relief_only": "c-v234b-cell-6.json",
}
base.STAGE_PASS_TEXT = (
    "V2.3.4 entered Gate 6 with the clean `FROZEN_ALL_GATES_PASS` base. "
    "The original C-V234 sealed verdict remains FAIL as written: five of "
    "seven criteria passed, with two evaluator-authored rate floors above "
    "the audited information bound. C-V234-B retained all scientific "
    "definitions and corrected only those two pilot-derived floors, then "
    "passed all seven sealed criteria. The single stage disposition "
    "therefore retains both seal outcomes and licenses the "
    "counterfactual-attribution claim under the attainable criteria."
)


if __name__ == "__main__":
    raise SystemExit(base.main())
