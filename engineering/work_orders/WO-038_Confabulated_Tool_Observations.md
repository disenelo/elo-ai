---
id: WO-038
title: "Desktop-context tool gives INCONSISTENT readings across turns (not fabrication — the reads were real)."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P2
review_required: David feels it read consistently
status: OPEN — CORRECTED per David 2026-08-03 (downgraded from P0; original 'confabulation' diagnosis was WRONG)
---

# WO-038 — desktop-context tool consistency (NOT confabulation)

## CORRECTION (David 2026-08-03) — Architect got this wrong
- Original WO called these FABRICATIONS. WRONG. **David WAS listening to ScHoolboy Q's
  "By Any Means" at the time** — eLo read the playing media CORRECTLY. That's real, accurate
  perception, not invention. Architect apologises for mislabelling real awareness as a hallucination.
- The "Quantum Gardening" page was likewise almost certainly a REAL item from browser history.

## The ACTUAL (much smaller) bug
- Inconsistency across turns: eLo said the tab title mentioned "Quantum Gardening", then a later
  turn said "Chrome isn't open or no tabs found", then surfaced it again as a real recent-history
  page. Same underlying data, three different framings.
- So the fix is tool-reliability / messaging: the desktop-context reader should be CONSISTENT about
  what it can see (live tab vs history vs media), not flip between "here it is" and "nothing found".

## Fix (Builder's lane — eLo OS) — MINIMAL
- Distinguish + label the source cleanly: live active tab vs recent history vs now-playing media.
  Don't report a history item as a live tab; don't say "no tabs" when it's actually reading history.
- Do NOT suppress the real reads — the media/context awareness is a FEATURE and worked. Only make
  the framing consistent.

## Acceptance
1. eLo's account of what it can see stays consistent within a conversation.
2. Real now-playing / history reads still surface (keep the working awareness).
