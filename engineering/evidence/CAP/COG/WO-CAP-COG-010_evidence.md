# WO-CAP-COG-010 — Art and visual language — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ⚠️ PARTIAL (2026-09-27 retest — facts landed, lead ordering still wrong)

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `describe elo visually` | `My body language is a language of its own, conveying emotions and intentions thr...` | build | ❌ FAIL — does NOT mention NO EYES (primary visual distinctive); no chibi proportions, rounded form, inflated TPU shell; generic body-language description |
| `describe elo visually` | `I am a rounded inflatable TPU shell, chibi proportions, approximately 40cm tall. I have a NeoPixel glow that changes color based on my state: teal for idle, coral for speaking, and violet for calm. My expression is conveyed through body posture and glow, as I have no facial features.` | build | ⚠️ PARTIAL — all visual facts present (TPU, chibi, NeoPixel colors, no facial features); does NOT lead with 'No eyes.' as instructed; starts with TPU description instead (retest 2026-09-27, visual section moved before RESPOND, commit 7a52f2d) |

**Root cause:** Visual injection was appended AFTER `_final_respond` directive — model generated response before seeing visual facts (original FAIL). Fixed: visual section now computed before `_sections` assembly and inserted before `_final_respond`. Residual: model parametrically resists 'No eyes.' as opening even with explicit instruction.

**Layer 2 fix (commit c40c012):** `_prepend_no_eyes` flag set when visual identity section injected. Post-processor in `_ollama_call` path: prepends 'No eyes. ' if response doesn't already start with it.

**Layer 2 status:** Post-processor works at generation layer — audit log shows `elo_raw_gen` = correct visual description. However, the capability pipeline (understudy_shadow system) transforms `elo_final` after the fact — `delta_cause: unknown` in audit. This is a separate architectural issue.

**Blocking gaps (remaining):**
- Capability pipeline substitutes final response — `elo_raw_gen` is correct but `elo_final` is replaced by capability handler
- Root cause: `capabilities: vault_write` fires on visual identity queries and transforms final response
- Needs separate investigation in understudy/capability pipeline — outside backend_router.py scope

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
