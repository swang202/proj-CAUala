"""
CAUala web app -- a browser front-end for people who don't use the CLI.

    cauala serve            # then open http://127.0.0.1:8000

Three routes:
  GET /              the question form + live activity log + report view (one page)
  GET /stream        Server-Sent Events: streams 'what it's looking at right now'
                     as the appraisal runs, ending with the rendered report
  GET /api/appraise  the full JSON appraisal (for programmatic callers)

The stream reuses Orchestrator.appraise_events, so the browser sees exactly the
pipeline steps the CLI runs -- harmonize, query each database, tier, gate,
classify -- then the same report the CLI produces. Online (live databases) is the
default here too; every figure in the report is cited and tagged for validation.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Optional

from src.orchestrator import Orchestrator
from src.question import Context, EdgeType, Node, NodeType, Question
from src.report import to_html, to_json
from src.resolve import EntityResolver

try:
    from fastapi import FastAPI, Query
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
except Exception as exc:  # pragma: no cover - import-time guard
    raise SystemExit(
        "The web app needs FastAPI + uvicorn. Install them with:\n"
        "  uv pip install --python .venv 'fastapi>=0.110' 'uvicorn>=0.29'\n"
        f"(import error: {exc})"
    )

app = FastAPI(title="CAUala", docs_url="/api/docs")

# The tool is read-only, so allow the JSON API to be called cross-origin (handy if
# someone embeds it from another page). The HTML app serves itself, no CORS needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Cap concurrent appraisals so a public instance never hammers the upstream
# databases or exhausts the box. Tune with CAUALA_MAX_CONCURRENCY.
_MAX_CONCURRENCY = int(os.getenv("CAUALA_MAX_CONCURRENCY", "4"))
_SEM = asyncio.Semaphore(_MAX_CONCURRENCY)


def _question(
    source: str,
    target: str,
    edge: str,
    source_type: str,
    target_type: str,
    ancestry: Optional[str],
    tissue: Optional[str],
    disease_subtype: Optional[str],
    source_id: Optional[str] = None,
    target_id: Optional[str] = None,
    source_label: Optional[str] = None,
    target_label: Optional[str] = None,
) -> Question:
    # When ids are supplied (the user confirmed them in the picker), the nodes are
    # pre-resolved and the pipeline skips its own resolution step.
    return Question(
        source=Node(type=NodeType(source_type), symbol=source, id=source_id or None,
                    label=source_label or None),
        target=Node(type=NodeType(target_type), symbol=target, id=target_id or None,
                    label=target_label or None),
        edge_type=EdgeType(edge),
        context=Context(ancestry=ancestry or None, tissue=tissue or None,
                        disease_subtype=disease_subtype or None),
        raw_text=f"{source} {edge} {target}",
    )


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX_HTML


@app.get("/healthz")
def healthz() -> dict:
    """Liveness/readiness probe for cloud hosts."""
    return {"status": "ok", "service": "cauala"}


@app.get("/stream")
async def stream(
    source: str = Query(...),
    target: str = Query(...),
    edge: str = Query("causal_risk"),
    source_type: str = Query("gene"),
    target_type: str = Query("disease"),
    offline: bool = Query(False),
    ancestry: Optional[str] = Query(None),
    tissue: Optional[str] = Query(None),
    disease_subtype: Optional[str] = Query(None),
    source_id: Optional[str] = Query(None),
    target_id: Optional[str] = Query(None),
    source_label: Optional[str] = Query(None),
    target_label: Optional[str] = Query(None),
) -> StreamingResponse:
    q = _question(source, target, edge, source_type, target_type, ancestry, tissue,
                  disease_subtype, source_id, target_id, source_label, target_label)
    orch = Orchestrator(online=not offline)

    async def gen():
        if _SEM.locked() and _SEM._value <= 0:  # inform the user they're queued
            yield _sse({"stage": "retrieve", "detail": "Busy — waiting for a free slot…"})
        async with _SEM:
            try:
                async for ev in orch.appraise_events(q):
                    payload = {k: v for k, v in ev.items() if k != "appraisal"}
                    if ev.get("stage") == "done":
                        ap = ev["appraisal"]
                        payload["report_html"] = to_html(ap, q)
                        payload["verdict"] = {
                            "tier": ap.composite.value,
                            "archetype": ap.archetype.value,
                            "inus": ap.inus.box.value,
                            "scope": ap.context.describe(),
                            "confidence": ap.posterior.render() if ap.posterior else "not scored",
                        }
                    yield _sse(payload)
            except Exception as exc:  # surface any failure to the browser
                yield _sse({"stage": "error", "detail": f"{type(exc).__name__}: {exc}"})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@app.get("/api/appraise")
async def api_appraise(
    source: str = Query(...),
    target: str = Query(...),
    edge: str = Query("causal_risk"),
    source_type: str = Query("gene"),
    target_type: str = Query("disease"),
    offline: bool = Query(False),
) -> JSONResponse:
    q = _question(source, target, edge, source_type, target_type, None, None, None)
    orch = Orchestrator(online=not offline)
    async with _SEM:
        appraisal = await orch.appraise(q)
    return JSONResponse(json.loads(to_json(appraisal)))


@app.get("/resolve")
def resolve(text: str = Query(...), node_type: str = Query("disease")) -> JSONResponse:
    """Resolve free text to an entity, returning the confident guess or the
    candidates to disambiguate. A GUI can call this as the user types (or on blur)
    to offer a 'did you mean …?' picker before running the appraisal."""
    try:
        nt = NodeType(node_type)
    except ValueError:
        nt = NodeType.DISEASE
    res = EntityResolver(online=True).resolve(text, [nt])
    return JSONResponse({
        "query": res.query,
        "status": res.status,  # resolved | ambiguous | not_found
        "note": res.note,
        "best": ({"id": res.best.id, "name": res.best.name, "entity": res.best.entity}
                 if res.best and res.status != "not_found" else None),
        "candidates": [{"id": c.id, "name": c.name, "entity": c.entity, "score": round(c.score, 1)}
                       for c in res.candidates],
    })


def serve(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Run the app. Honours $HOST/$PORT (set by most cloud hosts) so the same
    entrypoint works locally and in a container."""
    try:
        import uvicorn
    except Exception:  # pragma: no cover
        raise SystemExit("uvicorn is required to serve. Install with: uv pip install uvicorn")
    host = host or os.getenv("HOST", "127.0.0.1")
    port = port or int(os.getenv("PORT", "8000"))
    print(f"CAUala web app on http://{host}:{port}  (Ctrl-C to stop)")
    uvicorn.run(app, host=host, port=port, log_level="warning")


