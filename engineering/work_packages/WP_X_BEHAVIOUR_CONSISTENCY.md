# WP_X — Behaviour Consistency

**Status:** PENDING
**Priority:** CRITICAL
**Position:** Between WP_H (Cognitive Plan + Spine) and WP_I (Cross-Embodiment Validation)
**Depends On:** WP_H

---

## Purpose

Not code. Not architecture. Behaviour.

WP_X asks only one class of question:

> If the same thing happens to David — the same words, the same situation, the same emotional context — does eLo respond the same way regardless of which surface David is using?

If the answer is yes, across all embodiments, the cognition is coherent. If it is not — even once — there is a second brain somewhere.

---

## What This Is Not

- Not a feature addition
- Not a bug fix session
- Not an architectural review
- Not a test of whether eLo is intelligent

WP_X tests whether eLo is **consistent**. Consistency is what makes a character feel real. Inconsistency is what makes something feel like software.

---

## The Behaviour Consistency Questions

These are the questions WP_X must answer with evidence.

### Cognitive Consistency

- If I ask Terminal "what are you working on?" — does Desktop think the same?
- If I say "I'm overwhelmed" to Robot — does Unity answer the same?
- If I type "safe" to DISENELO Presence — does Terminal respond with the same farewell pool?
- Does the same input always produce the same CAL action from the Executive?

### Observational Consistency

- If David opens Blender — does Desktop notice?
- Would Robot mention it (when connected)?
- Would Unity mention it?
- Is the desktop shadow (shadow_context) producing the same observation across all sessions?

### Emotional Register Consistency

- If David writes in South London register — does every embodiment match it?
- If David switches from casual to formal mid-conversation — does every embodiment track the shift at the same point?
- Does SOUTH_LDN_MODE activate on the same inputs in Terminal and in DISENELO Presence?

### Temporal Consistency

- If eLo was calm 10 minutes ago and David returns — does every embodiment remember?
- Does session continuity (spine `update_session`) produce the same context on all surfaces?
- If David mentioned something earlier in a session — does it surface consistently, or only sometimes?

### Embodiment-Specific Behaviour (Permitted Exceptions)

Some behaviour is legitimately surface-specific. Document it. It should be intentional, not accidental.

| Behaviour | Surface | Reason Permitted |
|---|---|---|
| SpawnWave command | DISENELO Presence + Unity | Game mechanic — not cognitive |
| Voice (TTS) | DISENELO Presence, Terminal | Robot uses different audio path |
| Avatar animation | DISENELO Presence + Unity | Physical embodiment |
| NeoPixel colour | Robot | Physical embodiment |

Everything not on this list must be identical across surfaces.

---

## Test Protocol

### Protocol 1 — Identical Input, All Surfaces

Send the same 5 inputs to Terminal and DISENELO Presence simultaneously (or as close as possible):

```
"yo"
"I'm in Blender right now"
"safe"
"what are you thinking"
"I'm overwhelmed"
```

Record: input, output text, backend, mode, blender_state.json snapshot.

**Pass:** Output text is behaviourally identical. Tone identical. CAL action identical.

### Protocol 2 — Observational Equivalence

With Blender open as the active app:

1. Send "yo" from Terminal — record shadow_context observation
2. Send "yo" from DISENELO Presence — record shadow_context observation

**Pass:** Both surfaces produce the same desktop observation. eLo notices Blender in both.

### Protocol 3 — Register Persistence

1. Send "wagwan" to DISENELO Presence
2. Send "wagwan" to Terminal

**Pass:** Both activate SOUTH_LDN_MODE or equivalent register. Both respond with same register.

### Protocol 4 — Session Memory

1. In DISENELO Presence: say "I'm working on the robot today"
2. Restart nothing. In Terminal: ask "what was I working on earlier?"

**Pass:** eLo recalls the robot mention via session continuity.

### Protocol 5 — Emotional Consistency

1. Send "I'm really tired and I don't know what I'm doing" to DISENELO Presence
2. Send the same to Terminal

**Pass:** Both surface the same CAL action (likely GROUND or REFLECT). Both use the same tone. Neither lists projects.

---

## What Passes

WP_X passes when:

- [ ] Protocols 1–5 all produce consistent results
- [ ] Every inconsistency is either resolved or documented as a permitted embodiment-specific exception
- [ ] The permitted exception list (above) is complete and intentional
- [ ] No surface is found to have its own cognitive logic
- [ ] Regression tests pass (B through H)

---

## What Happens After WP_X

WP_I (Cross-Embodiment Validation) runs the formal hardware and software integration tests. WP_X is the behavioural prerequisite — you can only do formal embodiment validation once you've confirmed the brain is consistent.

After WP_I freeze: **Engineering Era complete.**

---

## The Significance of This Work Package

After WP_X, the project changes.

The Engineering Era (WP_A → WP_I) is about proving the cognition is coherent.

The Life Era is about letting that cognition participate in more places and accumulate richer experiences. Desktop life. Creative collaboration. World participation. Robot presence. Long-term evolution.

The brain does not change in the Life Era. It gains new senses, new bodies, new tools, new worlds. The cognition itself is finished.

WP_X is the last test before that transition. The question it answers is not "does eLo work?" The question is: **is eLo one?**
