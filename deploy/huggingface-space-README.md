---
title: CAUala
emoji: 🐨
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# CAUala — causal evidence appraisal

Ask *does gene A cause disease B?* CAUala retrieves real evidence from genomics
databases (Open Targets, gnomAD), scores it through a causal — not merely
associational — lens, and returns a gated verdict with a cited,
validation-flagged report.

> **To deploy on Hugging Face Spaces:** create a new **Docker** Space, then copy
> the whole CAUala repo into it INCLUDING the `Dockerfile`. Replace the Space's
> auto-generated `README.md` with THIS file (the YAML frontmatter above tells the
> Space to build the Dockerfile and serve on port 7860). Push, and the Space
> builds and goes live at `https://huggingface.co/spaces/<you>/cauala`.

Figures pulled from live databases are tagged `[RETRIEVED]` and must be verified
in-source; curated placeholder citations are tagged `[UNVERIFIED]`.
