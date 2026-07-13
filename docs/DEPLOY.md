# Hosting CAUala as a website

> 🧭 **Use — host it.** Put CAUala on a public URL so non-CLI users can just visit and ask. Ship-ready configs (`Dockerfile`, `render.yaml`, `Procfile`, `fly.toml`, HF Space) live in the repo root. Docs map: **[docs index](README.md)**.

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
| **Hugging Face Spaces** | free | science/bio audience, zero DevOps | `Dockerfile` + `deploy/huggingface-space-README.md` |
| **Render** | free tier | simplest "connect a GitHub repo" | `render.yaml` |
| **Railway** | small credit | fast Git deploys | `Procfile` |
| **Fly.io** | scales to zero | global, cheap idle | `fly.toml` + `Dockerfile` |
| **Google Cloud Run** | pay-per-use, generous free | scales to zero, containers | `Dockerfile` |
| **Any Docker host / your VPS** | your box | full control | `Dockerfile` |

### A. Hugging Face Spaces (recommended — no command line needed)

You can do this entirely in a web browser. End result: a public URL anyone can visit.

**Step 1 — Make a free Hugging Face account.** Go to <https://huggingface.co/join>,
sign up, confirm your email.

**Step 2 — Create the Space.** Go to <https://huggingface.co/new-space> and set:
- **Owner:** your username. **Space name:** `cauala` (this becomes part of the URL).
- **License:** optional (e.g. MIT).
- **Select the Space SDK:** click **Docker**, then the **Blank** template.
- **Space hardware:** **CPU basic — Free**.
- **Visibility:** **Public**.
- Click **Create Space**.

**Step 3 — Upload the project files.** On the new Space page open the **Files** tab
→ **+ Add file** → **Upload files**. From Finder, **drag these in, keeping the
folders intact** — this is the minimum the app needs to run:
- `Dockerfile`
- `requirements.txt`
- the `src` folder
- the `registry` folder
- the `scoring` folder

**Do NOT upload the project's own `README.md`** — keep the one Hugging Face created
for you (it holds the config the Space needs). Then scroll down and click
**Commit changes to main**.
> If your browser won't let you drag a whole folder, upload one folder at a time:
> Upload files → drag `src` → commit; repeat for `registry` and `scoring`.

**Step 4 — Let it build.** The Space rebuilds automatically after the commit. A
**Building** badge appears (top right); it takes ~2–5 minutes. Click **Logs** to
watch progress if you like.

**Step 5 — Open and share.** When the badge turns to **Running**, the app appears on
the page. Your public URL is `https://huggingface.co/spaces/<your-username>/cauala`
— share that. (Free Spaces sleep after a couple of idle days and wake on the next
visit, ~30 s cold start.)

**If the Space shows a "config error" or a blank/timeout screen:** open the **Files**
tab, click `README.md`, click the pencil (edit), and make sure the very top of the
file is exactly this block (then commit) — it tells the Space to serve on port 7860,
which is what the app listens on:

```
---
title: CAUala
emoji: 🐨
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---
```

A ready-made copy is in [`deploy/huggingface-space-README.md`](../deploy/huggingface-space-README.md).

**Updating later:** edit any file from the **Files** tab (or re-upload it) and
commit — each commit triggers a rebuild.

### B. Render

1. Push to GitHub.
2. Render → **New → Blueprint** → select the repo. It reads `render.yaml`.
3. Click apply. Live at `https://cauala.onrender.com` (free instance sleeps when
   idle; first hit cold-starts in ~30 s).

### C. Railway

1. Push to GitHub. Railway → **New Project → Deploy from GitHub repo**.
2. It detects `Procfile` and Python. Add a public domain in **Settings → Networking**.

### D. Fly.io

```bash
fly launch --copy-config --now     # reads fly.toml, builds the Dockerfile
```
Live at `https://cauala.fly.dev`. `min_machines_running = 0` scales to zero when idle.

### E. Google Cloud Run

```bash
gcloud run deploy cauala --source . --region us-central1 --allow-unauthenticated
```
Cloud Run builds the `Dockerfile`, injects `$PORT`, and scales to zero. Live at a
`*.run.app` URL.

### F. Docker anywhere (or locally)

```bash
docker build -t cauala .
docker run -p 8000:7860 cauala        # then open http://localhost:8000
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
