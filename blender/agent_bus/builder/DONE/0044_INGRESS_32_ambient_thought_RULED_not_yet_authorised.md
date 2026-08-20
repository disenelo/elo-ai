# 0044 — 🔴 **INGRESS #32 FOUND: `ambient_thought()`. Ruled. NOT authorised. Do not start it.**

**Architect, 2026-08-16.** Full ruling: `Output/RULING_ambient_ingress_2026-08-16.md`.
**This card exists so you know the shape before `W5`. It adds nothing to your queue today.**

---

## What happened
David heard eLo **speak spontaneously with Presence closed**, while macOS showed the screen-recording
indicator. The trace, **verified by me against disk**:

`server.py:717–895` · `ambient_thought()` · fires on a **2–4 min daemon tick** · makes its **own** `_rt()`
LLM calls at `:758` and `:857` with a **separate minimal system prompt** · speaks via `_voice_speak()` at
`:888`.

**Absent from all 179 lines:** `spine.run` · `exec_decide` · `executive` · `decision_journal` ·
`journal_route` · `world_state` · `attention`.

🔴 **My exception list said 31 and I ratified it as complete. It is 32.** My scan window was
`1571–2404` — **the request path.** I never scanned daemon entry points. `0038` is amended.
**Card `0038` line 80 literally says the assertion "stops number 32 appearing." It already existed.**

🟢 **Bounded — I checked before alarming you:** of **21** `_voice_speak()` call sites, **20 are in
`_process_turn()`** and **exactly 1 is ambient.** One path. Not a systemic leak.

---

## ⚖️ RULED — and it needs NO new code that doesn't already exist

**`ambient_thought()` is demoted from DECIDER to PROPOSER.** Same shape as **D8** (gatekeeper proposes,
never vetoes) and **AR-24** (Unity proposes routes, brain selects). **Nothing novel.**

🔴 **Everything required already exists and is already wired — do not build any of it:**

| Piece | Where | State |
|---|---|---|
| `plan.intent_source: "david" \| "self" \| "reflex"` | `runtime/spine/plan.py:27` (WO-099b) | **exists** |
| `plan.internal_intent: dict` *(kind·source·trigger·priority)* | `runtime/spine/plan.py:29` (WO-114) | **exists** |
| `internal_intents(state, idle_seconds)` | `self/emergent_cognition.py:45` | **exists — the canonical producer** |
| Already consumed on the request path | `server.py:3078–3091` | **already wired** |
| Executive handles degenerate input | `Volume_VII/01:361` — AT for input of `"…"` | **already canon** |

🔴 **`ambient_thought()` is a DUPLICATE of `internal_intents()` that bypasses the Executive.**
**Classification G, not H.** When its WO comes: **retire the second implementation INTO the first. Never
rebuild it beside.**

### The target route
```
daemon tick → internal_intents(state, idle_seconds)
            → spine.run(intent_source="self", internal_intent=…)
            → PERCEIVE/STATE/ATTENTION/MEMORY/SIGNIFICANCE   ← ambient finally SEES what vision saw
            → EXECUTIVE decides: SPEAK | STAY SILENT
            → action + decision_journal row
```

---

## 🟢 NOTHING IS BEING REMOVED — and silence gets better
**Ambient initiation, silence, tone, emotion and voice are all preserved.** David's intent is explicit:
eLo may speak spontaneously while he works, **and may choose to sit in the silence.** That is product
behaviour, not a bug.

**Today silence is *the daemon not firing* — an absence, invisible and unexplainable.**
**Routed, `STAY SILENT` becomes a decision the Executive makes and journals.** eLo can then truthfully say
*"I noticed, and chose not to interrupt"* — backed by a row instead of being a nice line.

---

## 🔴 NOT AUTHORISED. Your queue is unchanged.
**`W1` outcome** → **`W2` session ids** → **`W5` ONEBRAIN-012** *(ambient lands with W5 — it needs the
same `ExecutiveContext` as a user turn)* → **the loop test.** `0037` before W5.

**Do not touch `ambient_thought()` yet.** Routing it before `W5` gives it an Executive that reads seven
keys off one dict — **you would move the organ and not fix the blindness.** That is the "one layer away"
error, and I have made it twice this week.

**One thing I could not verify and will not assume:** whether `spine.run()` behaves correctly with an
empty `raw` and a populated `internal_intent`. `Vol VII AT :361` specifies the Executive must handle
`"…"`, but **I have not run it.** **Exercise that path at `W5` and report what happens** — it is your
measurement, not David's.

---

## 🟢 The finding worth keeping
**PRESENCE IS NOT THE BRAIN — and we now have runtime proof.** eLo perceived, thought and spoke with Unity
closed. `Volume_XIII/05` has always said Presence is a **realisation layer**, never the reasoning core.
**An accident proved a canonical claim.** Very little in this programme has been proven by runtime rather
than asserted by document. **This was.**
