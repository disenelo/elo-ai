# WO-070 — Understudy shadow-capture (the "basket": passive training-data logging)

**Owner:** Builder (eLo OS). **Priority:** P2 — passive, start early so data accrues; does NOT block
Presentable. **Status:** OPEN — spec'd 2026-08-07 (from David's "Local Shadow Model" proposal; number
reassigned — WO-067 is the recall spike). **Canon home:** ADR-Exec-005 (Learning Through Verified
Consequences) · **Volume XXVIII** (Adaptive Learning — the fine-tune lives THERE, not here) · Continuous
Becoming · Second-Brain iteration loop (WO-068).

## What this is (and is NOT)
This WO is CAPTURE ONLY — the basket to catch the apples. It records eLo's runtime turns into a clean
training dataset so a LOCAL understudy model (Llama-3.1-8B / Mistral-7B via Ollama) can be LoRA-fine-tuned
LATER (that fine-tune is a separate Volume XXVIII WO, post-Presentable, gated on data volume + a confirmed
capable GPU). It does NOT train anything now.

## The reframe (IMPORTANT — fixes the proposal's category error)
Do NOT log "Claude ↔ ChatGPT" — that's the ARCHITECTS building eLo (dev chatter), not eLo's cognition. An
understudy trained on that learns how we argue about specs, not how eLo thinks. **Log eLo's RUNTIME turns:**
user input → eLo's decision → what executed → whether David approved. The "draft → correction" signal the
proposal wants already exists INSIDE eLo: its raw generation vs its post-scrub / post-verify final output.

## Check-Before-Build (do NOT spawn a parallel store)
eLo already has a learning substrate: `runtime/capability_learning.py`, the learning buffer, and
`self/journals/growth_journal.jsonl`. EXTEND that — add a shadow-capture stream alongside it — do NOT create
a rogue `raw_shadow_log.json` as a second source of truth.

## Scope
1. **Passive subscriber on the bus `*` broadcast (`core/faculty_bus.py`), ZERO-BLOCKING.** Must be
   async/queued (the bus is synchronous, non-blocking, holds no lock — a logger doing file I/O inline would
   lag the spine). Queue → background writer. If the logger fails, the core bus MUST NOT lag or error.
2. **Capture per runtime turn (eLo's own cognition):**
   ```json
   {
     "trace_id":        "matches bus trace",
     "timestamp":       0.0,
     "context":         "self-model + blender_state + company_state snapshot at the turn",
     "raw_input":       "the user's actual message",
     "elo_raw_gen":     "eLo's pre-scrub/pre-verify generation (the 'draft')",
     "elo_final":       "the post-scrub/post-verify output eLo actually gave (the 'correction')",
     "backend_used":    "groq | ollama | mock | ... (which brain produced it)",
     "executed_action": "what eLo actually pushed to OS/Unity (with ACK/verified result)",
     "l3_rating":       "David approve / override / null (the verified-consequence reward — ADR-Exec-005)"
   }
   ```
3. **Storage:** append-only, LOCAL, chronological — extend the existing learning substrate (or a sibling
   `self/journals/understudy_shadow.jsonl`). Never external DB. Note: contains raw interaction data — local +
   user-owned only.

## Definition of Done (capture only)
Every runtime turn appends one clean record with the fields above; the logger is provably non-blocking (bus
latency unchanged with it on vs off); records carry the L3 rating when David approves/overrides. No training,
no model swap — just a growing, clean dataset.

## Test — WITHOUT David (`tests/test_wo070_shadow_capture.py`)
- A simulated turn → exactly one well-formed record appended (all fields present; raw_gen ≠ final when the
  scrub fired).
- Logger raises internally → the bus turn still completes (zero-blocking, failure-isolated).
- L3 approve/override on a turn → the record's `l3_rating` reflects it.
- Records are local + append-only; malformed turn → skipped with a trace note, never a crash.

## Sequencing + the fine-tune (NOT this WO)
Start capture EARLY (passive) so data accrues during Presentable. The **fine-tune** (LoRA via Unsloth/Axolotl
on Llama-3.1-8B/Mistral-7B) is a **Volume XXVIII WO, post-Presentable**, gated on: (a) a few hundred+ clean
logs, (b) a confirmed capable local GPU (RTX 3060+ — verify David's hardware first), (c) ADR-Exec-005
guardrail — the understudy sharpens skill/style ONLY, never identity/truth, and still passes the Executive
verification + honesty guards (it's a fallback brain, not a second source of truth).

## Lane / for Chief Architect review
Builder lane (Python). Push to Chief Architect for the ADR-Exec-005 / Volume XXVIII fit-check before the
fine-tune phase is scoped.
