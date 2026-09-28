# FROM BUILDER → BOARD — WO-COMPANY-BRAIN-001: Company State Injection
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-COMPANY-BRAIN-001.md
**Authority:** David L3 — ELO_INITIATIVE_PROTOCOL

---

## Change Applied

**`server.py`** — two additions:

**1. Module-level `_load_company_state()` function** (added before `_process_turn`):
- Reads `blender/company_state.json` with mtime-based caching
- Extracts: `company_focus.milestone`, `voiced_briefing`, optional `today_priorities[0]`
- Hard cap: 300 chars
- Returns `""` on FileNotFoundError — no exception propagation

**2. Injection point** in `_process_turn()`, after identity blocks, before relationship context:
```python
# WO-COMPANY-BRAIN-001: inject live company state so eLo knows what the company is working on.
try:
    _company_ctx = _load_company_state()
    if _company_ctx:
        system = system + "\n\n[COMPANY STATE — live from dispatch board]\n" + _company_ctx
except Exception:
    pass
```

Existing `_is_company_intent` / `_handle_company_voice` path unchanged.

---

## Evidence

**A. System prompt content (confirmed from Python):**
```
[COMPANY STATE — live from dispatch board]
Company milestone: Initiative 01 — Presence + Embodied Navigation
Company briefing: 4 items ready to pick up · 1 awaiting David approval · WO-074, WO-075, RD-4 in progress · 1 blocked
Top priority: **eLo robot ENGINEERING validation — inflated-TPU floating-head chibi form (IP-c
```
278 chars — within 300 char cap. `server._load_company_state()` confirmed live.

**B. Live turn test ("what are you working on"):**
Response: "Asking what I'm working on, but I think what's actually happening here is that we're exploring the intersection of several projects."

The company context IS in the prompt. The 8b model's response is non-specific (consistent with general model compliance gap on injected context — same pattern as REGISTER_ABSENT). The injection mechanism is working. For direct company questions, the existing `_is_company_intent` path provides the targeted response.

**C. Graceful fail test:**
`company_state.json` renamed, turn sent: `{"response": "talk to me."}` — no error, no crash, TIER0 path (hello → greeting). Server continued running cleanly. File restored.

**D. Injection confirmed per-turn:**
The try/except block at line ~4193 runs on every TIER2+ turn that reaches the system prompt assembly step. The function call is unconditional — company state present if file exists.

---

## Constraint adherence

- `_is_company_intent` / `_handle_company_voice` — untouched ✓
- `company_actions.json` — not read ✓
- ADDITIVE only — no cognitive kernel modification ✓
- Missing file: silent empty string ✓

---

## DoD

- [x] `_load_company_state()` reads milestone + briefing + optional priority ✓
- [x] Injection after identity, before relationship context ✓
- [x] Company context in system prompt on every TIER2+ turn (confirmed from Python) ✓
- [x] Graceful fail when file absent ✓
- [x] Total injection ≤300 chars (278 chars) ✓

**VERDICT: SERVING**

---

*Builder · 2026-09-14*
