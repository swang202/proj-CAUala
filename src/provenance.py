"""
Provenance & validation registry.

Every evidence figure in a report is tagged with (a) the data source it came from,
cited, and (b) a validation status saying whether the number has been verified
in-source. Online mode is the default, so most figures arrive `[RETRIEVED]` from a
live database this session -- metadata seen, not yet verified against the primary
record -- and the report must say so loudly rather than presenting them as checked
facts. Curated offline figures carry `TODO:cite` placeholder citations and are
`[UNVERIFIED]` until replaced from a paper actually read.

This module maps an EvidenceItem to its DataSource + validation status; the report
layer renders the citation and the "validate before use" banner from it.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.schema import EvidenceItem


@dataclass(frozen=True)
class DataSource:
    id: str
    name: str
    citation: str          # human-readable academic citation
    doi: str               # DOI/accession for the database of record
    url: str
    access_class: str      # A open / B controlled / C paper-attached (Data-Source Catalog)
    retrieval: str         # how the figure was obtained
    validation: str        # what still has to be done before trusting the number
    provenance_tag: str    # [VERIFIED] / [RETRIEVED] / [TRAINING - verify] / [UNVERIFIED]


# Live, keyless databases wired today.
_OPEN_TARGETS = DataSource(
    id="opentargets",
    name="Open Targets Platform",
    citation="Ochoa et al., Nucleic Acids Research 51:D1353 (2023)",
    doi="10.1093/nar/gkac1046",
    url="https://platform.opentargets.org",
    access_class="A (open, keyless)",
    retrieval="live GraphQL query this session",
    validation="RETRIEVED live — integrated score, not a primary measurement; verify the "
    "underlying datatype evidence in-source before use.",
    provenance_tag="[RETRIEVED]",
)
_GNOMAD = DataSource(
    id="gnomad",
    name="gnomAD",
    citation="Karczewski et al., Nature 581:434 (2020)",
    doi="10.1038/s41586-020-2308-7",
    url="https://gnomad.broadinstitute.org",
    access_class="A (open, keyless)",
    retrieval="live GraphQL query this session",
    validation="RETRIEVED live — constraint metric; confirm gene build/version and "
    "current gnomAD release before use.",
    provenance_tag="[RETRIEVED]",
)
# Offline hand-curated fixtures (placeholder citations).
_CURATED = DataSource(
    id="curated",
    name="Hand-curated literature fixture",
    citation="see per-item DOI/PMID (TODO:cite placeholders)",
    doi="",
    url="",
    access_class="C (paper-attached)",
    retrieval="curated offline record",
    validation="UNVERIFIED — placeholder citation (TODO:cite); replace from the primary "
    "paper before any real use.",
    provenance_tag="[UNVERIFIED]",
)

DATA_SOURCES: dict[str, DataSource] = {s.id: s for s in (_OPEN_TARGETS, _GNOMAD, _CURATED)}

# Prefixes that identify a live-retrieved item by its provenance_group.
_LIVE_PREFIXES = {"opentargets": "opentargets", "gnomad": "gnomad"}


def source_of(item: EvidenceItem) -> DataSource:
    """Which DataSource an item came from, inferred from its provenance group."""
    pg = item.provenance_group.lower()
    for src_id, prefix in _LIVE_PREFIXES.items():
        if pg.startswith(prefix):
            return DATA_SOURCES[src_id]
    return DATA_SOURCES["curated"]


def is_live(item: EvidenceItem) -> bool:
    return source_of(item).id in _LIVE_PREFIXES


def accession(item: EvidenceItem) -> str:
    """The queryable accession/key for the retrieved figure (the provenance group
    encodes the resolved ids for live items)."""
    return item.provenance_group


def cite(item: EvidenceItem) -> str:
    """A one-line datasource citation for an item, e.g. for a reference list."""
    src = source_of(item)
    if src.id == "curated":
        return f"{item.source} (primary; {src.name}, {src.access_class}) [{src.validation.split(' — ')[0]}]"
    return (
        f"retrieved from {src.name} ({src.citation}; doi:{src.doi}), "
        f"accession {accession(item)}, {src.access_class}"
    )


def validation_banner(items: list[EvidenceItem]) -> str:
    """A prominent 'these need validating' summary for the top of a report."""
    live = [i for i in items if is_live(i)]
    curated = [i for i in items if not is_live(i)]
    parts: list[str] = []
    if live:
        srcs = sorted({source_of(i).name for i in live})
        parts.append(
            f"{len(live)} figure(s) RETRIEVED live this session from {', '.join(srcs)} "
            "— tagged [RETRIEVED]; verify each in-source before use."
        )
    if curated:
        parts.append(
            f"{len(curated)} figure(s) from curated fixtures carry placeholder citations "
            "(TODO:cite) — tagged [UNVERIFIED]; replace from the primary paper before use."
        )
    if not parts:
        return "No quantitative figures on record."
    return " ".join(parts)
