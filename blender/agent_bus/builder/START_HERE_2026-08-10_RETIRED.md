# ▶ BUILDER — START HERE (2026-08-10, current). Supersedes START_HERE_2026-08-04.

**Self-serve from here. Do ONE WO per run, in lane (eLo OS Python only), ship WITH a test that passes
WITHOUT David, run the live round-trip yourself, write your outbox, then take the next. David runs no
commands — his only check is L3 feel.**

## Context that changed (read once)
- **Tier 0 (real brain) is effectively UNBLOCKED.** David's local `llama3.1:8b` is serving; the "running on
  backup" mock line is NOT firing in his latest sessions. So conversation is judgeable now — the mock excuse
  is gone. WO-073 drops to a P2 tidy (confirm routing to llama is intentional; diagnose why Groq flaps) — do
  it LAST, not first.
- WO-048/061 (how's-the-company) + WO-022/037 (recall + `conversing`) are shipped and **IN_REVIEW awaiting
  David's live-confirm** — not blocking you. Keep building down the queue.

## YOUR QUEUE — top to bottom
1. **WO-085 — Proactive-proposal gating (P1, DO FIRST).** The live annoyance David explicitly said he has to
   debug: eLo offering "add to tracker / save to vault" on every screen item, ignoring his "no." Gate the
   proposals (respect a decline, don't re-offer, no fabricated links), AND fix the voice — David: "saying
   vault is weird… feels robotic." Say **"brain" / "hold onto"**, not "vault." Ship with a test that proves a
   declined proposal isn't re-offered.
2. **WO-069 — Multilingual "how are you"** (P2, small). "Como estas?" must be answered in-language, no
   meta-narration. `_HOW_ARE_YOU_POOL` exists at `server.py:966` — it just isn't reached for non-greeting
   multilingual. Wire it.
3. **WO-072 — Intent Gatekeeper** (P1). Rules-first intent normalisation, cheap-LLM fallback. (Cheap-LLM path
   now exists via the local brain — dependency satisfied.)
4. **WO-068 — Capture / Prepare / Hold the thread** (Second Brain). Note: pairs with WO-085's voice fix —
   don't ship "vault" language.
5. **WO-071 — Realtime correction / ICL loop.**
6. **WO-076 — Perception mis-link fidelity** (no fragments, no fabricated links).
7. **Weather-publish carry-forward** (small): publish real weather to `blender_state.json` top-level
   `"weather":"<condition>"` on the normal state tick (see `FROM_ARCHITECT_2026-08-10_weather_publish.md`).
8. **WO-073 — Local brain in the fallback chain (P2 tidy, LAST).** Confirm the llama routing is intended;
   diagnose the Groq flap so the chain is `Groq→Cerebras→Ollama→Mock` cleanly.

Full specs: `engineering/work_orders/WO-0XX_*.md`. Report each close in your outbox; the Architect reconciles.
