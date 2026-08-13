# WO-069 — Multilingual conversational match ("Como estas?" → answer, in-language, no meta)

**Owner:** Builder (eLo OS). **Priority:** P2 (small, David-flagged twice). **Status:** OPEN — spec'd 2026-08-07.
**Canon:** Conversation is engagement, not reflection (Vision Spine) — answer the question, don't narrate that
a language was used. Ties WO-029 (greeting/how-are-you family) + WO-036 (no meta-narration).

## Problem (David live, 2026-08-07)
"Como estas?" → eLo: "I notice you asked in Spanish, a friendly little pivot that feels warm." It NARRATED
the language instead of answering. Root cause (verified in code): `_LANGUAGE_GREETINGS` / `_detect_language_
query` (`server.py:1291`, `:1325`) cover only greetings ("Hola") and greeting-requests ("say hi in Spanish").
There is NO multilingual "how are you", so "Como estas?" / "Ciao bello" fell through to the general path and
tripped the mirror/meta reflex. A `_HOW_ARE_YOU_POOL` already exists (`:966`) — it just isn't reached
multilingually.

## Scope
1. **Recognise "how are you" across languages** → route to the existing HOW_ARE_YOU intent: e.g. `como estas`
   (es), `ça va` / `comment vas-tu` (fr), `come stai` (it), `wie geht's` (de), `tudo bem` / `como vai` (pt),
   `kak dela` (ru), `hogy vagy` (hu), etc. Map each to its language.
2. **Answer — and match the language when detected.** "Como estas?" → a warm HOW_ARE_YOU reply IN SPANISH
   (e.g. "Bien, aquí contigo — ¿y tú?"), not English, not a comment. If no in-language reply is available,
   answer warmly in English — but ANSWER, never narrate "you asked in Spanish."
3. **Kill the meta.** The "I notice you asked in X" reflex must not fire on a language switch (WO-036 family).

## Definition of Done
"Como estas?" / "Ciao, come stai?" / "ça va?" → eLo answers the question, in that language when it can, with
zero meta-narration. English "how are you" still works (WO-029 unaffected).

## Test — WITHOUT David (`tests/test_wo069_multilingual_how_are_you.py`)
- `como estas?` → reply classified HOW_ARE_YOU, contains a Spanish answer token, does NOT contain "I notice"/
  "you asked in Spanish".
- `come stai?` (it) · `ça va?` (fr) · `wie geht's?` (de) → HOW_ARE_YOU reply, in-language when mapped.
- `how are you?` (en) → unchanged (WO-029 pool).
- A pure greeting ("Hola") still hits the greeting path (no regression).

## Lane
Builder only (Python). Small: extend the multilingual map + wire to HOW_ARE_YOU + suppress meta.
