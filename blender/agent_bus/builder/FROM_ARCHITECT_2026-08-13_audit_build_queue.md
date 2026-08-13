# ▶ BUILDER — AUDIT FINDINGS ARE NOW THE PRIORITY. 5 new cards in your QUEUE.

David 2026-08-13: **"the priority was the audit findings and fixing them and the gaps."** The robot spec in
`ROBOT_SPEC/` is REFERENCE ONLY — file it, don't work it. Card `03` (robot Pi bridge) stays design-only, P3.

**Work your QUEUE lowest-number-first. New cards 04–08, all derived from the canon audit
(`docs/architecture/AUDIT_MASTER_2026-08-10.md`).**

| Card | What | Why it matters |
|---|---|---|
| **02** | WO-097 — EmbodimentState publishes EMPTY every direct-response turn (`build_embodiment_state`:503 runs before `_conversation_faculty`:509) | **live silent defect** |
| **04** | **WO-CANON-VII — close Ruling C.** `exec_decide()` at `server.py:2322` runs BEFORE `spine.run()` assembles → **eLo still decides before he assembles.** Also fix AT-1, which passes while the invariant is violated because it inspects only `spine.py` | **THE audit headline** |
| **05** | WO-CANON-VI — Ruling B: `runtime/working_memory.py` is built, tested, **imported nowhere**; wire it as THE single attention driver, recast `core/attention.py` as a relevance-filter supplier | two attentions = One-Brain violation |
| **06** | WO-CANON-XII + XV — wire perception→world-state copy; faculties read the world ONCE; promote the fidelity guard to structured flags | the sensor drift Vol XV exists to remove |
| **07** | WO-CANON-VIII — **`reinforce()` is never called on retrieval**, so the forgetting curve has no counterforce; wire the single logical MemoryFaculty | memories decay even when used |
| **08** | WO-CANON-IV — write the **ordering tests** for every invariant in `Volume_IV/02`; each must FAIL if the sequence changes | two invariants were violated **silently** |

## The pattern worth naming
Every defect the audit found was **silent** — swallowed exception (WO-096), empty publish (WO-097),
assemble-after-decide passing a test that looked at the wrong file, `reinforce()` never called. **Card 08 is
the antidote:** make the contracts testable so drift is loud instead of invisible.

Canon backing each card: `Volume_VII/` · `Volume_VI/` · `Volume_XII/` + `Volume_XV/` · `Volume_VIII/` ·
`Volume_IV/`. Rulings: `docs/architecture/CANON_RULINGS_2026-08-10.md`.
Report each close to your outbox with the commit hash; the Architect reconciles.
