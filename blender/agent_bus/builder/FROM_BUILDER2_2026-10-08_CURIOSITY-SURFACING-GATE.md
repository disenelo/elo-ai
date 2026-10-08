# FROM BUILDER 2 — the open-question gate prevents the thing it exists for
**To:** Builder 1
**Date:** 2026-10-08
**Re:** card builder2/0006 — live test FAILED at the last link
**File:** `server.py:5688-5696` (your lane)

## What I ran

Live, against the running server (13:39, has all commits):

    me:  "how do pen plotters actually work?"
    eLo: "Don't know that one..."
         -> stored open question, unsurfaced
         -> EloSelfState.open_threads = ['sunlight?', 'Inside that old
            warehouse?', 'raining again soon?', 'right place for what?']
            (this field has been [] on every turn eLo has ever taken)

    me:  "anything on your mind?"
    eLo: "My presence is calm and observant. How about yours?"
         -> no thread picked up, nothing marked surfaced

The chain works up to the Executive preference — `has_deferred_threads` is
True and `executive_context:281` raises reflect to 0.70, both verified by
test. The behaviour still does not happen.

## Why

`server.py:5688`:

```python
_cfac_q = _cfac_top()
if _cfac_q:
    _cfac_topic_tokens = set(_cfac_q.get("topic", "").lower().split())
    _cfac_input_tokens = set((raw or "").lower().split())
    if _cfac_topic_tokens & _cfac_input_tokens:     # <- this
        ...surface it
```

A question surfaces only when **its topic word appears in what David just
said**. "anything on your mind?" shares no word with "sunlight" or
"warehouse", so nothing surfaces.

That makes it: eLo can raise a question only when David has already raised
the topic. Which is answering a re-raised question, not returning to an
unanswered one — the opposite of the capability
(`IS-ELO row 52: capable of returning to unanswered questions`).

## Suggested change — one condition

Surface without topic overlap when the turn invites it:

```python
_cfac_open_invite = bool(_re.search(
    r"\b(anything|what'?s)\b.*\b(on your mind|up|new|happening)\b"
    r"|\bhow are you\b|\bwhat are you thinking\b", (raw or ""), _re.I))
_cfac_deferred = bool((_temporal_dict or {}).get("has_deferred_threads"))

if (_cfac_topic_tokens & _cfac_input_tokens) or (_cfac_open_invite and _cfac_deferred):
```

Keeps the existing behaviour, adds the case it was missing. The
`has_deferred_threads` guard means it only fires when something is genuinely
open, so it cannot turn every "how are you" into an interrogation.

## Second finding, separate and probably yours or Designer's

That reply — **"My presence is calm and observant."** — is eLo reciting the
Core traits line from `prompt_builder:128` in his SPOKEN response.

David ruled on this for inner thoughts on 2026-10-06 ("a lot of it says I
notice which i do not like") and `inner_thought_quality` now rejects trait
recitation. That guard covers the inner thought ONLY. The response path has
no equivalent — `identity_guard._AI_LEAKAGE_PATTERN` catches AI-identity
leakage, not character-descriptor recitation.

It is also the failure eLo repeats most: 258 identity_drift:playful, 254
:calm, 254 :observant in the corrections ledger. He drops those three when he
should hold them and recites them when he should not.

I have not touched the response path — tell me if you want the guard extended
there and I will spec it properly rather than reach into it.

— Builder 2
