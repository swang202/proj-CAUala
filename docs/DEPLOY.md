# Hosting CAUala as a website

> 🧭 **Use — host it.** Put CAUala on a public URL so non-CLI users can just visit and ask. Ship-ready configs (`render.yaml`, `Dockerfile`) live in the repo root. Docs map: **[docs index](README.md)**.

Goal: give non-CLI users a URL where they type a gene + disease and get an answer,
while CLI users can still clone the repo.

## First, the one honest constraint

CAUala scores evidence and queries live databases in **server-side Python**. So it
**cannot** run on a pure static host (GitHub Pages, Netlify/Vercel *static*, S3) —
those only serve files and can't run the pipeline. You need a host that runs a
Python process. The good news: several do it free and in a few clicks. All of them
just run this one command:

```
uvicorn src.webapp:app --host 0.0.0.0 --port $PORT
```

The app already reads `$PORT`/`$HOST`, has a `/healthz` check, permissive CORS on
the JSON API, and a concurrency cap (`CAUALA_MAX_CONCURRENCY`, default 4). Config
files for the common hosts ship in the repo root.

## Pick a host

| Host | Cost | Best for | Files used |
|---|---|---|---|
| **Render** ← *currently deployed* | free tier | simplest "connect a GitHub repo" | `render.yaml` |
| **Google Cloud Run** | pay-per-use, generous free | scales to zero, containers | `Dockerfile` |
| **Any Docker host / your VPS** | your box | full control | `Dockerfile` |

### A. Render (currently deployed — recommended)

The live demo runs here: **<https://cauala.onrender.com>**. To reproduce it:

1. Push the repo to GitHub.
2. Sign up at **render.com** and connect GitHub.
3. **New + → Blueprint** → select the repo. Render reads `render.yaml` (build
   `pip install -r requirements.txt`, start `uvicorn src.webapp:app`, health check
   `/healthz`).
4. Click **Apply**. First build takes ~2–4 minutes; you get a URL like
   `https://cauala.onrender.com` that auto-redeploys on every push.

The free instance sleeps after ~15 min idle and cold-starts in ~30–60 s; the **$7/mo
Starter** plan stays always-on if you're presenting live.

### B. Google Cloud Run

```bash
gcloud run deploy cauala --source . --region us-central1 --allow-unauthenticated
```
Cloud Run builds the `Dockerfile`, injects `$PORT`, and scales to zero. Live at a
`*.run.app` URL.

### C. Docker anywhere (or locally)

```bash
docker build -t cauala .
docker run -p 8000:8000 cauala        # then open http://localhost:8000
```
Point any reverse proxy (Caddy/nginx) at it for a custom domain + HTTPS.

## After it's live — checklist

- **Custom domain:** every host above supports adding your own domain + free TLS.
- **SSE through proxies:** the progress stream uses Server-Sent Events. The app
  sends `X-Accel-Buffering: no`; if a proxy still buffers, disable response
  buffering for `/stream` (nginx: `proxy_buffering off;`). The hosts above work
  as-is.
- **Keyed data sources:** Open Targets + gnomAD are keyless and need nothing. To
  add OpenGWAS/OMIM/CLUE later, set their secrets as host env vars (see
  `docs/CONNECTORS.md`) — never bake keys into the image.
- **Load / abuse:** raise or lower `CAUALA_MAX_CONCURRENCY`. Each appraisal makes
  a few outbound DB calls; the cap protects both your box and the upstream APIs.
- **Citations caveat:** the curated causal evidence still uses `TODO:cite`
  placeholder references (shown as `[UNVERIFIED]`). Live figures are real and
  cited but tagged `[RETRIEVED]` (verify in-source). Make sure that's acceptable
  for a public audience before sharing widely — the report states it, but you may
  want a banner of your own.

## Keeping the CLI path

Nothing here removes the CLI. Repo users still run
`python -m src.cli appraise PCSK9 "coronary artery disease"` or
`python -m src.cli serve` locally. The website and the CLI share the exact same
pipeline (`Orchestrator.appraise_events`), so answers match.
