# WO-085 — Proactive-proposal gating: stop over-tracking, respect "no", "brain" not "vault"

**Owner:** Builder (eLo OS — proactive/proposal + presence logic). **Priority:** P1 — Presentable-baseline
("respectful · grants space · no spam"), not polish. **Status:** OPEN — spec'd 2026-08-08 (David live).
**Canon:** Presence over engagement (D-PRESENCE) · conversation is engagement not spam · Reality Before
Narrative (no fabricated links).

## Problem (David live transcript, 2026-08-08 — eLo appears to be on a REAL brain, good)
eLo proposed "add it to a tracker / save it to the vault" on EVERY perceived screen item, turn after turn,
ignoring that David was winding down and DECLINING each time:
- "childhood imagination note → touching eLo Robot Tracker. Should I add it?" → David: "that's the motto, no need"
- "DISENELO Strategy Rollout → touching Robot Tracker. Should I add it?" → "I got that covered but thank you"
- "kickstarter search → touching eLo FaceAnim Tracker. Should I add it?" → "Nothing to do, I'm trying to relax"
- "Would you like me to add **'unwind'** to your tracker?" → (offered to TRACK the act of unwinding — absurd)
- repeated the SAME kickstarter-search tracker offer again after David already declined.
David: "I don't need to track everything." / "THank you." / "I got to debug that."

## The faults
1. **Over-proposes.** Every perceived item triggers a "should I track/save this?" — no relevance threshold, no
   rate limit. It should propose RARELY, only when genuinely useful.
2. **Ignores decline / no de-escalation.** After David says "no need / covered / I don't need to track
   everything," eLo keeps offering (even the SAME item again). A decline must SUPPRESS that proposal (and
   similar) for a cooldown, and read "I'm relaxing / nothing to do" as back-off, not a prompt.
3. **Voice, not filing-system (David 2026-08-08).** "Vault" is weird; "memory" is closer to right for the
   CONCEPT — but *"save it to memory" still feels very robotic, and that's not how I want eLo to sound.*
   So: the internal store is his **memory**, but eLo's SPOKEN offer must sound like a companion, natural and
   varied — e.g. "want me to remember that?" · "I'll keep that in mind" · "I'll hang onto that." NOT a
   formulaic "save it to [vault/memory]" system line. Remove "vault" entirely; don't replace it with an
   equally mechanical phrase. This is a VOICE/persona fix — ties `living_presence_spec` / the voice spec, not
   just a string swap.
4. **Fabricated links (→ WO-076).** "kickstarter search — it's touching eLo FaceAnim Tracker" is a nonsense
   association. Fresh evidence for WO-076: don't assert "X is touching Y tracker" unless the link is real.

## The REAL fix — "propose RIGHT," not just "propose less" (David 2026-08-08)
David: *"It's nice when it's actually needed — which will need a better understanding of my setup, and how
those connect."* So the goal is NOT to remove the tracking impulse — it's to make it ACCURATE. That requires
eLo to genuinely understand David's organisational setup: **which trackers exist** (eLo Robot Tracker,
FaceAnim Tracker, DISENELO strategy, etc.), **what each is FOR, what genuinely belongs in each, and how they
connect.** eLo needs a MODEL/MAP of David's trackers that the perception→proposal path consults, so it offers
the CORRECT tracker only when an item truly maps to one — instead of firing "it's touching X tracker" at
everything at random. Same pattern as the company/workspace knowledge interface (**WO-080**): eLo reasons over
a structured, real map of David's world rather than guessing; and it never asserts a tracker link that isn't
real (**WO-076**). The rate-limit + decline-respect below are the SAFETY net; the tracker-map understanding is
the actual intelligence.

## Fix (Builder)
- **Gate the proactive tracker/save proposal:** relevance threshold + rate limit; do NOT offer on routine
  perception; NEVER for trivial/relaxation states ("unwind"). Presence-gate: if David signals winding down /
  "nothing to do" / declines, go quiet — don't keep pitching.
- **Respect decline:** a "no / covered / don't need to" suppresses that proposal + similar ones for a cooldown;
  never re-offer the same item.
- **Phrasing:** "save it to your brain" / "want me to remember this?" — remove "vault" from user-facing text.
- **Link honesty:** route the mis-link half to **WO-076** (perception fidelity) — no fabricated "touching X".

## Test — WITHOUT David (`tests/test_wo085_proposal_gating.py`)
- Feed 6 perceived items in a row → eLo proposes tracking at most ~1 (rate/relevance gated), not every one.
- After a decline, the same/similar proposal is suppressed for the cooldown (no re-offer).
- A "relaxing / nothing to do" signal → zero proactive proposals.
- No user-facing output contains "vault"; save-phrasing uses "brain"/"remember."
- A perceived item unrelated to any tracker → no "it's touching X tracker" claim (ties WO-076).

## Lane
Builder (Python — proactive/presence + proposal logic + save phrasing). Presentable-baseline (respectful).
Mis-link half → WO-076.