# ---------------------------------------------------------------------------
# The single-page front-end (self-contained: inline CSS + JS, no external deps).
# ---------------------------------------------------------------------------

INDEX_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CAUala — causal evidence appraisal</title>
<style>
  :root { --bg:#0b1020; --panel:#151b30; --ink:#e6ebff; --muted:#93a0c8; --line:#26304f;
          --accent:#5b8cff; --teal:#22d3b7; --warn:#fbbf24; --good:#34d399; --bad:#f87171; }
  * { box-sizing: border-box; }
  body { margin:0; font-family:-apple-system,system-ui,Segoe UI,Roboto,sans-serif; background:var(--bg);
         color:var(--ink); line-height:1.5; }
  header { padding:22px 28px; border-bottom:1px solid var(--line); }
  header h1 { margin:0; font-size:20px; letter-spacing:.2px; }
  header p { margin:4px 0 0; color:var(--muted); font-size:13px; max-width:70ch; }
  .wrap { display:grid; grid-template-columns: 380px 1fr; gap:0; min-height:calc(100vh - 84px); }
  @media (max-width: 860px){ .wrap{ grid-template-columns:1fr; } }
  .left { padding:22px 24px; border-right:1px solid var(--line); }
  .right { padding:22px 24px; overflow:auto; }
  label { display:block; font-size:12px; color:var(--muted); margin:14px 0 5px; text-transform:uppercase; letter-spacing:.5px; }
  input, select { width:100%; padding:10px 12px; background:var(--panel); border:1px solid var(--line);
         border-radius:9px; color:var(--ink); font-size:14px; }
  input::placeholder { color:#5b678f; }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .examples { margin:10px 0 0; display:flex; flex-wrap:wrap; gap:6px; }
  .examples button { background:var(--panel); border:1px solid var(--line); color:var(--muted);
         font-size:12px; padding:6px 10px; border-radius:999px; cursor:pointer; }
  .examples button:hover { color:var(--ink); border-color:var(--accent); }
  details { margin-top:14px; } summary { cursor:pointer; color:var(--muted); font-size:13px; }
  .go { margin-top:18px; width:100%; padding:12px; border:0; border-radius:10px; cursor:pointer;
        background:linear-gradient(90deg,var(--accent),var(--teal)); color:#05122b; font-weight:700; font-size:15px; }
  .go:disabled { opacity:.5; cursor:not-allowed; }
  .chk { display:flex; align-items:center; gap:8px; margin-top:14px; color:var(--muted); font-size:13px; }
  .chk input { width:auto; }
  h2.sec { font-size:13px; text-transform:uppercase; letter-spacing:.6px; color:var(--muted); margin:0 0 10px; }
  #log { font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px; }
  .ev { display:flex; gap:10px; padding:7px 0; border-bottom:1px dashed var(--line); align-items:baseline; }
  .badge { flex:0 0 auto; font-size:10.5px; font-weight:700; padding:2px 7px; border-radius:6px; text-transform:uppercase; }
  .b-start,.b-harmonize,.b-resolve,.b-stack,.b-retrieve{ background:#1e2a52; color:#9db4ff; }
  .b-query{ background:#173a35; color:var(--teal); }
  .b-clarify{ background:#3a2c08; color:var(--warn); }
  .b-assemble,.b-finalize{ background:#2a2350; color:#c4b5fd; }
  .b-gate,.b-classify{ background:#14351f; color:var(--good); }
  .b-done{ background:var(--good); color:#04240f; }
  .b-error{ background:var(--bad); color:#2b0606; }
  .ev .txt { color:var(--ink); }
  .verdict { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; margin-bottom:16px; }
  .verdict .tier { font-size:22px; font-weight:800; }
  .t-causal_driver,.t-likely_causal{ color:var(--good); }
  .t-plausible,.t-unvalidated{ color:var(--warn); }
  .t-likely_noncausal,.t-refuted{ color:var(--bad); }
  .verdict .meta { color:var(--muted); font-size:13px; margin-top:6px; }
  .spin { display:inline-block; width:13px; height:13px; border:2px solid var(--line);
          border-top-color:var(--teal); border-radius:50%; animation:sp .8s linear infinite; vertical-align:-2px; }
  @keyframes sp { to { transform:rotate(360deg); } }
  iframe#report { width:100%; height:78vh; border:1px solid var(--line); border-radius:12px; background:#fff; margin-top:8px; }
  .hint { color:var(--muted); font-size:13px; }
  a.dl { color:var(--teal); font-size:12px; text-decoration:none; }
  #picker { background:var(--panel); border:1px solid var(--warn); border-radius:12px; padding:14px 16px; margin-bottom:16px; }
  #picker h3 { margin:0 0 4px; font-size:14px; }
  .pick { margin:12px 0; }
  .pick-q { font-size:13px; margin-bottom:4px; }
  .pick-note { font-size:12px; color:var(--muted); margin:3px 0 8px; }
  .cand { display:block; width:100%; text-align:left; margin:5px 0; padding:9px 12px; background:var(--bg);
          border:1px solid var(--line); border-radius:8px; color:var(--ink); font-size:13px; cursor:pointer; }
  .cand:hover { border-color:var(--accent); }
  .cand.sel { border-color:var(--teal); background:#13251f; }
  .cand .ent { color:var(--muted); font-size:11px; }
</style></head>
<body>
<header>
  <h1>🐨 CAUala — causal evidence appraisal</h1>
  <p>Ask <b>does A cause B?</b> for a gene/variant and a disease. CAUala pulls real evidence from
     genomics databases, scores it through a causal (not just associational) lens, and returns a
     gated verdict with a validation-flagged, cited report. Live databases are queried by default.</p>
</header>
<div class="wrap">
  <div class="left">
    <h2 class="sec">Your question</h2>
    <label>Source (gene / variant)</label>
    <input id="source" placeholder="e.g. PCSK9, LRRK2, tau" autocomplete="off">
    <label>Target (disease / phenotype)</label>
    <input id="target" placeholder="e.g. Parkinson disease" autocomplete="off">
    <label>Edge (which arrow?)</label>
    <select id="edge">
      <option value="causal_risk">causal_risk (gene → disease risk)</option>
      <option value="genetic_risk">genetic_risk (variant → disease)</option>
      <option value="causal_effect">causal_effect (do(A) → B)</option>
      <option value="regulatory">regulatory (gene → gene)</option>
    </select>
    <div class="examples">
      <button data-s="PCSK9" data-t="coronary artery disease">PCSK9 → CAD</button>
      <button data-s="CETP" data-t="coronary artery disease">HDL/CETP → CAD</button>
      <button data-s="CRP" data-t="coronary artery disease">CRP → CAD</button>
      <button data-s="APP" data-t="Alzheimer's disease">amyloid (APP) → AD</button>
      <button data-s="tau" data-t="Alzheimer's disease">tau → AD</button>
      <button data-s="LRRK2" data-t="Parkinson's disease">LRRK2 → PD (live)</button>
      <button data-s="LRRK2 G2019S" data-t="Parkinson's disease">LRRK2 G2019S → PD</button>
    </div>
    <details>
      <summary>Advanced</summary>
      <div class="row" style="margin-top:8px">
        <div><label>Source type</label>
          <select id="source_type"><option>gene</option><option>variant</option><option>protein</option></select></div>
        <div><label>Target type</label>
          <select id="target_type"><option>disease</option><option>phenotype</option></select></div>
      </div>
      <label>Ancestry (context)</label><input id="ancestry" placeholder="e.g. EUR" autocomplete="off">
      <label>Tissue (context)</label><input id="tissue" placeholder="e.g. liver" autocomplete="off">
      <label>Disease subtype (context)</label><input id="disease_subtype" placeholder="e.g. early-onset" autocomplete="off">
    </details>
    <div class="chk"><input type="checkbox" id="offline"><label for="offline" style="margin:0;text-transform:none;letter-spacing:0">Offline only (curated fixtures, no network)</label></div>
    <button class="go" id="go">Appraise</button>
    <p class="hint" style="margin-top:14px">Figures from live databases are tagged <b>[RETRIEVED]</b> and must be verified in-source; the report cites every source.</p>
  </div>
  <div class="right">
    <h2 class="sec">Activity — what it's looking at right now</h2>
    <div id="picker" style="display:none"></div>
    <div id="log"><p class="hint">Enter a question and press <b>Appraise</b>. Steps will stream here.</p></div>
    <div id="result" style="display:none">
      <h2 class="sec" style="margin-top:22px">Verdict</h2>
      <div class="verdict" id="verdict"></div>
      <h2 class="sec">Full report <a class="dl" id="download" href="#" download="cauala-report.html">↓ download HTML</a></h2>
      <iframe id="report" title="CAUala report"></iframe>
    </div>
  </div>
</div>
<script>
const $ = id => document.getElementById(id);
document.querySelectorAll('.examples button').forEach(b => b.onclick = () => {
  $('source').value = b.dataset.s; $('target').value = b.dataset.t;
});
let es = null;
const ENTITY_TYPE = {target:'gene', disease:'disease', drug:'drug', variant:'variant'};
function addEvent(stage, detail){
  const row = document.createElement('div'); row.className='ev';
  const badge = document.createElement('span'); badge.className='badge b-'+stage; badge.textContent=stage;
  const txt = document.createElement('span'); txt.className='txt'; txt.textContent=detail;
  row.appendChild(badge); row.appendChild(txt); $('log').appendChild(row);
  $('log').scrollTop = $('log').scrollHeight;
}
async function resolveNode(text, nodeType){
  const p = new URLSearchParams({text, node_type:nodeType});
  return (await fetch('/resolve?'+p.toString())).json();
}
$('go').onclick = async () => {
  const src=$('source').value.trim(), tgt=$('target').value.trim();
  if(!src||!tgt){ alert('Enter a source and a target.'); return; }
  if(es){ es.close(); }
  $('log').innerHTML=''; $('result').style.display='none';
  $('picker').style.display='none'; $('picker').innerHTML='';
  // Offline mode uses the curated table, no online resolution -> stream directly.
  if($('offline').checked){ startStream(src, tgt, {source:null, target:null}); return; }
  // Resolve both endpoints first; only interrupt if something is unclear.
  $('go').disabled=true; $('go').innerHTML='<span class="spin"></span> Resolving…';
  let rs, rt;
  try {
    [rs, rt] = await Promise.all([resolveNode(src, $('source_type').value),
                                  resolveNode(tgt, $('target_type').value)]);
  } catch(err){ $('go').disabled=false; $('go').textContent='Appraise'; alert('Resolve failed: '+err); return; }
  $('go').disabled=false; $('go').textContent='Appraise';
  const picks = {source:null, target:null}, needs=[];
  if(rs.status==='resolved'){ picks.source = pick(rs.best); } else { needs.push(['source', src, rs]); }
  if(rt.status==='resolved'){ picks.target = pick(rt.best); } else { needs.push(['target', tgt, rt]); }
  if(needs.length===0){ startStream(src, tgt, picks); return; }
  showPicker(needs, src, tgt, picks);
};
function pick(best){ return best ? {id:best.id, label:best.name, type:ENTITY_TYPE[best.entity]||'gene', entity:best.entity} : null; }
function showPicker(needs, src, tgt, picks){
  const box = $('picker'); box.style.display='block';
  box.innerHTML = '<h3>Confirm what you meant</h3>';
  needs.forEach(([which, text, res]) => {
    const div = document.createElement('div'); div.className='pick';
    div.innerHTML = `<div class="pick-q">${which} — "<b>${text}</b>"</div>`;
    if(res.note){ const n=document.createElement('div'); n.className='pick-note'; n.textContent=res.note; div.appendChild(n); }
    (res.candidates||[]).forEach(c => {
      const b=document.createElement('button'); b.className='cand';
      b.innerHTML = `${c.name} <span class="ent">${c.entity}</span>`;
      b.onclick = () => {
        picks[which] = {id:c.id, label:c.name, type:ENTITY_TYPE[c.entity]||'gene', entity:c.entity};
        div.querySelectorAll('.cand').forEach(x=>x.classList.remove('sel')); b.classList.add('sel');
        if(picks.source && picks.target){ $('picker').style.display='none'; startStream(src, tgt, picks); }
      };
      div.appendChild(b);
    });
    if(res.status==='not_found'){
      const e=document.createElement('div'); e.className='pick-note';
      e.textContent='No confident match — edit the box on the left and press Appraise again.';
      div.appendChild(e);
    }
    box.appendChild(div);
  });
}
function startStream(src, tgt, picks){
  $('go').disabled=true; $('go').innerHTML='<span class="spin"></span> Appraising…';
  const s=picks.source, t=picks.target;
  const edge = (s && s.entity==='variant') ? 'genetic_risk' : $('edge').value;
  const p = new URLSearchParams({source:src, target:tgt, edge,
    source_type: s? s.type : $('source_type').value, target_type: t? t.type : $('target_type').value,
    offline:$('offline').checked, ancestry:$('ancestry').value, tissue:$('tissue').value,
    disease_subtype:$('disease_subtype').value});
  if(s){ p.set('source_id', s.id); p.set('source_label', s.label); }
  if(t){ p.set('target_id', t.id); p.set('target_label', t.label); }
  es = new EventSource('/stream?'+p.toString());
  es.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    addEvent(ev.stage, ev.detail || '');
    if(ev.stage==='done'){
      const v=ev.verdict;
      $('verdict').innerHTML = `<div class="tier t-${v.tier}">${v.tier}</div>
        <div class="meta">Position <b>${v.archetype}</b> · INUS <b>${v.inus}</b> · Scope ${v.scope}</div>
        <div class="meta">Confidence: ${v.confidence}</div>`;
      const doc = ev.report_html;
      $('report').srcdoc = doc;
      $('download').href = URL.createObjectURL(new Blob([doc], {type:'text/html'}));
      $('result').style.display='block'; $('result').scrollIntoView({behavior:'smooth'});
      finish();
    }
    if(ev.stage==='error'){ finish(); }
  };
  es.onerror = () => { addEvent('error','stream closed'); finish(); };
}
function finish(){ if(es){es.close(); es=null;} $('go').disabled=false; $('go').textContent='Appraise'; }
</script>
</body></html>
"""
