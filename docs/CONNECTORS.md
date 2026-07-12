# Connecting CAUala to real databases

> 🧭 **Build — connect/add databases.** How live data sources work and how to add a new connector (~40 lines). Related: [../build-brief.md](../build-brief.md) (spec), [Causal_Data_Source_Catalog.md](Causal_Data_Source_Catalog.md) (the source catalog). Docs map: **[docs index](README.md)**.

CAUala runs **online by default**: `appraise` queries live databases and every
figure is cited to its source and tagged for validation. Two real, keyless sources
are wired and working (Open Targets, gnomAD); the rest of the §3 catalog has a
uniform contract and registry entry and can be added with the recipe below. Pass
`--offline` to fall back to curated, recorded-fixture evidence
(`registry/curated_evidence.yaml`), which the `demo` and `validate` commands and
the test suite use for reproducibility.

## Run it

```bash
# easy path — two words, online by default
.venv/bin/python -m src.cli appraise PCSK9 "coronary artery disease"

# a target NOT curated: resolved from scratch via Open Targets search, live-scored
.venv/bin/python -m src.cli appraise SORT1 "coronary artery disease"

# reproducible, no network
.venv/bin/python -m src.cli appraise PCSK9 "coronary artery disease" --offline
```

## Validation & citation

Because online is the default, most figures arrive **`[RETRIEVED]`** from a live
database this session — metadata seen, not verified against the primary record.
The report says so loudly: a "⚠️ Validation required" banner at the top, an inline
datasource citation under every figure (database name + academic citation + DOI +
accession), a "Sources queried" list with access class in §9, and a references
section (§12) that cites both the primary source and the database, each with its
validation status. Curated placeholder figures are tagged **`[UNVERIFIED]`**. The
registry lives in `src/provenance.py` — add a `DataSource` there when you add a
connector.

Opt-in live smoke tests (kept out of the default suite):

```bash
CAUALA_LIVE=1 .venv/bin/python -m pytest tests/test_live.py -v
```

## What happens in `--online` mode

1. **Harmonize** the question — resolve gene/disease to ontology ids. The offline
   table is tried first; on a miss, `OpenTargetsConnector.resolve()` uses the OT
   `search` endpoint (`src/orchestrator.py::_resolve_online`). Ids are never
   fabricated — an unresolved node stays unresolved and is reported as a gap.
2. **Query** every available connector for the question type
   (`Orchestrator._retrieve`). `available_for(q)` gates each one on `--online`,
   node type, and id resolution.
3. **Map** each native payload into a `schema.EvidenceItem` (DOI/PMID source,
   direction, provenance group). The scorer — never the connector — assigns tiers.
4. **Score** deterministically and assemble the appraisal. A live network failure
   degrades to `[]` (a named gap in the report), never a crash.

> The design invariant survives live data: Open Targets' integrated score is
> **direction-less**, so even a high `genetic_association` (SORT1 scored 0.97)
> cannot lift the tier by itself — it lands in `association`, and the gate still
> demands *directional* causal evidence (MR, perturbation, RCT) to go causal.

## Auth reality (from the build brief §3)

| Source | Status here | Auth | How to enable |
|---|---|---|---|
| **Open Targets** | ✅ wired, working | none | `--online` |
| **gnomAD** | ✅ wired, working | none | `--online` |
| GWAS Catalog | contract + registry entry | none | implement `fetch` (REST v2) |
| eQTL Catalogue | contract + registry entry | none | implement `fetch` (REST / tabix) |
| ClinVar | contract + registry entry | optional NCBI key | `NCBI_API_KEY` |
| Europe PMC | contract + registry entry | none | implement `fetch` |
| **OpenGWAS / MR-Base** | contract + registry entry | **JWT bearer (since 05/2024)** | `OPENGWAS_JWT` |
| OMIM / ClinGen | contract + registry entry | OMIM key (ClinGen none) | `OMIM_API_KEY` |
| LINCS L1000 (CLUE.io) | contract + registry entry | CLUE key (SigCom none) | `CLUE_API_KEY` |
| DepMap / scPerturb | bulk ingest (no query API) | none | download + cache locally |

Keyed connectors read their secret from an environment variable at construction —
none is required for the two that ship working. Suggested variable names above;
set them in your shell (or a `.env` you do not commit) before `--online`.

## Adding a connector (the recipe)

Every connector is ~40 lines. Follow `src/connectors/opentargets.py` or
`src/connectors/gnomad.py`:

```python
# src/connectors/gwas_catalog.py
from src.question import NodeType, Question
from src.schema import Dimension, Direction, EffectSize, EvidenceItem, EvidenceType, Readout, System

class GwasCatalogConnector:
    connector_id = "gwas_catalog"
    modality = "gwas_finemap"

    def __init__(self, online: bool = False):
        self.online = online

    def available_for(self, q: Question) -> bool:
        return self.online and q.source.type == NodeType.GENE \
            and q.target.type == NodeType.DISEASE

    async def fetch(self, q: Question) -> list[EvidenceItem]:
        if not self.available_for(q):
            return []
        # 1. hit the REST endpoint (httpx, with try/except -> [] on failure)
        # 2. map each association to an EvidenceItem:
        #      - dimension = Dimension.GENETIC
        #      - direction from the risk allele / effect sign (NOT null if directional)
        #      - effect = EffectSize(value=beta_or_or, ci_low=..., ci_high=..., units=...)
        #      - source = the study's PMID/DOI   (schema REJECTS anything else)
        #      - provenance_group = one id per underlying observation (dedup key)
        #      - leave the TIER unset — the scorer assigns it
        return []
```

Then register it in two places:

1. `src/orchestrator.py` — construct it in `Orchestrator.__init__` and add it to
   the loop in `_retrieve` (`for connector in (self.opentargets, self.gnomad, ...)`).
2. `registry/evidence_stacks.yaml` — reference its `connector:` id in the relevant
   stack entries so the question-type routing and the not-examined/VOI reporting
   know it exists.

### The three hard rules a connector must honour

- **Provenance or it doesn't count.** `EvidenceItem.source` must be a DOI (`10.…`)
  or `PMID:…`; the schema validator rejects anything else. Uncited evidence stays
  out of the ledger.
- **Direction comes from the design, not convenience.** Cross-sectional /
  co-expression payloads must be emitted `Direction.NULL` (direction-less) — the
  scorer's directionality gate then keeps them out of the causal tiers.
- **Don't set the tier.** Emit the record; `scoring_engine.assemble_dimension`
  assigns the tier from design quality, replication, and context match.

## Caching & scale

`src/connectors/base.py` ships a trivial in-process cache (`CACHE`). For bulk /
production scale, swap it for the `duckdb` + local Parquet store named in the
brief — the interface the connectors depend on is just `get(key)` / `set(key,
value)`. Bulk sources (DepMap, scPerturb, LINCS GEO) are ingest-and-cache rather
than live-query: download once, register a connector that reads the local store.
```
