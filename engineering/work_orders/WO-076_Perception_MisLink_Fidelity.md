# WO-076 — Screen-perception fidelity: no fragments, no fabricated links (F7)

**Owner:** Builder (eLo OS — perception/desktop-context). **Priority:** P2 — POST-L3 (not a finish-line-6
blocker; a fidelity/honesty issue). **Status:** OPEN — spec'd 2026-08-07 (F7, flagged in live transcript #2).
**Canon:** Reality Before Narrative (never assert a relationship that isn't real) · Embodied Truth.

## Problem (live transcript #2, 2026-08-07)
eLo's screen perception (a) reads **fragments** — "I saw you checked the 'Limited Use: Seems…" (truncated,
no real content), and (b) **fabricates a link** — "the Grok page is linked right into the eLo Robot Tracker
you've been checking." David: "a lot of things are linked but not how you're seeing it." So eLo is
mis-associating separate things it sees on screen and surfacing half-read fragments as if they mean something.

## Fresh evidence (David live 2026-08-08)
eLo said "kickstarter disenelo — Google Search — it's touching **eLo FaceAnim Tracker**" and "…touching **eLo
Robot Tracker**" — asserting relationships between unrelated screen items. Same fault: confident fabricated
links from perception. (Behavioural over-proposing that surfaced these = WO-085.)

## Scope
1. **No fragment-as-fact:** if the perceived text is truncated/partial, eLo either reads it fully or says it
   only caught a fragment — it does NOT present a partial string as a confident observation.
2. **No fabricated relationships:** eLo must NOT assert that two things it sees are "linked"/related unless
   there's a real, verifiable relationship in the data. Separate tabs/pages are separate unless the source
   says otherwise. (This is the perception-side of ADR-Exec-001 — don't narrate an inferred link as fact.)
3. Ties the desktop-context layer (WO-038 chrome_reader labels · `tools/vision_loop.py` · the CognitiveSnapshot
   chrome perception fields). Extend those — don't add a parallel perceiver (Check-Before-Build).

## Definition of Done
Given a known screen context, eLo reports what's actually present (full, or honestly flagged as partial) and
does NOT invent links between unrelated items. If unsure what it's seeing, it says so rather than confabulating.

## Test — WITHOUT David (`tests/test_wo076_perception_fidelity.py`)
- Feed a perception context with two UNRELATED items → eLo's summary does NOT assert they're linked.
- Feed a truncated/partial capture → eLo flags it as partial / doesn't present the fragment as a fact.
- Feed a context with a REAL relationship → eLo may state it (no false-negative).

## Lane
Builder only (Python — perception/desktop-context). Post-L3; does not gate Presentable.
