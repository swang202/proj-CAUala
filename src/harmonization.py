"""
Harmonization layer -- ID mapping + coarse-label detection.

Cross-DB joins fail without ID mapping, and a failed join looks exactly like "no
evidence." This layer normalizes user terms to ontology ids (genes -> Ensembl,
disease -> MONDO/EFO, variants -> rsID) and flags disease terms that map to many
subtypes so the appraisal can advise stratification (the memo's
"collection of diseases" point).

Offline it uses a small built-in table covering the demo entities; `online=True`
would fan out to mygene.info / OLS. Resolution never fabricates an id -- an
unresolved node stays unresolved and is reported as such.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.question import Node, NodeType, Question

# Minimal offline resolver table for the demo entities. Real deployment swaps in
# mygene.info (genes), OLS/text2term (disease), dbSNP/SPDI (variants).
_GENE_IDS: dict[str, tuple[str, str]] = {
    "pcsk9": ("ENSG00000169174", "PCSK9"),
    "app": ("ENSG00000142192", "APP"),
    "app/amyloid": ("ENSG00000142192", "APP"),
    "amyloid": ("ENSG00000142192", "APP"),
    "mapt": ("ENSG00000186868", "MAPT"),
    "tau": ("ENSG00000186868", "MAPT"),
    "crp": ("ENSG00000132693", "CRP"),
    "cetp": ("ENSG00000087237", "CETP"),
    "hdl-c": ("EFO_0004612", "HDL cholesterol"),   # a measurement, not a gene
    "hdl": ("EFO_0004612", "HDL cholesterol"),
}

_DISEASE_IDS: dict[str, tuple[str, str]] = {
    "coronary artery disease": ("EFO_0001645", "coronary artery disease"),
    "cad": ("EFO_0001645", "coronary artery disease"),
    "chd": ("EFO_0001645", "coronary artery disease"),
    "cardiovascular disease": ("EFO_0000319", "cardiovascular disease"),
    "alzheimer's disease": ("MONDO_0004975", "Alzheimer disease"),
    "alzheimer disease": ("MONDO_0004975", "Alzheimer disease"),
    "ad": ("MONDO_0004975", "Alzheimer disease"),
    "parkinson disease": ("MONDO_0005180", "Parkinson disease"),
    "parkinson's disease": ("MONDO_0005180", "Parkinson disease"),
    "parkinsons": ("MONDO_0005180", "Parkinson disease"),
    "pd": ("MONDO_0005180", "Parkinson disease"),
}

# Common disease abbreviations expanded to their full term BEFORE resolution, so
# "PD" is understood as Parkinson's disease rather than left to a fuzzy search that
# could match the wrong entity. Expansion is recorded as a harmonization note.
_DISEASE_ABBREV: dict[str, str] = {
    "pd": "Parkinson disease",
    "ad": "Alzheimer disease",
    "als": "amyotrophic lateral sclerosis",
    "ftd": "frontotemporal dementia",
    "hd": "Huntington disease",
    "ms": "multiple sclerosis",
    "cad": "coronary artery disease",
    "chd": "coronary artery disease",
    "cvd": "cardiovascular disease",
    "t2d": "type 2 diabetes mellitus",
    "ibd": "inflammatory bowel disease",
    "ra": "rheumatoid arthritis",
    "scz": "schizophrenia",
}

# Disease terms known to span many mechanistically distinct subtypes. A hit sets
# coarse_label_warning and the appraisal offers to stratify.
_COARSE_LABELS: dict[str, list[str]] = {
    "cardiovascular disease": ["coronary artery disease", "stroke", "heart failure", "atrial fibrillation"],
    "cancer": ["breast", "lung", "colorectal", "prostate", "..."],
    "dementia": ["Alzheimer disease", "frontotemporal dementia", "Lewy body", "vascular"],
    "diabetes": ["type 1", "type 2", "MODY", "gestational"],
}


@dataclass
class Harmonization:
    """The result of resolving a Question: the resolved question plus any warnings."""

    question: Question
    coarse_label_warning: bool
    unresolved: list[str]
    notes: list[str]


def _resolve_node(node: Node) -> Node:
    key = node.display().strip().lower()
    if node.type in (
        NodeType.GENE,
        NodeType.PROTEIN,
        NodeType.TRANSCRIPT,
        NodeType.VARIANT,
        NodeType.CELL_STATE,
    ):
        hit = _GENE_IDS.get(key)
    elif node.type in (NodeType.DISEASE, NodeType.PHENOTYPE):
        hit = _DISEASE_IDS.get(key)
    else:
        hit = None
    if hit is None:
        return node
    ident, label = hit
    return node.model_copy(update={"id": node.id or ident, "label": node.label or label})


def is_coarse_label(disease_term: str) -> tuple[bool, list[str]]:
    """True + the subtype list if the disease term spans many subtypes."""
    subtypes = _COARSE_LABELS.get(disease_term.strip().lower())
    return (subtypes is not None, subtypes or [])


def _expand_abbreviation(node: Node) -> tuple[Node, Optional[str]]:
    """Expand a known disease abbreviation (PD -> Parkinson disease) on a disease/
    phenotype node so the term is understood, not fuzzy-matched. Returns the node
    (possibly updated) and a note describing the expansion."""
    if node.type not in (NodeType.DISEASE, NodeType.PHENOTYPE):
        return node, None
    key = node.display().strip().lower()
    full = _DISEASE_ABBREV.get(key)
    if full is None or full.lower() == key:
        return node, None
    return node.model_copy(update={"symbol": full}), f"Read '{node.display()}' as '{full}'."


def harmonize(q: Question) -> Harmonization:
    """Resolve both endpoints and flag a coarse disease label. Never fabricates ids."""
    notes: list[str] = []
    src_node, src_note = _expand_abbreviation(q.source)
    tgt_node, tgt_note = _expand_abbreviation(q.target)
    notes.extend(n for n in (src_note, tgt_note) if n)

    source = _resolve_node(src_node)
    target = _resolve_node(tgt_node)
    resolved = q.model_copy(update={"source": source, "target": target})

    unresolved = [n.display() for n in (source, target) if not n.is_resolved()]
    coarse, subtypes = is_coarse_label(target.display())
    if coarse:
        notes.append(
            f"'{q.target.display()}' maps to many subtypes ({', '.join(subtypes)}); "
            "verdict advised to be stratified."
        )
    if unresolved:
        notes.append(f"Unresolved ids: {', '.join(unresolved)} -- joins may return no evidence.")

    return Harmonization(
        question=resolved,
        coarse_label_warning=coarse,
        unresolved=unresolved,
        notes=notes,
    )
