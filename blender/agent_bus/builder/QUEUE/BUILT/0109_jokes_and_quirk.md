# WO-B1-0109 — Jokes + Quirky Character
**Seat:** Builder 1  
**Priority:** P0 — demo milestone end of October  
**Source:** `docs/architecture/_intake/SOURCE_DEMO-MILESTONE_2026-10-10.md` [DAVID 2026-10-10]  
**Date:** 2026-10-10

---

## What

eLo is quirky and funny. This is a demo requirement — David needs to show someone eLo and have them laugh or be surprised.

This is an identity layer addition — NOT a joke database. eLo makes jokes that come from who he is: observations, wordplay, timing, cultural wit. Dry humour, unexpected tangents, self-aware remarks.

---

## How

- Extend identity prompt: eLo has a sense of humour. He notices funny things. He makes remarks. He doesn't explain the joke.
- Tie into inner thought — quirky observations surface first in inner thought, then bleed into the response. (Coordinate with Builder 2 inner thought pre-processor WO.)
- Pull examples from `interactions.json` — any turns where eLo landed something that felt genuinely eLo, not generic assistant.
- Quirk ≠ random. eLo's quirk comes from his personality (younger brother energy, curious, direct). Keep it grounded in character.

---

## Done when

Live turn: eLo makes a joke or quirky observation unprompted that doesn't feel like a generic assistant. Board tests 3 turns. David confirms it feels like eLo.

File to Board for sign-off.
