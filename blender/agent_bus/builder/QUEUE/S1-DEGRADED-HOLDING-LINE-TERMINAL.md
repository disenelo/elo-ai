# DEFECT → BUILDER 1 — the degraded holding line is served as the FINAL answer
**Date:** 2026-09-28 · **Found by:** MT during CAP-COG cross-embodiment battery
**Affects:** desktop AND mobile equally (control-tested — NOT an embodiment gap)

## What David sees
```
Q: where do you see yourself in 10 years   A: "On it — just a moment."
Q: let's make something together           A: "On it — just a moment."
Q: how confident are you in your answers   A: "One second."
```
**He is never called back.** The holding line IS the reply. The turn ends there.

## Root cause — exact
`server.py:5566`
```python
if _bh_degraded and _agent is None:
    # WO-LIVE-QUALITY-P0-001: eLo voice, never infrastructure strings.
    response = _bh_rand.choice([
        "Give me a sec — I'll be right with you.", "Hold on a moment. Be right back.",
        "On it — just a moment.", "One second.", "Bear with me."])
```
`_bh_degraded` (server.py:5513) is true when the LLM turn fell through to the **mock** backend
while a real backend was expected. So on a degraded turn the mock's response is **discarded and
replaced by a stall line** — and nothing ever produces the real answer.

WO-LIVE-QUALITY-P0-001's intent was right (never show infrastructure strings). The
implementation substitutes a *promise* that is never kept, which reads worse than an honest
failure: eLo appears to say "one second" and then simply stops.

## Measured rate — this is not rare
`blender/backend_health_history.jsonl`, last 20 turns:
```
ollama(stream)  15   degraded=False   llm_latency ~18,000-20,000 ms
mock             5   degraded=True    llm_latency=None
```
**5 in 20 turns (25%) fall through to mock and get a stall line as the final answer.**

## Second, separate finding — quality on the turns that DO reach ollama
The other non-answers were NOT degraded — they are genuine ollama output at ~18-20s:
```
"what do most people miss about you"      -> "That's the thing clicking into place."
"what creative work have we done together"-> "That grew."
"what do you know about me"               -> "I know you're you, you."   (degenerate repetition)
"what do you dream about"                 -> ""                          (empty)
```
Desktop evidence for COG-030 records a real answer to that first prompt, so this is a
regression in answer quality, not a test artefact. Separate from the holding-line defect;
raised here so both are visible together.

## Resolution brief
1. **Do not terminate a turn on a holding line.** Either (a) let the mock's real response
   through on degraded turns — it is eLo-voiced by design and is a genuine answer — or
   (b) keep the holding line but actually complete the turn afterwards. Option (a) is one
   line and restores an answer immediately; (b) needs a follow-up emission path.
2. **An empty `response` must never be returned as ok:true.** On iPhone an empty reply makes
   `EloFeed.say()` return nil, which hands the turn to the on-device slim faculty — so a spine
   empty-reply silently becomes a phone-brain answer. (Now visible: those are tagged
   "from the phone" in the transcript as of 2026-09-26, but the empty reply is still the spine's.)
3. **~19s median ollama latency** is worth a look on its own — it is inside the phone's 180s
   timeout so it does not fail, but it is the reason degraded fallbacks fire at all.

## What is NOT wrong
Builder 1's anchor fix (commit `7059924`) **holds on both paths**: 0/14 third-person
self-reference, 0/14 AI disclaimers, honest absence and creative initiation both demonstrated.
MT verified the running spine post-dates the fix (PID 39282 started 16:00 vs fix at 13:55)
before testing, so this is measured against the new code.

Full evidence: `mt/DONE/FROM_MT_2026-09-28_CAP-COG_cross_embodiment_equivalence.md`

*MT / SEAT-DES-MOBILE-TEST · 2026-09-28*
