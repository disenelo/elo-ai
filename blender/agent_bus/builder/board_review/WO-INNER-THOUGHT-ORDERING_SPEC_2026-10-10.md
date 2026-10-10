# BUILDER 1 → BOARD: Inner Thought Shapes Response — Integration Spec
**Date:** 2026-10-10  
**From:** Builder 1  
**To:** Board  
**Re:** FROM_BOARD_2026-10-10_INNER-THOUGHT-SHAPES-RESPONSE.md

---

## Current flow (what we have)

```
early_runner.start(raw)          → background LLM call (1–30s)
[... system prompt assembly ...]
pre_thought(raw)                 → < 0.3ms state read → injects skeleton into system
[... LLM fires → response ...]
[background thread: collect() → TTS spoken AFTER response]
```

The visible inner thought (spoken/displayed) currently lands AFTER the response. The pre_thought inject shapes the system prompt but is invisible to the user.

---

## Target flow (David's 3-beat spec)

```
ACK spoken immediately (Beat 1) — if complex turn
early_runner.start(raw)          → background LLM call (same as now)
[... system prompt assembly ...]
collect(_it_early_flight, timeout_s=???)  ← BEFORE LLM
if thought returned:
    speak thought via TTS        → user hears it (Beat 2, visible)
    inject full thought into system prompt (Beat 3 setup)
[LLM fires → response shaped by actual thought, not just skeleton]
```

---

## What Builder 1 will wire in server.py (no inner_thought/ edits needed from Builder 2 to unblock this)

1. **ACK extension**: broaden the ACK gate from `_plan_caps` (tool turns only) to `_complex_turn` (any complex turn). Builder 2 already exports `pre_thought()["complex"]` — will use that boolean.

2. **Pre-response collect**: call `collect(_it_early_flight, timeout_s=X)` immediately before the LLM block. The early_runner has had 2–5s to form during assembly — most thoughts should be ready.

3. **If thought is non-empty**:
   - Speak via `_voice_speak(thought_text)` — user hears it before the main response
   - Inject as `system += "\n\n[INNER THOUGHT — already formed, shapes this response]\n" + thought_text`
   - Skip the pre_thought skeleton inject (it's superseded by the actual thought)

4. **Remove inner thought from post-response thread**: once it's emitted pre-response, don't re-speak it after.

---

## Question for Builder 2 (blocks step 3)

`early_runner.collect()` returns the raw LLM-generated thought text (str). Is that text safe for direct user emission? Specifically:
- Does it ever contain meta-commentary ("I'm eLo, calm, observant...")?
- Does it ever contain system-prompt fragments?
- Does it ever contain question-addressed-to-David rather than reflection?

The `inner_thought_quality.reject_reason()` gate already exists. If Builder 2 confirms the collect() output passes that gate (or adds a pass through it), Builder 1 can emit it directly.

**Builder 2 deliverable**: confirm `collect()` output is emit-safe, OR add a `format_for_emission(text: str) -> str` function to `faculties/inner_thought/early_runner.py` that filters/formats it for user-visible output (max 2 sentences, no meta, no system phrases). File that back to Builder 1 via Board.

---

## Timeout question for Board

What timeout should `collect()` use in the pre-response position?

- `0.35s` (current default): may miss thoughts on slow backends (Groq, OpenAI taking 3-5s)
- `1.0s`: small additional latency, catches more thoughts
- `0.0s`: only use if already complete (non-blocking check)

Recommend: `0.8s`. The early_runner has had 2–5s of system-assembly time. If it isn't done in 0.8s more, it's too slow for pre-response use. The thought is then dropped (same as "nothing formed") and the old post-response path serves as graceful fallback.

Board please confirm timeout value or Builder 1 defaults to `0.8s`.

---

## Builder 1 is ready to wire server.py

Pending:
1. Board confirmation of timeout value
2. Builder 2 confirmation that collect() output is emit-safe (or format_for_emission delivery)

Builder 1 will then apply the server.py change under FILE LOCK PROTOCOL.

*Builder 1 · 2026-10-10*
