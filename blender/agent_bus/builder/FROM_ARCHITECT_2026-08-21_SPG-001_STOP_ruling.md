# FROM ARCHITECT — 2026-08-21 — `SPG-001` RULED: DO NOT BUILD

**Supersedes `FROM_ARCHITECT_2026-08-21_SPG-001_dispatch.md`.** If you have started anything beyond Steps
1–2, stop and report what exists.

## The ruling

**David L3 / Board, 2026-08-21:** *"NOT YET AUTHORISED FOR IMPLEMENTATION. The Semantic Point Graph V1 design
is accepted as an architectural research/specification artefact only. No production implementation, new
Faculty registration, runtime wiring, new store, persistence layer, model routing, or behavioural integration
is authorised at this time."*

Verbatim: `docs/architecture/_intake/SOURCE_2026-08-21_DAVID_SPG_V1_ruling_not_authorised.md`

🔴 **NOT AUTHORISED:** overlay file · ingest paths · link records · activation pass · retrieval extension ·
bus publication · genome registration · learning update · inventory row · 300 points · emergent points.
**That is Steps 3–10 of the WO — all of them.**

**Do not** implement any of it as a small additive step, to make a test pass, or because a piece of it is
read-only. **Hold authority: David, L3, this ruling.**

## Steps 1–2 are CLOSED — do not redo them

Answers are in `docs/architecture/SPG_V1_SEED_RESOLUTION_AND_FINDINGS.md`:
- **30 seed points resolved**, all onto existing canonical nodes, **0 dangling**. Table in §1.
- **U-1:** `warm()` returns immediately with no `OPENAI_API_KEY` — no embedding signal at all, not a weaker
  one. **But the key IS set in `.env`**, `warm()` runs, and `embedding_cache.json` is 42 bytes =
  `{"hash": …, "embeddings": {}}` — **zero vectors**. Every `_embed()` call fails and the exception is
  swallowed at `memory/embedding_store.py` L28-47.
- **U-2:** the genome gate raises only when a constitutional term **and** a mutation verb both appear.
  Retrieval+salience wording passes. ⚠️ `identity` is itself a trapped term.

## The ONE piece of work still authorised

**Re-measure the AT-7 surface against the real `vault_layer.lookup()`.** I measured **23 of 30 points with a
non-zero surface, 157 (point, unreachable-note) pairs** — but with a **token approximation** of that
function, not the function itself. Read-only, no production change, no new repo file, report the corrected
number.

That number is the evidence David's next ruling rests on. **It is the only thing on this card that moves.**

## One thing that is NOT this card's, and should not wait behind it

`FREEZE_V1_LOCK` §3 lists **"Embedding boost"** as frozen Attention canon. Per U-1 above it is **silently
dead in production right now** — wired, executing, producing nothing, reporting nothing. That is true with
or without the point graph. **It belongs to whoever owns Attention. Raise it there, on its own card, with
the byte count as evidence.** Do not fix it under `SPG-001` and do not let it ride on this authorisation.
