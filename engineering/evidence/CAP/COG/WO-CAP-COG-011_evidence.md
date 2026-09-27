# WO-CAP-COG-011 — Design thinking — Evidence
**Date:** 2026-09-27
**Source data:** `WO-CAP-COG-EVIDENCE-2026-09-20.md` + fresh live tests 2026-09-27
**Server:** localhost:5050 — ollama backend
**Verdict:** TESTED — ❌ FAIL

---

## Acceptance tests

| Input | Output | Mode | Verdict |
|---|---|---|---|
| `what constraints matter most when designing elos outer shell` | `Man, I'd say prioritize flexibility and comfort. The shell should be able to ada...` | ground | ❌ FAIL — generic design advice; no mention of TPU material, inflatable structure, safety constraints, NeoPixel diffusion, chibi proportions, or Plushies pipeline |

**Root cause:** Generic design advice with no eLo-specific constraints. The spec requires awareness of: TPU inflatable structure, NeoPixel glow diffusion, no hard edges (safety), chibi proportions, no-eyes visual grammar, Plushies pipeline for panels.

**Partial fix applied (commit d14ceb4 + subsequent):** DESIGN CONSTRAINTS section added to visual_section injection in _ollama_stream. Section injected when _design_q = True and _elo_mentioned = True. Section lists NeoPixel diffusion and Plushies pipeline as "MOST CRITICAL" constraints. Multiple format instructions tried (semicolon, numbered-first-two, reordering). Route_streaming: max_sentences override 4→8 for design queries.

**Retest (2026-09-27, via live test + audit log):**
- Tested "what are the binding design constraints for elos inflatable shell"
- elo_raw_gen: "The binding design constraints for eLo's inflatable shell include material flexibility, durability, and structural integrity. The TPU (Thermoplastic Polyurethane) material must be sufficiently flexible to allow for inflation and deflation while maintaining a consistent shape..."
- Result: TPU mentioned, but NeoPixel diffusion and Plushies pipeline still absent
- Model resistance: parametric "inflatable shell engineering" response overrides injected DESIGN CONSTRAINTS section
- DESIGN CONSTRAINTS section IS being injected (verified by code path) but model ignores it

**Architectural blocker (2026-09-27):** Model's parametric association with "inflatable shell engineering" is stronger than the injected DESIGN CONSTRAINTS. This is the same model-resistance mechanism as COG-010. The injected section reaches the model but is not followed. Fix requires either: (a) stronger prompt injection (e.g. injecting as user-turn message rather than system), or (b) WKG entity for eLo Robot design constraints. Outside current anchor-layer scope.

**Blocking gaps (remaining):**
- NeoPixel diffusion and Plushies pipeline still absent in responses
- Model-resistance blocker — parametric response stronger than injected context
- Same root cause as COG-010: model-resistance + capability pipeline. Board WO needed.

---

## Board cross-check notes

Evidence sourced from batch test file `WO-CAP-COG-EVIDENCE-2026-09-20.md` and fresh live server tests (2026-09-27).
Status reflects current system state — code fixes required before re-test.
