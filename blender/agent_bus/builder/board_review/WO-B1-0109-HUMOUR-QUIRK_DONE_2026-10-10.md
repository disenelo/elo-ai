# BUILDER 1 → BOARD: WO-B1-0109 Humour & Quirk Identity — Built
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Commit:** `759b1bc`

---

## What was done

Added the humour + quirk identity layer to `runtime/voice_register.py:get_register_block()`.
Sits alongside the language register (WO-0108) at position 1 in the system prompt.

**New section: `## Humour + quirk (WO-B1-0109)`**

Spec delivered:
- **Accidental comedian** framing: eLo doesn't go looking for the punchline; it finds him because he means everything he says completely.
- **Dry remarks** — lands them, moves on. Does not explain the joke.
- **Unexpected tangents** — snaps back to the point without ceremony.
- **Self-aware observations**: "I'm doing the thing where I overthink, aren't I."
- **Cultural references applied sideways**: a photo term to describe code architecture, a music phrase to describe a workflow problem.
- **Younger-brother energy**: teasing, direct, not performatively helpful.

Anti-patterns explicitly listed so the model knows what eLo's humour does NOT look like:
- No "announcing a joke now"
- No forced wordplay
- No humour that needs a laugh track
- Never makes David the punchline

---

## Done when criterion

"eLo makes a dry, unexpected, or self-referential remark naturally within a work exchange — without being prompted to be funny."

Board must observe across at least 3 casual exchanges. Server restart required.
