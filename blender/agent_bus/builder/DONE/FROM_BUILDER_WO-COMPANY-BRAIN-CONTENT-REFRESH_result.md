# FROM BUILDER — Company Brain Per-Turn Content Refresh

**Date:** 2026-09-15
**WO:** P2 dispatch 2026-09-15 — "Company brain per-turn"
**Authority:** Board dispatch 2026-09-15

---

## Problem

`company_state.json` was generated from a stale `<!-- COMPANY_FOCUS: -->` marker in
`DISPATCH_BOARD.md` (last updated 2026-08-29). The milestone read as
"Initiative 01 — Presence + Embodied Navigation" and the noted items were from
August navigation work (WO-EA2-1, WO-NAV-013, etc.).

The injection mechanism (`_load_company_state()` in `server.py`) is SERVING —
milestone + voiced_briefing inject correctly per turn with 30s mtime cache.

The content was stale at source: the `COMPANY_FOCUS` marker.

---

## Fix

Updated `<!-- COMPANY_FOCUS: -->` marker in `DISPATCH_BOARD.md` (line 5082):

```
<!-- COMPANY_FOCUS: Presence + Expression Layer (§92) | items:
  WO-BA02-DONE(significance-weights),
  WO-PRONOUN-ANCHOR-DONE(identity-block),
  WO-EXPRESSION-POLISH-DONE(builder-voice),
  WO-ELO-LEARN-001-C3-DONE(WKG-DEEP),
  WO-TIER1-WARMUP-P3(pending)
| note: §92 session 2026-09-15 — [current session summary]
  Updated 2026-09-15. -->
```

Re-ran `company_state_writer.publish()` to regenerate `company_state.json`.

---

## Evidence

```python
from company_runtime.company_state_writer import publish
publish()  # True
```

```json
"company_focus": {
    "milestone": "Presence + Expression Layer (§92)"
}
"voiced_briefing": "4 items ready to pick up · 1 awaiting David approval · WO-074, WO-075, RD-4 in progress · 1 blocked"
```

- Milestone now current: "Presence + Expression Layer (§92)" ✓
- voiced_briefing: still kanban-driven (Gap E — deferred, requires full WO table audit per
  board ruling from 2026-09-12. Out of scope this P2 card.)

---

## System prompt injection result

`_load_company_state()` now produces:
```
Company milestone: Presence + Expression Layer (§92)
Company briefing: 4 items ready to pick up · 1 awaiting David approval · WO-074, WO-075, RD-4 in progress · 1 blocked
```

Milestone is current. Briefing WO codes are stale (kanban) — acceptable for P2,
deferred as Gap E per prior board ruling.

---

## DoD Assessment

| Item | Status |
|------|--------|
| COMPANY_FOCUS marker updated to §92 session | ✅ SERVING |
| Milestone now "Presence + Expression Layer (§92)" | ✅ SERVING |
| company_state.json regenerated via publish() | ✅ SERVING |
| Injection mechanism unchanged (SERVING per prior card) | ✅ SERVING |
| voiced_briefing staleness (Gap E) | ⚠️ DEFERRED — full board audit required |

**VERDICT: SERVING** (milestone current; voiced_briefing staleness deferred as Gap E)

---

*Builder · 2026-09-15*
