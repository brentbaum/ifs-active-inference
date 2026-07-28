"""Run the excluded V2.4.2 matching-feasibility calibration."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from ref.v24 import matching_feasibility_calibration


ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / "V2.4.2"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    result = matching_feasibility_calibration()
    rows = result.pop("rows")
    expected = 0.13
    if result["derived_tolerance"] != expected:
        raise AssertionError("derived tolerance differs from frozen value")
    RESULT.mkdir(parents=True, exist_ok=True)
    csv_path = RESULT / "matching-calibration-per_world.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "complexity_per_observation": json.dumps(
                        row["complexity_per_observation"]
                    ),
                }
            )
    audited = [
        ROOT / "protocols" / "v2.4-analysis-plan.md",
        ROOT / "protocols" / "v2.4-parameters.json",
        ROOT / "ref" / "v24.py",
        csv_path,
    ]
    result.update(
        {
            "status": "frozen_before_v2.4.2_criterion_runs",
            "provenance": "pilot-amended_excluded_calibration",
            "criterion_use": False,
            "hashes": {
                str(path.relative_to(ROOT)): sha256(path)
                for path in audited
            },
        }
    )
    (RESULT / "matching-calibration.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("V2.4.2 matching tolerance frozen at 0.13")


if __name__ == "__main__":
    main()
