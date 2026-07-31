"""Suite V3 exact structural-grammar reference package."""

from .grammar import (
    BLOCKS,
    DYNAMICS,
    EDGES,
    SCOPES,
    GrammarBounds,
    GrammarStructure,
    GrammarWorld,
    StructurePosterior,
    generate_world,
    score_world,
)

__all__ = [
    "BLOCKS",
    "DYNAMICS",
    "EDGES",
    "SCOPES",
    "GrammarBounds",
    "GrammarStructure",
    "GrammarWorld",
    "StructurePosterior",
    "generate_world",
    "score_world",
    "v36",
    "v36_oracle",
]
from . import v36, v36_oracle
