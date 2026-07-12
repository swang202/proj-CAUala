"""
Export the pydantic models as JSON Schema (draft 2020-12) for external consumers.

The shipped `schema.py` is the single source of truth; this just serializes it via
`model_json_schema()`. Run `cauala export-schemas` or import `export_all`.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from src.question import Question
from src.schema import (
    Context,
    DimensionAssessment,
    EvidenceItem,
    InusVerdict,
    Posterior,
    TargetAppraisal,
)

_MODELS: dict[str, type[BaseModel]] = {
    "TargetAppraisal": TargetAppraisal,
    "EvidenceItem": EvidenceItem,
    "DimensionAssessment": DimensionAssessment,
    "Context": Context,
    "Posterior": Posterior,
    "InusVerdict": InusVerdict,
    "Question": Question,
}


def export_all(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, model in _MODELS.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        path = out_dir / f"{name}.json"
        path.write_text(json.dumps(schema, indent=2))
        written.append(path)
    return written


if __name__ == "__main__":
    for p in export_all(Path("schemas")):
        print(p)
