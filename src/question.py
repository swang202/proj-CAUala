"""
The parsed causal question -- the one core object not in the shipped schema.

The agent layer produces a Question from free text; a human can confirm or edit
it before retrieval. The atomic claim the whole tool answers is `source -> target
| context`, never a context-free "A causes B". The `context` field reuses the
shipped `schema.Context` verbatim (invariant: it maps 1:1, may be partially null).

Node and edge vocab is fixed here so the evidence-stack registry can match on it.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from src.schema import Context


class NodeType(str, Enum):
    """What kind of thing a source/target node is. The retrieval stack differs
    per (source_type, target_type, edge_type)."""

    VARIANT = "variant"
    GENE = "gene"
    TRANSCRIPT = "transcript"
    PROTEIN = "protein"
    PATHWAY = "pathway"
    CELL_STATE = "cell_state"
    PHENOTYPE = "phenotype"
    DISEASE = "disease"
    DRUG = "drug"


class EdgeType(str, Enum):
    """The arrow being asked about. Each routes to a different evidence stack."""

    REGULATORY = "regulatory"          # A changes B's expression/activity
    PHYSICAL = "physical"              # A binds/contacts B
    GENETIC_RISK = "genetic_risk"      # variant raises/lowers disease risk
    CAUSAL_RISK = "causal_risk"        # gene/exposure -> disease risk
    CAUSAL_EFFECT = "causal_effect"    # do(A) changes B


class Direction(str, Enum):
    """Which way the hypothesized arrow points."""

    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"      # the reverse-causation hypothesis
    BIDIRECTIONAL = "bidirectional"
    UNKNOWN = "unknown"


class Node(BaseModel):
    """A typed, ideally-resolved endpoint of the causal arrow."""

    type: NodeType
    id: Optional[str] = Field(
        default=None,
        description="Resolved ontology id (Ensembl, MONDO, rsID, ChEBI, ...). "
        "None until harmonization runs.",
    )
    symbol: Optional[str] = Field(
        default=None, description="Human-facing symbol/label as entered (e.g. 'APP')."
    )
    label: Optional[str] = Field(
        default=None, description="Canonical name once resolved (e.g. 'Alzheimer disease')."
    )

    def display(self) -> str:
        return self.symbol or self.label or self.id or f"<{self.type.value}>"

    def is_resolved(self) -> bool:
        return self.id is not None


class Question(BaseModel):
    """A parsed causal question, ready to route to an evidence stack.

    The agent fills this from free text; harmonization resolves the node ids; the
    orchestrator matches (source.type, target.type, edge_type) against the
    evidence-stack registry to decide which modalities to query.
    """

    source: Node
    target: Node
    edge_type: EdgeType
    hypothesized_direction: Direction = Direction.SOURCE_TO_TARGET
    context: Context = Field(default_factory=Context)

    raw_text: Optional[str] = Field(
        default=None, description="The free-text question the agent parsed this from."
    )

    def stack_key(self) -> tuple[str, str, str]:
        """The (source_type, target_type, edge) triple the registry matches on."""
        return (self.source.type.value, self.target.type.value, self.edge_type.value)

    def describe(self) -> str:
        arrow = {
            Direction.SOURCE_TO_TARGET: "->",
            Direction.TARGET_TO_SOURCE: "<-",
            Direction.BIDIRECTIONAL: "<->",
            Direction.UNKNOWN: "-?-",
        }[self.hypothesized_direction]
        return (
            f"{self.source.display()} {arrow} {self.target.display()} "
            f"[{self.edge_type.value}] | {self.context.describe()}"
        )

    def fully_resolved(self) -> bool:
        """True once both endpoints carry ontology ids (harmonization done)."""
        return self.source.is_resolved() and self.target.is_resolved()
