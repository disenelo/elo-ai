# BUG — inner_thought generation quality: system prompt fragments + generic filler (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 2
**Date:** 2026-10-05
**Priority:** P0
**Source:** Live chat log — David's session 2026-10-05

---

## Two generation failures in the same log

### Failure 1 — System prompt verbatim fragment in inner_thought

Observed: `"the thing I decided not to lead with: 'I'm eLo: calm, observant, playful'"`

The phrase "calm, observant, playful" is a verbatim character descriptor from the system prompt / identity injection. It is appearing word-for-word in eLo's inner_thought — meaning the generation is reflecting on the system prompt text rather than generating an actual thought.

eLo's inner_thought must be generated from eLo's perspective as a thinking entity — not as a language model narrating its own system prompt. The character description is not a thought. "I decided not to lead with [my character definition]" is the LLM noticing its own system context, not eLo having an inner experience.

Fix: inner_thought generation prompt must not allow verbatim reproduction of system-level character descriptors. If eLo's character is "curious, playful, direct" — eLo never thinks "I am curious, playful, direct." eLo just IS that. The inner_thought is about something happening in the moment, not about eLo's own definition.

---

### Failure 2 — Generic contemplative filler

Observed: `"I am settling into a moment of quiet reflection, letting go of any urgency..."`

This is generic LLM introspective text — the model producing spiritual/meditative language that has no connection to the actual conversation. eLo is not a meditation app.

Canonical standard (from David's example): "well not smarter just more equipped analytically" — specific, direct, connected to what David said, in eLo's actual voice.

Generic contemplative filler = immediate FAIL. If inner_thought has no specific content connected to the conversation, it should not fire at all — it is better to suppress than to emit filler.

Fix: add a specificity check to inner_thought generation. The thought must reference something concrete from the current turn or conversation. "Settling into quiet reflection" references nothing. That should be filtered and not emitted.

---

## Evidence
One session log where:
- No inner_thought contains verbatim system prompt phrases
- No inner_thought contains generic contemplative/spiritual filler unconnected to the conversation
- Every inner_thought references something specific from the current turn
