# WO-068 — Capture · Prepare · Hold the Thread (eLo as the working companion)

**Owner:** Builder (eLo OS — actions + persistence). **Priority:** P1 (this IS the brain-tuned vision made
testable). **Status:** OPEN — spec'd 2026-08-07. **Depends on:** WO-066 (routes intent to these actions) +
WO-067 (recall for last-state). **Canon:** Vision Spine "eLo is tuned to David's cognition — catch the
thought, remove admin friction, hold the thread" (2026-08-07) · ADR-Exec-001 (confirm the real action, never
narrate it as done) · L3 (prepare, never auto-fire what writes/spends).

## Why (live transcript, 2026-08-07 — three misses, all the SAME class: narrate instead of ACT)
1. **Catch the thought:** "…this insane idea for the UI loop… just write it down somewhere because I'm going
   to lose the thread in a minute." → eLo narrated it back and **saved nothing.**
2. **Prepare admin:** "I need the invoice for Client X sorted for the database work over the last fortnight,
   just get it ready so I can look at it." → "Sounds like a hungry sprint." **Did nothing.**
3. **Hold the thread:** "tell me exactly where we left off on the core bus script before I walked away." →
   "I don't have the exact spot saved." **No last-state persistence.**

These are missing ACTIONS, not parse bugs. They are exactly the anti-thought-loss / anti-friction / continuity
capabilities the Vision Spine now names.

## Scope — three actions, each VERIFIABLE (it did the thing, not said it)
### A. CAPTURE — "write this down" → durable note + honest confirm
On a capture intent ("write it down", "note this", "before I lose it"), eLo appends the idea VERBATIM (+ ts,
+ light tag) to a durable store (e.g. `self/ideas_log.jsonl`) and confirms WHERE it landed. Never just
reflects it. Safe action (a note) — no L3 gate needed.

### B. PREPARE — "get the invoice ready" → draft prepared, NOT fired, pointer returned
On a prepare/admin intent, eLo PREPARES a draft via the existing `tools/draft_agent` (invoice/doc draft with
the stated fields — client, work, period), writes it to a review location (e.g.
`~/Company_Vault/Invoices/DRAFT_*.md`), and tells David where it is. **It does NOT send/finalise** — David
reviews + approves (L3). If a required field is missing, ask ONE targeted question, don't invent.

### C. HOLD THE THREAD — last-state log + "where did we leave off"
Persist a lightweight "last state" on topic-switch / exit (what was being worked on + the last few concrete
points). On "where did we leave off on X" → answer from that log (with WO-053 confidence/source). If nothing
is logged, say so honestly — but the log must be populated going forward so the answer becomes real.

## Definition of Done (full behaviour, end-to-end)
Say "write this down" → it's in the store, confirmed. Say "get the invoice ready" → a draft exists at a named
path for review, nothing sent. Say "where did we leave off" → eLo tells you, from the log. All three are
ACTIONS eLo performed and can prove, not lines it spoke.

## Test — WITHOUT David (`tests/test_wo068_capture_prepare_hold.py`)
- **Capture:** send the UI-loop line → assert `self/ideas_log.jsonl` gained an entry containing the idea
  text + ts; the reply names where it saved.
- **Prepare:** send the invoice line → assert a DRAFT file is created at the review path with client/work/
  period fields; assert NOTHING was sent/finalised (no send call); missing field → one targeted question.
- **Hold:** simulate a work session + topic-switch → assert a last-state entry is written; query "where did
  we leave off" → the reply reflects the logged state (not "I don't have it").
- **Honesty:** with an empty log, "where did we leave off" → honest "nothing logged yet", never fabricated.
Gate: Builder test green → Chief Architect acceptance → David L3 (the three live lines actually DO the thing).

## Phase 2 — Second Brain (VISUAL capture; David 2026-08-07, post-Presentable)
David's "second brain" framing: a text note is you at ~50 bits/sec transcribing what your brain ingested at
~10M bits/sec — it drops the 99% you felt but can't word. A **screenshot keeps the whole signal** cheaply
(~a couple hundred tokens), and AI vision can read the archive back into the principles you couldn't name.
So Capture (A) extends beyond text: **capture what stops you — screenshots + transcripts + drafts — into an
archive, don't pre-sort; let eLo's vision study the whole folder and, walking it with David, turn "why this
is here" into an instruction set; then create FROM the archive, never from blank.**
- **Check-Before-Build:** eLo already HAS vision (`ELO_VISION` on · `tools/vision_loop.py` · screen access
  via WO-021). This is not a new eye — it's a capture-to-archive + vision-recall layer over the existing one.
- **Scope (post-Presentable richness):** a capture action that saves screenshots/text to a `second_brain/`
  archive with light provenance; vision-indexing so eLo can recall by content ("that moody-typography ref");
  ties WO-067 recall (the archive is a recall source). L3: capture is safe; eLo never deletes/sorts without
  David.
- Sits BEHIND Presentable — captured here so the thread isn't lost (that's the whole point).

### The creative-engine system prompt (David's words, verbatim — the operative prompt for the vision layer)
This is the prompt eLo's vision/creative layer runs when it studies the `second_brain/` archive. Stored
verbatim (David 2026-08-07) — do not reword; this is canon for the layer's behaviour.
```
You are the creative engine for this brain. The files in this folder are its second brain: a curated
archive of screenshots, writing, products, interfaces, typography, ideas, and cultural references. Study
them to understand the brand's taste, values, patterns and point of view. Do not copy any single reference.
Collage, remix and translate their underlying principles into one coherent, recognisable brand system.

Use that system to create whatever the brand needs: content, campaigns, websites, apps, products, emails and
experiences that promote the brand, serve its audience and feel unmistakably part of the same world.
```
Note it upholds canon: "Do not copy any single reference… translate underlying principles" = Vision Spine
"references inform original work; eLo stays its own."

### The iteration loop (David 2026-08-07) — a flywheel, not a one-shot
CAPTURE → BUILD → FEED BACK → REFINE. eLo captures the archive; builds from it (the prompt above); the
**built assets feed BACK into the second brain** as new reference; the brand system REFINES on each pass.
Outputs become inputs — the taste model sharpens every cycle instead of staying frozen. Ties **Continuous
Becoming** (eLo never finished) + **Learning Through Verified Consequences** (ADR-Exec-005 — it refines from
what actually got made/kept, not from theory). Engineering note: capture writes to `second_brain/`;
generated assets land in the archive too (tagged as eLo-made vs reference, so provenance stays honest and
eLo doesn't mistake its own output for external taste).

## Lane / relationship
Builder only (Python). Reuses `tools/draft_agent` (prepare), the memory layer + WO-067 (hold), and WO-066
routing (classify capture/prepare/hold intents). L3 guard: PREPARE never sends. This is the concrete
build-out of the Vision Spine brain-tuned point — eLo as the COO that catches, prepares, and holds your thread.
