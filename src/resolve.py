"""
Entity resolver -- turn free text ("PD", "tau", "LRRK2 G2019S") into a resolved
ontology entity, scalably and without hardcoded tables.

The strategy, in three moves (the "guess, then ask, then search" pattern):

  1. GUESS -- run one universal search, CONSTRAINED by the node's expected type.
     The question already tells us each node's type (source is a gene/protein,
     target is a disease), and constraining the search to that type removes most
     ambiguity for free: "tau" as a target -> MAPT; "MS" as a disease -> multiple
     sclerosis, not the gene MTR that an unconstrained search returns.

  2. DECIDE -- a confidence gate on the ranked hits:
       * one dominant hit, or an (case-insensitive) name match, or the runners-up
         are just sub-types of the top hit  -> RESOLVED (accept the guess);
       * two or more comparable, distinct candidates                 -> AMBIGUOUS
         (return them so the caller can ASK the user which they meant);
       * nothing                                                     -> NOT_FOUND
         (with a helpful suggestion -- e.g. a protein-change mutation needs an rsID).

  3. SEARCH -- the caller retrieves evidence with the confirmed id.

This never fabricates an id, works for any entity Open Targets indexes (target /
disease / drug), and only interrupts the user when the input is genuinely unclear.
Variants/mutations are handled separately (see `classify_variant`), because a
protein change like "G2019S" is not searchable as free text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import httpx

from src.connectors.opentargets import _post
from src.question import Node, NodeType

# Amino-acid one-letter -> three-letter, for building protein HGVS (G2019S ->
# p.Gly2019Ser) that Ensembl's variant recoder understands.
_AA3 = {
    "A": "Ala", "R": "Arg", "N": "Asn", "D": "Asp", "C": "Cys", "E": "Glu",
    "Q": "Gln", "G": "Gly", "H": "His", "I": "Ile", "L": "Leu", "K": "Lys",
    "M": "Met", "F": "Phe", "P": "Pro", "S": "Ser", "T": "Thr", "W": "Trp",
    "Y": "Tyr", "V": "Val", "*": "Ter",
}
_ENSEMBL_RECODER = "https://rest.ensembl.org/variant_recoder/human/{}"


def _to_protein_hgvs(gene: str, change: str) -> Optional[str]:
    """G2019S -> 'LRRK2:p.Gly2019Ser'. Returns None if not a simple missense."""
    m = re.fullmatch(r"([A-Za-z])(\d{1,5})([A-Za-z*])", change.strip())
    if not m:
        return None
    ref, pos, alt = m.group(1).upper(), m.group(2), m.group(3).upper()
    if ref not in _AA3 or alt not in _AA3:
        return None
    return f"{gene}:p.{_AA3[ref]}{pos}{_AA3[alt]}"


def _recode_to_rsid(gene: str, change: str, timeout: float = 20.0) -> Optional[str]:
    """Map a gene + protein change to an rsID via Ensembl's variant recoder."""
    hgvs = _to_protein_hgvs(gene, change)
    if not hgvs:
        return None
    try:
        r = httpx.get(_ENSEMBL_RECODER.format(hgvs),
                      headers={"content-type": "application/json"}, timeout=timeout)
        r.raise_for_status()
        for el in r.json():
            for key, val in el.items():
                if key in ("warnings", "input"):
                    continue
                for entry in (val if isinstance(val, list) else [val]):
                    for ident in (entry.get("id") or []):
                        if str(ident).startswith("rs"):
                            return str(ident)
    except Exception:
        return None
    return None

# Node type -> the Open Targets entity classes to constrain the search to.
_NODE_ENTITIES: dict[NodeType, list[str]] = {
    NodeType.GENE: ["target"],
    NodeType.PROTEIN: ["target"],
    NodeType.TRANSCRIPT: ["target"],
    NodeType.CELL_STATE: ["target"],
    NodeType.DISEASE: ["disease"],
    NodeType.PHENOTYPE: ["disease"],
    NodeType.DRUG: ["drug"],
}

