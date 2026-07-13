# CAUala — 3-minute demo transcript

**Format:** spoken narration + `[ACTION]` stage directions. Target ~3:00.
**Setup before recording:** browser tab open at `cauala.onrender.com` (warm it up first — the free tier sleeps and takes ~30 s to wake), and a terminal in the repo with the venv active. Total spoken ≈ 440 words.

---

## [0:00 – 0:25] — Introduction: the expensive mistake

> "Most of biology quietly measures **association** — that A and B move together — and then talks about it as **causation** — that A *drives* B. That slip is one of the most expensive mistakes in the field: chasing a drug target for ten years only to learn it was a passenger, or giving a patient a drug that can't help them.
>
> I built **CAUala** to make that mistake harder to make. It turns *'A is associated with B'* into *'A causes B, in this context, to this degree, with this confidence — and here's the experiment that would prove me wrong.'*"

`[ACTION]` On screen: the CAUala home page (`cauala.onrender.com`), title visible.

---

## [0:25 – 1:05] — The reveal: correlation and causation disagree

> "Here's the whole point in one screen. I'll run five targets the field has already paid to learn."

`[ACTION]` Switch to terminal. Run:

```bash
.venv/bin/python -m src.cli demo
```

`[ACTION]` The known-answer table prints:

```
target           tier (headline)    position               INUS box
PCSK9            causal_driver      validated_driver       necessary_and_sufficient
HDL-C            refuted            associated_noncausal   undetermined
CRP              likely_noncausal   displaced_signal       undetermined
APP/amyloid      likely_causal      upstream_initiator     necessary_and_sufficient
tau              plausible          downstream_mediator    undetermined
```

> "**HDL cholesterol** correlates *beautifully* with heart disease — and CAUala calls it **refuted**, because every drug that raised HDL failed. **Amyloid** correlates only *weakly* with Alzheimer's — and CAUala calls it **likely causal**. A tool that ranked by correlation would get both backwards. That gap — where association and causation disagree — is the product."

---

## [1:05 – 2:10] — Live: scoring a gene from real databases, right now

> "And it's not a lookup table. Let me score a gene it has no curated answer for — live."

`[ACTION]` Switch to browser. Type **`LRRK2`** and **`Parkinson disease`** into the form. Submit.

`[ACTION]` The progress stream ticks through in real time — point at it:

> "Watch what it's doing: it resolves the gene, then queries **real genomics databases over the network** — Open Targets genetics for the GWAS and rare-variant signal, gnomAD for constraint — and scores what comes back through a causal lens."

`[ACTION]` The report renders. Scroll to the headline verdict.

> "Verdict: **likely causal**, an **upstream initiator** — earned entirely from live human genetics, no hand-curation. Every number pulled from a database is tagged **`[RETRIEVED]`**, so you can verify it at the source. Nothing is presented as a checked fact that hasn't been checked."

`[ACTION]` Scroll to the 8-axis spider chart and the "next experiment" line.

> "This spider chart is the causal profile across eight axes. And down here it tells you the **single next experiment** that would most move the verdict."

---

## [2:10 – 2:45] — Why you can trust it: it gates, it doesn't sum

> "The discipline is in the scoring. It **gates** instead of adding things up: a gorgeous biochemical pathway can *never* buy a causal score, and direction has to come from genetics or perturbation — never from cross-sectional correlation, which carries zero directional information. When evidence conflicts, a failed intervention forces the verdict *down* — that's exactly why HDL lands at refuted. The scoring core is deterministic Python, so results are reproducible; the language model only reads the question and writes the prose — it never touches a score."

`[ACTION]` Briefly show the confidence band on the report (a band, not a bare number).

> "And the confidence is shown as a **band**, never a false-precision number, because it isn't calibrated yet — and the tool says so."

---

## [2:45 – 3:00] — Close

> "CAUala is a deterministic causal-reasoning core, four live database connectors, a CLI, and this web app — built end to end with Claude. It's the first rung of a ladder toward precision medicine: from *'A is associated with B'* to a causal claim you can actually act on. Thanks."

`[ACTION]` End on the rendered report, spider chart visible.

---

### Timing cheat-sheet

| Segment | Time | The one thing to land |
|---|---|---|
| Intro | 0:00–0:25 | Association ≠ causation is an expensive mistake |
| The reveal | 0:25–1:05 | HDL refuted, amyloid causal — correlation gets both backwards |
| Live demo | 1:05–2:10 | Scores a gene from real databases, live, with citations |
| Trust | 2:10–2:45 | It gates, it doesn't sum; deterministic core |
| Close | 2:45–3:00 | Built with Claude; first rung to precision medicine |

**Fallback if the network is slow:** the live LRRK2 query normally returns in under a minute, but if the hosted app is cold or the databases lag, run the same query in the terminal instead — `.venv/bin/python -m src.cli appraise LRRK2 "Parkinson disease"` — or fall back to `--offline` for a guaranteed instant result, and narrate over that.
