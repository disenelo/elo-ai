# Board Review — Bypass Path Audit (IS-ELO: single decision authority)

**Filed by**: Builder 1  
**Date**: 2026-10-06  
**Status**: AUDIT COMPLETE — 43 bypass paths documented. No changes made.

---

## IS-ELO question

*"Is there actually one cognitive authority?"*  
Board verdict: NO — three paths: main pipeline, inner_thought daemon, Presence/Unity.

Builder 1 assignment: audit all paths in server.py that produce output without going through the Executive. File each bypass.

---

## Findings

43 `return {"response": ...}` calls exist in `_process_turn` BEFORE the main LLM/Executive path runs (line ~5370 onward). All are "short-circuit" returns.

### Category A — Safety guards (2 paths, INTENTIONAL, KEEP)

| Line | Backend | Description |
|---|---|---|
| 2555 | guard | Input loop guard — malformed input |
| 2656 | jailbreak-guard | Identity attack detected (`_JB_RE.search(raw)`) |

**Board verdict needed**: These are correct. They intentionally bypass cognition. No fix required.

### Category B — Diagnostic / self-reference (12 paths, lines 2670–3039)

Short-circuit responses to internal questions about eLo's own state (embodiment, Spotify, robot strategy, WKG status, feelings, mission, agency, self-model, architecture, thinking, capabilities, intentions).

| Line range | Backend | Description |
|---|---|---|
| 2670 | direct | Device name / embodiment query |
| 2696 | direct | Location query |
| 2712 | spotify_agent | Spotify passthrough |
| 2734–3039 | direct (×9) | robot strategy, embodiment, WKG, feelings, mission, agency, self-model, architecture, thinking, capability, intentions |

**Issue**: These all fire on keyword matching BEFORE the Executive sees the input. They produce LLM-generated responses without cognition context (no vault, no WKG, no attention). eLo's answer to "what do you believe?" is a string in source code, not drawn from its actual accumulated state.

**Fix (P2 — after causal chain is proven)**: Route these through the Executive as `action: "self_reference"` with the current self_model, WKG, and vault context injected. The Executive answers from state, not from hardcoded strings.

### Category C — OS-level commands (10 paths, lines 3066–3477)

| Line range | Backend | Description |
|---|---|---|
| 3066–3138 | computer_control (4 paths) | CC cancel/execute/disabled/confirm |
| 3170 | anim_cmd | Animation command |
| 3191 | scale_cmd | Scale command |
| 3202 | invade_cmd | Presence invade |
| 3227 | grounding_diag | Grounding diagnostic |
| 3277–3294 | video_ctrl (2 paths) | Video control |

**Status**: These are OS-level actuations, not conversational responses. Intentional bypasses. KEEP as-is. Logging them to the decision trace would be useful (future P3).

### Category D — Media controls (8 paths, lines 3324–3477)

YouTube volume/app (×3), media open (×2), push notification (×1), reference search (×2).

**Status**: Direct actuations. KEEP. Add to decision trace log (future).

### Category E — App switch + self-reference rationale (3 paths, lines 4008–4149)

| Line | Backend | Description |
|---|---|---|
| 4008 | app_switch | App switch command |
| 4140 | self_ref_rationale | Self-reference with rationale |
| 4149 | self_ref_empty | "Don't have that on record yet" |

**Status**: `self_ref_rationale` and `self_ref_empty` are the least defensible — they fire when David asks eLo about itself, return hardcoded text, and bypass WKG/vault. Same Category B fix applies.

---

## Summary

| Category | Count | Verdict |
|---|---|---|
| A — Safety guards | 2 | KEEP — correct |
| B — Self-reference (keyword-matched) | 12 | FIX — route through Executive with state |
| C — OS actuations | 10 | KEEP — intentional; add to decision trace |
| D — Media controls | 8 | KEEP — intentional |
| E — App/self-ref | 3 | FIX (self-ref); KEEP (app_switch) |

**Actionable items for Board:**
1. P2 fix: Category B + E self-reference paths → Executive routing with WKG/vault context
2. P3 nice-to-have: Categories C/D add `backend` to `decision_trace` so they appear in the audit log

---

Builder 1 · 2026-10-06