_SEARCH = """
query Resolve($s: String!, $e: [String!]) {
  search(queryString: $s, entityNames: $e) {
    total
    hits { id name entity score }
  }
}
"""

# Open Targets calls genes "target"; say "gene" to users so a not-found note about
# a gene isn't mistaken for the disease side of the question.
_FRIENDLY_ENTITY = {"target": "gene", "disease": "disease", "drug": "drug"}

# A few gene display-labels that are not searchable symbols (keys are _norm()'d).
GENE_ALIASES: dict[str, str] = {
    "amyloid": "APP", "app amyloid": "APP", "abeta": "APP", "a beta": "APP",
}

# A dominant hit is at least this many times the runner-up's score.
_DOMINANCE = 1.6
# Below this search score a non-exact top hit is treated as no confident match
# (garbage input like "XYZ" tops out ~280; real synonym matches score >3800).
_RELEVANCE_FLOOR = 500.0
# rsID and protein-change (e.g. G2019S, p.Gly2019Ser) patterns.
_RS = re.compile(r"^rs\d+$", re.I)
_PROTEIN_CHANGE = re.compile(r"\b([A-Z]\d{1,5}[A-Z*]|p\.\w+)\b")

# Curated aliases for common biomedical DISEASE abbreviations. This is a small,
# reliable override layer -- not the scaling mechanism (search is) -- for the cases
# where free-text search mis-ranks an abbreviation ("MS" search tops out at myeloid
# sarcoma, not multiple sclerosis). Gene symbols are already canonical, so aliases
# here are disease-only; gene synonyms are left to search. Applied only when the
# node's expected type is a disease/phenotype.
DISEASE_ALIASES: dict[str, str] = {
    "pd": "Parkinson disease", "ad": "Alzheimer disease",
    "als": "amyotrophic lateral sclerosis", "ftd": "frontotemporal dementia",
    "hd": "Huntington disease", "ms": "multiple sclerosis",
    "cad": "coronary artery disease", "chd": "coronary artery disease",
    "cvd": "cardiovascular disease", "t2d": "type 2 diabetes mellitus",
    "t1d": "type 1 diabetes mellitus", "ibd": "inflammatory bowel disease",
    "ra": "rheumatoid arthritis", "scz": "schizophrenia",
    "mdd": "major depressive disorder", "copd": "chronic obstructive pulmonary disease",
    "ckd": "chronic kidney disease",
    # common apostrophe-less / plural name variants search handles poorly
    "parkinsons": "Parkinson disease", "parkinson": "Parkinson disease",
    "alzheimers": "Alzheimer disease", "alzheimer": "Alzheimer disease",
    "lou gehrigs": "amyotrophic lateral sclerosis", "lou gehrig": "amyotrophic lateral sclerosis",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


@dataclass
class Candidate:
    id: str
    name: str
    entity: str
    score: float

    def label(self) -> str:
        return f"{self.name} ({self.id}, {self.entity})"


@dataclass
class Resolution:
    query: str
    status: str  # "resolved" | "ambiguous" | "not_found"
    best: Optional[Candidate] = None
    candidates: list[Candidate] = field(default_factory=list)
    note: str = ""

    @property
    def resolved(self) -> bool:
        return self.status == "resolved" and self.best is not None


@dataclass
class VariantHint:
    """A parsed variant input that OT free-text search cannot resolve directly."""

    kind: str  # "rsid" | "protein_change" | "none"
    gene: Optional[str] = None
    change: Optional[str] = None
    rsid: Optional[str] = None


def classify_variant(text: str) -> VariantHint:
    """Detect an rsID or a `GENE p.Change` mutation so it can be routed, not
    fuzzy-searched. Returns kind='none' if the text is not variant-shaped."""
    t = text.strip()
    if _RS.match(t):
        return VariantHint(kind="rsid", rsid=t.lower())
    m = _PROTEIN_CHANGE.search(t)
    if m:
        # e.g. "LRRK2 G2019S" -> gene LRRK2, change G2019S
        gene = t[: m.start()].strip() or None
        return VariantHint(kind="protein_change", gene=gene, change=m.group(1))
    return VariantHint(kind="none")


class EntityResolver:
    """Resolve free text to an ontology entity via type-constrained search."""

    def __init__(self, online: bool = True, timeout: float = 20.0) -> None:
        self.online = online
        self.timeout = timeout

    def _search(self, text: str, entities: Optional[list[str]]) -> list[Candidate]:
        data = _post(_SEARCH, {"s": text, "e": entities}, self.timeout)
        if not data:
            return []
        hits = data.get("search", {}).get("hits", []) or []
        out: list[Candidate] = []
        for h in hits:
            if entities and h.get("entity") not in entities:
                continue
            out.append(
                Candidate(
                    id=h["id"], name=h["name"], entity=h["entity"],
                    score=float(h.get("score") or 0.0),
                )
            )
        return out

    def resolve_variant(self, text: str) -> Optional[dict]:
        """Resolve an rsID or `GENE ProteinChange` to an OT variant candidate (and
        the parent gene, as an alternative). Returns None if not variant-shaped."""
        v = classify_variant(text)
        rsid: Optional[str] = None
        gene: Optional[str] = None
        if v.kind == "rsid":
            rsid = v.rsid
        elif v.kind == "protein_change" and v.gene:
            gene = v.gene
            rsid = _recode_to_rsid(v.gene, v.change)
        else:
            return None
        if not rsid:
            return {"variant": None, "gene": None,
                    "note": f"Could not map '{text}' to a known rsID (try giving the rsID directly)."}
        vhits = self._search(rsid, ["variant"])
        variant_cand = None
        if vhits:
            vc = vhits[0]
            label = f"{text} ({rsid})" if gene else vc.name
            variant_cand = Candidate(id=vc.id, name=label, entity="variant", score=vc.score)
        gene_cand = None
        if gene:
            ghits = self._search(gene, ["target"])
            if ghits:
                gene_cand = ghits[0]
        return {"variant": variant_cand, "gene": gene_cand, "rsid": rsid}

    def resolve(self, text: str, expected_types: Optional[list[NodeType]] = None) -> Resolution:
        if not self.online:
            return Resolution(text, "not_found", note="Resolver offline; use the built-in table or --online.")

        types = expected_types or []
        source_scope = any(t in (NodeType.GENE, NodeType.PROTEIN, NodeType.VARIANT) for t in types)
        vinfo = classify_variant(text)
        # Variant routing: a variant-shaped input in a source position resolves to
        # the specific variant, with the parent gene offered as the alternative.
        if NodeType.VARIANT in types or (vinfo.kind != "none" and source_scope):
            vres = self.resolve_variant(text)
            variant = (vres or {}).get("variant")
            gene = (vres or {}).get("gene")
            if variant is None:
                note = (vres or {}).get("note") or f"Could not resolve variant '{text}'."
                # fall through to a normal gene search if a gene name is recoverable
                if gene is None and NodeType.VARIANT not in types:
                    pass
                else:
                    return Resolution(text, "not_found", note=note, candidates=[c for c in [gene] if c])
            else:
                cands = [c for c in (variant, gene) if c]
                return Resolution(
                    text, "ambiguous", best=variant, candidates=cands,
                    note=(f"'{text}' resolves to variant {vres['rsid']}. Appraise the specific "
                          f"variant (recommended), or the whole gene?"),
                )

        entities: list[str] = []
        disease_scope = False
        for t in expected_types or []:
            entities.extend(_NODE_ENTITIES.get(t, []))
            disease_scope = disease_scope or t in (NodeType.DISEASE, NodeType.PHENOTYPE)
        entities = list(dict.fromkeys(entities)) or None

        # Expand a known disease abbreviation before searching (MS -> multiple
        # sclerosis). Apostrophe-insensitive: "Parkinson's" and "parkinsons" both hit.
        raw = text.strip()
        query = raw
        if disease_scope:
            nraw = _norm(raw)
            query = DISEASE_ALIASES.get(nraw) or DISEASE_ALIASES.get(nraw.replace(" ", "")) or raw
        elif any(t in (NodeType.GENE, NodeType.PROTEIN) for t in types):
            query = GENE_ALIASES.get(_norm(raw), raw)
        aliased = query != raw

        hits = self._search(query, entities)
        if not hits:
            # A mutation is not free-text searchable -- say what to do instead.
            v = classify_variant(raw)
            friendly = " / ".join(_FRIENDLY_ENTITY.get(e, e) for e in entities) if entities else "entity"
            if v.kind == "protein_change":
                hint = (f"'{raw}' looks like a protein-change mutation. I can appraise the gene "
                        f"'{v.gene or raw}' instead, or give me the rsID for the specific variant.")
            elif v.kind == "rsid":
                hint = f"'{raw}' is an rsID; variant-level appraisal is a separate path from gene/disease."
            else:
                hint = f"No {friendly} matched '{raw}'. Check spelling or try the full name."
            return Resolution(raw, "not_found", note=hint)

        hits.sort(key=lambda c: c.score, reverse=True)
        top = hits[0]
        second = hits[1] if len(hits) > 1 else None
        exact = _norm(top.name) == _norm(query)
        subtype = second is not None and _norm(top.name) in _norm(second.name)

        # (a) exact name match -> confident (covers alias-expanded terms)
        if exact:
            note = (f"Read '{raw}' as '{query}'; exact match {top.label()}." if aliased
                    else f"Exact match: {top.label()}.")
            return Resolution(raw, "resolved", best=top, candidates=hits[:5], note=note)
        # relevance floor: a non-exact top hit below the floor is a weak/garbage
        # match, not a real synonym -- do not resolve it to something unrelated.
        if top.score < _RELEVANCE_FLOOR:
            return Resolution(raw, "not_found", note=(
                f"No confident match for '{raw}' (best was '{top.name}', a weak match). "
                "Check spelling or use the full name."))
        # (b) the runners-up are just sub-types of the top term -> accept the parent
        if subtype:
            return Resolution(raw, "resolved", best=top, candidates=hits[:5],
                              note=f"Resolved to the parent term {top.label()} (others are sub-types).")
        # (caution) a short, unknown, abbreviation-like input that does NOT match by
        # name is exactly where search silently guesses wrong ("MS" -> myeloid
        # sarcoma). Do not trust dominance here -- hand back candidates and ask.
        if not aliased and len(raw) <= 4 and raw.upper() == raw:
            return Resolution(raw, "ambiguous", best=top, candidates=hits[:4],
                              note=f"'{raw}' looks like an abbreviation with no confident match; asking which was meant.")
        # (c) one dominant hit -> confident guess
        if second is None or top.score >= _DOMINANCE * max(second.score, 1e-6):
            return Resolution(raw, "resolved", best=top, candidates=hits[:5],
                              note=f"Best match: {top.label()}.")
        # (d) genuinely ambiguous -> hand back candidates for a follow-up question
        return Resolution(
            raw, "ambiguous", best=top, candidates=hits[:4],
            note=f"'{raw}' is ambiguous — {len(hits)} comparable matches; asking which was meant.",
        )

    def resolve_node(self, node: Node) -> tuple[Node, Resolution]:
        """Resolve a node in place (fills id/label from the best candidate when
        resolved). Returns the (possibly updated) node and the Resolution."""
        if node.is_resolved():
            return node, Resolution(node.display(), "resolved",
                                    best=Candidate(node.id, node.label or node.display(), "given", 0.0),
                                    note="Already resolved.")
        res = self.resolve(node.display(), [node.type])
        if res.resolved:
            node = node.model_copy(update={"id": res.best.id, "label": res.best.name})
        return node, res
