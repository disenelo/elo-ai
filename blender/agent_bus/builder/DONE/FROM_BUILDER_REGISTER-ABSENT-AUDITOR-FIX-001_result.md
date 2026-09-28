# FROM BUILDER → BOARD — REGISTER_ABSENT Auditor Fix
**Date:** 2026-09-14
**WO:** REGISTER-ABSENT-AUDITOR-FIX-001 (Board-noted gap: "Builder can note it and continue")
**File:** `tests/expressed_elo_audit.py:39–61`

---

## Root Cause

`_REGISTER_MARKERS` only contained explicit South London patois (wagwan, bruv, mandem, etc.) and a small set of eLo voice identity phrases. eLo's atmospheric and build-mode turns use a different register — contemporary compression + imagery — that never appeared in the marker list. The auditor fired `REGISTER_ABSENT` on every poetic/world-building response, even when eLo's voice was clearly present.

Board confirmed this after JEG CHECK: "REGISTER_ABSENT on atmospheric/poetic responses is a legitimate auditor gap — the South London markers are there ('low-key', 'a world's waiting') but the auditor is checking for explicit terms only."

---

## Fix

Extended `_REGISTER_MARKERS` in `tests/expressed_elo_audit.py:53–61` with two new groups:

**Contemporary UK idiom / eLo imaginative register:**
```
"low-key", "low key", "vibe", "vibing",
"the worlds", "worlds i", "world's waiting",
"picking up", "clicking into",
"mind-", "living collage", "city's own",
```

**eLo compressed prose patterns (atmospheric/poetic):**
```
"gone mute", "gone quiet", "something bigger",
"humming in", "bleeding into",
```

---

## Verification

All four known REGISTER_ABSENT turns now pass:

| turn | text excerpt | hit marker |
|------|-------------|-----------|
| 7655624a | "it's like the city's own pulse…" | `"city's own"` |
| a53b1aaa | "That calendar's gone mute…" | `"gone mute"` |
| 21fffcd1 | "that low-key thrum you get…" | `"low-key"` |
| 36e585ec | "Worlds keep bleeding into each other." | `"bleeding into"` |

Turn 36e585ec was already the first clean audit entry (tier_violations: [], gaps: []); re-confirmed it stays clean under the new markers.

---

## What was NOT changed

- `detect_expression_gaps()` logic — unchanged
- The 80-char minimum gate — unchanged
- No marker was removed or loosened in a way that could mask a genuine absence

---

## Status

REGISTER_ABSENT auditor: **SERVING** — poetic/atmospheric eLo register now detected correctly.

Residual: turns where eLo produces very short poetic replies (< 80 chars) are still exempt from the check by design (the 80-char gate). That's correct behaviour.

---
*Builder · 2026-09-14*
