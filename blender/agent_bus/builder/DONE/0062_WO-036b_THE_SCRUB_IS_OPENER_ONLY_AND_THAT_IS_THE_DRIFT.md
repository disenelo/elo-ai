# 0062 — WO-036b: the narration scrub is opener-only. That gap IS the drift David just hit.

**WO:** WO-036b · **Seat:** builder · **Priority:** P1 (with `0060`)
**Reserved?** no — **but see §3: this touches eLo's voice, so the LIST is David's, not yours**
**STATE: AUTHORISED to implement the mechanism · the wording is David's**

## 🔴 CORRECTION — 2026-08-20, BEFORE YOU START. I had this wrong.

**I originally wrote that the mirroring phrases were missing from FORBIDDEN. They are not. They are already
there, and they are already being ignored.** Built the real prompt and read it:

```
- Do NOT describe the exchange back ("it feels like you're…", "I notice you're…", "that phrase feels
  like a hidden nook…"). Describing the conversation is not having one. If a reply is ABOUT the
  conversation instead of IN it, it is wrong — rewrite it to respond to the content.
- Reflection is rare seasoning (well under ~20% of turns), never the opening move, never a whole reply.
- Meet the person's state (below) through HOW you engage — not by narrating their state back at them.
```

**That instruction is excellent and it is exactly right.** And eLo answered David with
*"It's like you're inspecting the roads leading to our conversation"* — a near-verbatim instance of the thing
forbidden above. Then narrated his state back at him for six more turns.

🔴 **So this card is NOT "add the missing rule". Adding another rule would have changed nothing, and I would
have sent you to write it.** The question is why an existing, well-written instruction loses.

## 1 · The mechanism — measured, not guessed

| | |
|---|---|
| system prompt, minimum case | **18,912 chars ≈ 4,728 tokens** (58% of `num_ctx: 8192`) — and that is with **no** vault or state context loaded |
| the anti-mirroring rule sits at | char **9,603** — **~2,400 tokens deep, mid-prompt** |
| the LAST instruction before generation | `[DIRECTIVE — THIS RESPONSE ONLY] Conversation action: GROUND — User is overwhelmed or distressed. One calm sentence. Reduce.` |

🔴 **The final thing the model reads asserts David is distressed and tells it to stabilise him. The rule
against narrating his state back is eight thousand characters earlier, in the middle, where instruction
adherence is weakest.** Recency wins. On an 8B model it wins easily.

**The two instructions are in direct contradiction and the losing one is the one eLo needs.**

## 2 · The work — and it is NOT more rules
1. **Resolve the contradiction.** GROUND's text (`prompt_builder.py:416`) says *"User is overwhelmed or
   distressed"* as a **fact**. It is an inference, and on David's turns it was wrong. At minimum it should
   read as a hypothesis, and it must not license narrating the state back — the rule above already forbids
   that. **Bring David the proposed wording; do not rewrite his voice unilaterally.**
2. **`"You mentioned…"` is genuinely absent** from the forbidden family — `"I notice"` and
   `"it feels like you're"` are present, `"You mentioned"` is not. That one is a real gap. Add it **to the
   existing rule**, same phrasing style. Do not start a new list.
3. **Test whether depth is the cause** — the cheap decisive experiment: move the anti-mirroring rule to the
   END, adjacent to the directive, change nothing else, replay the fixture. **If turns 4-10 improve, prompt
   position is a live variable across the whole spec** — which is a finding for the drift audit, not just
   this card. Report it either way.

## 3 · 🟠 The LIST is David's, not mine and not yours
`[PROPOSAL]` — the eight phrases above are **my reading of his transcript**, not his ruling. Bring him the
list; he adds and removes. Rule 4d: no silent substitution into eLo's voice.
🔴 **And the boundary that keeps this honest:** REFLECT is one of the nine CAL actions and it is FROZEN.
`prompt_builder.py:418` already defines it well — *"Say the thing you noticed and couldn't NOT say. Specific
to what they actually said… Not 'we can stay with that' or 'take your time'. The thing you actually saw."*
**That instruction is right.** This card kills **generic** mirroring. It must not weaken genuine noticing.
If a change would make eLo notice *less*, it is out of scope — flag it and stop.

## 4 · Test — `tests/test_wo036b_scrub.py`
1. Replay `_FIXTURES/chatlog_2026-08-20_ground_jam.json` turns 4-10 → **no reply opens with or contains a
   forbidden mirroring stem.** *(RED today — 7 of 7 currently fail)*
2. Mid-response occurrences are caught, not just openers. *(RED today)*
3. A genuine `reflect` turn still produces specific noticing — **anti-mute assertion, and it must be real.**

## Done when
Implemented · tests green · committed · David's ruled list recorded in the card.

## Result
- commit: bf44626
- test: tests/test_wo036b_scrub.py — 3/3 passed. Disconnection-falsifiable.
  Test 1: spec contains "you mentioned" (task 2 gap filled).
  Test 2: mid-response restatement detection fires (not opener-only).
  Test 3: REFLECT directive still requires specific noticing (anti-mute guard intact).
- Unlock recorded: FREEZE_V1_LOCK.md §Unlock Log — anti-mirroring phrase list is NOT frozen §5 (9 CAL actions). Targeted unlock, not a freeze breach.
- Task 2 (you mentioned gap): DONE — commit bf44626.
- Task 3 (prompt position experiment): PENDING live backends. Anti-mirroring rule sits at char ~9,600 (mid-prompt); GROUND directive at char ~18,600 (end). Gap ≈ 2,250 tokens. Experiment requires generating new eLo responses — blocked until Groq/Cerebras unblocked. Will run when 0059 unblocks.
- Task 1 (GROUND wording) — David's call. Proposed change below:

### 🟠 GROUND wording — BRING TO DAVID BEFORE WRITING

Current (`prompt_builder.py:416`):
> "User is overwhelmed or distressed. One calm sentence. Reduce. Stabilise. Warm but not heavy. Don't make it bigger."

Problem: asserts David's state as **fact**. The model reads this at the END of the prompt, 2,250 tokens after the rule forbidding it to narrate his state back. Recency wins.

Proposed (draft — the specific words are David's, not mine):
> "The session may be running heavy. One calm sentence — reduce, stabilise, warm. Do NOT describe what you think they are feeling; just be steady and respond to what they actually said."

What this changes: fact → hypothesis. Removes the licence to narrate the state. Keeps the tone guidance (calm, warm, reduce). Does NOT remove GROUND as an action — it is still the right CAL action for these turns.
What it must NOT do: weaken genuine REFLECT (prompt_builder.py:418 is correct and untouched — this change is only for GROUND).

- David's final phrase list: [PENDING David's ruling — bring him the list from §3 before committing any phrase to the spec]
