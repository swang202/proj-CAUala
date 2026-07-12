"""
The connector contract. Every database connector implements the same interface
and maps its native payload into schema.EvidenceItem.

Hard rules the base layer enforces so no connector can violate them:
  * every emitted EvidenceItem carries a DOI/PMID source (schema validates it);
  * the connector sets direction, provenance_group, assumptions_required, and
    leaves the TIER for the scorer (assemble_dimension) to assign;
  * results are cached and connectors degrade gracefully -- a network failure
    yields [] with a logged note, never a crash mid-appraisal.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from src.question import Question
from src.schema import EvidenceItem


@runtime_checkable
class BaseConnector(Protocol):
    """Structural contract. `modality` is what the registry references; the
    connector fetches evidence for a Question and returns schema EvidenceItems."""

    connector_id: str
    modality: str

    def available_for(self, q: Question) -> bool: ...

    async def fetch(self, q: Question) -> list[EvidenceItem]: ...


class ConnectorError(Exception):
    """Raised for a hard connector failure the orchestrator should surface as a
    named gap, not swallow silently."""


class _MemoryCache:
    """A trivial in-process cache. The real system swaps in duckdb + parquet; the
    interface (get/set on a string key) is what the connectors depend on."""

    def __init__(self) -> None:
        self._store: dict[str, list[EvidenceItem]] = {}

    def key(self, connector_id: str, q: Question) -> str:
        return f"{connector_id}:{q.source.display()}:{q.target.display()}:{q.edge_type.value}"

    def get(self, key: str) -> list[EvidenceItem] | None:
        return self._store.get(key)

    def set(self, key: str, value: list[EvidenceItem]) -> None:
        self._store[key] = value


CACHE = _MemoryCache()
