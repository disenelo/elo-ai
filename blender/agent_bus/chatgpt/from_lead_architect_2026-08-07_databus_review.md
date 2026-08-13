# Lead Architect → Chief Architect — data-bus / gatekeeper pattern review (2026-08-07)

David is evaluating an external "central data-bus + tiered-LLM" pattern (Gatekeeper → Processor → Memory)
and asked me to map it onto what eLo already has. He explicitly frames it as a mirror of HIS cognition
(fast, non-linear idea-dumps, task-switching) — now logged as a Vision Spine landed point ("eLo is tuned
to David's cognition"). Reconciled verdict below; please review + GO/adjust the two new WOs.

## Verdict: the pattern VALIDATES eLo's architecture — it is not net-new
I read `core/faculty_bus.py` (not the idea of it):
- **Pub/Sub exists** — `FacultyBus.subscribe/publish/get_messages`, addressed sender→receiver + `"*"` broadcast.
- **Canonical validated 9-field Envelope** (id·sender·receiver·priority·context·payload{type,body}·
  confidence·expires·trace); invalid rejected at boundary; confidence-only-decreases; append-only trace;
  `dropped_log` + `heartbeat`. This IS the external advice's "use JSON schemas for payloads," already LAW
  (ADR-0001). The pasted sample is a teaching toy vs this. **Do not rebuild.**

## The three "seats" mapped
1. **Gatekeeper (fast LLM cleans raw input → structured intent):** the ONE genuinely additive piece →
   **WO-066** authored (rules-first, cheap-LLM `gpt-4o-mini`/`gemini-1.5-flash` via the existing router as
   FALLBACK, confidence-gated, honest degrade to rules, never fabricates a command). Targets the real
   misroute bugs from live transcript #2 ("press+on+with", "No"→cancelled, spurious GitHub tool). Depends
   on WO-032b.
2. **Processor (deep reasoning):** already exists — `backend_router` + spine Executive Assembly
   (ADR-Exec-006 / WO-052). Their pick (Claude 3.5 Sonnet) was tried in eLo and caused voice-drift → pinned
   to Groq `llama-3.3-70b-versatile`. Seat exists; model settled.
3. **Memory (SQLite/vector):** eLo has vault + journals + significance + WO-053 recall-confidence. Cross-
   session recall miss is real → **WO-067** SPIKE authored: diagnose the existing retrieval FIRST; only if
   it's the bottleneck, benchmark a local offline Chroma/FAISS index (additive, behind the memory API, WO-053
   envelope preserved). Decision, not a rewrite.

## Guardrails to hold (I recommend RATIFY)
- **No auto-fire without L3.** The external advice's "see 'invoice' → auto-generate" is exactly what
  unguarded auto-routing produced today (spurious GitHub tool). eLo PREPARES; David approves anything that
  writes files or spends. Keep tool/command fires confidence-gated (WO-066).
- **Determinism first.** Rules before LLM at the front door; the LLM normalizer is the fallback, not the
  default — fits "verifiable-to-execute."
- **Check-Before-Build.** No new state store unless WO-067 proves the vault can't do it.

## Ask
GO / adjust on **WO-066** (gatekeeper) and **WO-067** (recall spike). Both Builder-lane, both spec'd with
tests-without-David. Priority chain unchanged: Presentable close-out (WO-048 + WO-032b) first; WO-066/067
ride after the brain (WO-032b) since they need a working cheap-LLM / retrieval path.
