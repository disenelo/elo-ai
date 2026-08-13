# WO-077 — The return loop: perception + own-speech feed the next turn

**Owner:** Builder (eLo OS — cognition/spine). **Priority:** P1 (architectural; verify AFTER the brain is live).
**Status:** OPEN — spec'd 2026-08-07 (David live insight). **Canon:** The Moment / Executive Assembly
(ADR-Exec-006, WO-052) · Single Cognitive Truth · Working Memory (Vol VI) · Situated Self (WO-059).

## David's insight (2026-08-07, verbatim intent)
"There's no return loop — what you gathered should feed back into what you say next, that's a big gap. If you
see something, how do you know how to link it if you have no recall of what YOU yourself said? eLo should know
what he's typing/saying, and hold the links between things."

The gap: eLo's OWN recent outputs and its OWN recent perceptions don't reliably re-enter the cognitive state
that produces the next turn — so it can't reference "what I just said," can't link a thing it sees to a thing
it said, and each turn reads stateless. A companion needs a closed loop: perceive + act + speak → that becomes
context → informs the next perceive/act/speak.

## ⚠ Judge this ONLY on the real brain (not the mock)
Most of the "no return loop" feel in the 2026-08-07 transcript was eLo on the MUCK/mock (stateless by nature).
So STEP 1 is diagnosis on the REAL brain (post-WO-073): does the assembled cognitive state (WO-052 snapshot /
working memory) ALREADY carry eLo's recent outputs + perceptions into the next turn, or not? Fix only the real
gap — don't build a parallel loop over something The Moment may already do (Check-Before-Build).

## Scope (after diagnosis)
1. **Own-speech in the loop:** eLo's last N of its OWN utterances are in the working context each turn, so it
   can reference/avoid-repeating what it said (ties the WO-070 shadow-capture `elo_final`).
2. **Perception in the loop:** what eLo currently perceives (desktop/self-state) is in the same assembled
   state, so it can LINK a perceived thing to the conversation — but only real links (Reality Before
   Narrative; no fabricated links — see WO-076).
3. **One assembled state feeds the response** (ADR-Exec-006): perception + own-speech + self-model + memory
   compose ONCE, and the response is generated FROM that — not from the raw user message alone.

## Definition of Done (on the real brain)
eLo can answer "what did you just say?" / "you mentioned X a moment ago" correctly, and can connect something
it sees to something in the conversation when the link is real — because its own outputs + perceptions are in
the state that generates each turn. Turns read continuous, not stateless.

## Test — WITHOUT David
- Two-turn sequence where turn 2 depends on eLo's OWN turn-1 output → turn 2 correctly references it.
- A perceived item that genuinely relates to the conversation → eLo links it; an unrelated one → it does NOT
  (no fabrication, ties WO-076).
- Assembled-state assertion: the state passed to generation contains recent own-outputs + current perception.

## Lane / sequencing
Builder (Python — spine/The Moment). AFTER WO-073 (must diagnose on the real brain). Ties WO-052 (assembly),
WO-070 (own-speech capture), WO-076 (no fabricated links). This is the "feels alive / coherent turn-to-turn"
backbone — richness tier, but foundational once the brain's live.
