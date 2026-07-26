"""Load stage-local frozen parameter blocks."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=3)
def load_parameters(stage: str) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "protocols" / f"{stage.lower()}-parameters.json"
    return json.loads(path.read_text(encoding="utf-8"))

