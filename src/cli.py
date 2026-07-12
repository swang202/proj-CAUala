"""
CAUala command-line interface.

    cauala appraise --source PCSK9 --source-type gene \
        --target "coronary artery disease" --edge causal_risk [--format md|json|html]
    cauala demo                 # run all curated known-answer cases
    cauala list-cases           # list the offline curated evidence store
    cauala export-schemas       # write JSON Schemas to ./schemas

The CLI is the deterministic core WITHOUT the agent layer: the caller supplies a
already-typed question. (The agent layer would parse free text into the same
Question object; it never computes a score.)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.export_schemas import export_all
from src.question import Context, EdgeType, Node, NodeType, Question
from src.orchestrator import Orchestrator
from src.report import to_html, to_json, to_markdown


def _build_question(args: argparse.Namespace) -> Question:
    source = args.source or args.source_pos
    target = args.target or args.target_pos
    if not source or not target:
        raise SystemExit(
            "error: need a source and a target.\n"
            "  e.g.  cauala appraise PCSK9 'coronary artery disease'"
        )
    context = Context(
        cell_type=args.cell_type,
        tissue=args.tissue,
        ancestry=args.ancestry,
        sex=args.sex,
        disease_subtype=args.disease_subtype,
        stage=args.stage,
    )
    return Question(
        source=Node(type=NodeType(args.source_type), symbol=source),
        target=Node(type=NodeType(args.target_type), symbol=target),
        edge_type=EdgeType(args.edge),
        context=context,
        raw_text=args.raw,
    )


def _emit(appraisal, fmt: str, q: Question) -> str:
    if fmt == "json":
        return to_json(appraisal)
    if fmt == "html":
        return to_html(appraisal, q)
    return to_markdown(appraisal, q)


def cmd_appraise(args: argparse.Namespace) -> int:
    online = not args.offline  # online is the DEFAULT; --offline opts out
    q = _build_question(args)
    orch = Orchestrator(online=online)
    appraisal = orch.appraise_sync(q)
    out = _emit(appraisal, args.format, q)
    mode = "online (live databases)" if online else "offline (curated fixtures)"
    if args.out:
        Path(args.out).write_text(out)
        print(f"[{mode}] wrote {args.format} report to {args.out}", file=sys.stderr)
        print(appraisal.verdict_line(), file=sys.stderr)
    else:
        print(out)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    orch = Orchestrator(online=False)
    print("proj-CAUala — known-answer demonstration (offline, curated evidence)\n")
    print(f"{'target':16s} {'tier (headline)':18s} {'position':22s} {'INUS box'}")
    print("-" * 78)
    for case in orch.fixtures.all_cases():
        q = Question(
            source=Node(type=NodeType.GENE, symbol=case.target),
            target=Node(type=NodeType.DISEASE, symbol=case.disease),
            edge_type=EdgeType.CAUSAL_RISK,
        )
        ap = orch.appraise_sync(q)
        print(f"{case.target:16s} {ap.composite.value:18s} {ap.archetype.value:22s} {ap.inus.box.value}")
    print("\nThe association ranking and the causal ranking disagree — that gap is the product.")
    return 0


def cmd_list_cases(args: argparse.Namespace) -> int:
    orch = Orchestrator(online=False)
    for case in orch.fixtures.all_cases():
        print(f"- {case.target} → {case.disease}  "
              f"[area={case.disease_area}, upstream_signal={case.upstream_node_carries_signal}, "
              f"prior={case.prior}, items={len(case.items)}]")
    return 0


def cmd_export_schemas(args: argparse.Namespace) -> int:
    paths = export_all(Path(args.dir))
    for p in paths:
        print(f"wrote {p}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from src.validation import run_validation

    report = run_validation()
    print(report.summary())
    return 0 if (report.all_recovered and report.separation_holds) else 1


def cmd_serve(args: argparse.Namespace) -> int:
    from src.webapp import serve

    serve(host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cauala", description="Causal evidence appraisal for A→B|context.")
    sub = p.add_subparsers(dest="command", required=True)

    ap = sub.add_parser(
        "appraise",
        help="appraise one causal question (online by default)",
        description="Simplest form:  cauala appraise PCSK9 'coronary artery disease'",
    )
    # Positional form is the easy path; flags override for non-default types.
    ap.add_argument("source_pos", nargs="?", help="source symbol, e.g. PCSK9")
    ap.add_argument("target_pos", nargs="?", help="target symbol/label, e.g. 'coronary artery disease'")
    ap.add_argument("--source", default=None, help="source symbol (overrides positional)")
    ap.add_argument("--source-type", default="gene", choices=[t.value for t in NodeType])
    ap.add_argument("--target", default=None, help="target symbol/label (overrides positional)")
    ap.add_argument("--target-type", default="disease", choices=[t.value for t in NodeType])
    ap.add_argument("--edge", default="causal_risk", choices=[e.value for e in EdgeType])
    ap.add_argument("--format", default="md", choices=["md", "json", "html"])
    ap.add_argument("--out", default=None, help="write to file instead of stdout")
    ap.add_argument("--offline", action="store_true",
                    help="use only curated offline fixtures (default is online: live databases)")
    ap.add_argument("--raw", default=None, help="the free-text question, for the record")
    ap.add_argument("--cell-type", default=None)
    ap.add_argument("--tissue", default=None)
    ap.add_argument("--ancestry", default=None)
    ap.add_argument("--sex", default=None)
    ap.add_argument("--disease-subtype", default=None)
    ap.add_argument("--stage", default=None)
    ap.set_defaults(func=cmd_appraise)

    d = sub.add_parser("demo", help="run all curated known-answer cases")
    d.set_defaults(func=cmd_demo)

    lc = sub.add_parser("list-cases", help="list the offline curated evidence store")
    lc.set_defaults(func=cmd_list_cases)

    es = sub.add_parser("export-schemas", help="write JSON Schemas for external consumers")
    es.add_argument("--dir", default="schemas")
    es.set_defaults(func=cmd_export_schemas)

    v = sub.add_parser("validate", help="run the calibration/separation harness")
    v.set_defaults(func=cmd_validate)

    sv = sub.add_parser("serve", help="launch the web app (browser UI); honours $HOST/$PORT")
    sv.add_argument("--host", default=None, help="default 127.0.0.1, or $HOST")
    sv.add_argument("--port", type=int, default=None, help="default 8000, or $PORT")
    sv.set_defaults(func=cmd_serve)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
