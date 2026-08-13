---
id: WO-036
title: "eLo replies too long / flowery — tighten to present, concise presence."
owner_seat: SEAT-ENG-001 (Builder / eLo OS)
priority: P2
review_required: David feels it live
status: OPEN
created: 2026-08-03
---

# WO-036 — reply length discipline

## Evidence (David live, 2026-08-03)
Replies over-elaborate: "It feels like we're settling in for a conversation that's been
waiting to happen. What's been on your mind lately?" / "That's an interesting choice of
word. It feels like there's something behind it..." — length + invented subtext where a
short present reply fits. The prompt already says "keep it light" — the generation isn't honouring it.

## Fix (Builder's lane — eLo OS: prompts/ + generation)
- Enforce brevity by default: eLo answers in the fewest words that stay warm and present.
  Short prompts get short replies. No filler ("It feels like…"), no unsolicited follow-up
  questions every turn, no narrating the user's tone back at them.
- This is prompt/length tuning, not a personality change — presence stays, verbosity goes.

## Acceptance
David talks casually → replies read tight and present, not essayistic.

## ADDENDUM (2026-08-03) — the "I notice you…" mirroring
Live transcript shows near-every reply is a reflective mirror ("I notice you slipped a comma…",
"I hear you're curious…", "I see you pointing out…"). David: "you notice a lot, but also say
'I notice you' often." Part of this is the backup model's voice (WO-032), part is the REFLECT/
CONNECT prompt directives ("Say the thing you noticed"). Trim it: eLo should ANSWER first; the
"I notice…" reflex should be rare and earned, not the default frame for every turn.

## CA FIX FOLD-IN (P1) — Conversation style monitor
Chief Architect: add a style monitor that DETECTS repetitive phrasing ("I notice…", "I hear…",
"It feels…") and diversifies output. Not just a shorter prompt — an active check on the last N
replies that penalises the same opener/frame. Pairs with WO-032 (backup model drives much of the tic).
