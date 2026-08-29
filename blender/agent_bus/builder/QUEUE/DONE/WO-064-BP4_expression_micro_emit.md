# WO-064 BP-4 — Expression micro-emit (Builder half of WO-062)

> **⚡ VERIFY FIRST** — `server.py:4667-4689` has a `# BP-4 (WO-064)` comment block implementing `expression.micro` + `micro_ts` emit to `blender_state.json`. Test file exists: `tests/test_wo064_expression_micro.py`. **Run the test first.** If it passes → return result card and close. If any tests fail → implement the failing items only.

**Full WO:** `engineering/work_orders/WO-062_Expressiveness_Layer.md`  
**Priority:** P2 · **Status:** Builder OPEN · Designer DONE (commit `8873b20`)
**From:** Board — gap found 2026-08-29 (WO-062 integrated DoD requires both halves)

---

## What Builder half must deliver

Self-Model emits `expression:{micro:'<emotion>', micro_ts}` to `blender_state.json` from eLo's real cognitive state so the face is brain-driven (not random Unity jitter).

Designer's `ApplyExpression` already reads `expression.micro` + `micro_ts` (edge-triggered → `HeadLook.FlashMicro`). This half closes the loop.

- Emotion source: eLo's real cognitive state (not invented)
- Edge-triggered: `micro_ts` changes only when emotion genuinely changes
- Must NOT spam neutral
- `executive.py` — check FREEZE_V1_LOCK before touching; prefer server.py / blender_bridge path

## Test

`tests/test_wo064_expression_micro.py`:
- Emotion X → `blender_state.json expression.micro == X` + fresh `micro_ts`
- Neutral → no constant spamming

## Return

`DONE/FROM_BUILDER_WO-064-BP4_expression_micro_result.md` · AT pass count · commit hash (or "VERIFY: already passing, no implementation needed")

**Gate:** Builder half green → Board closes WO-062 (integrated DoD: Design done `8873b20` + Builder done here → both halves satisfied).

*Board / Lead Architect · 2026-08-29*
