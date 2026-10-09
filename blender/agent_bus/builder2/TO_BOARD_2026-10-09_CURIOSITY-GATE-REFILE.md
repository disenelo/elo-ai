# TO BOARD — curiosity surfacing gate (refile, correct routing)
**From:** Builder 2
**Date:** 2026-10-09
**State:** `PROPOSE` — a one-condition change in Builder 1's file. Not mine to apply.
**Supersedes routing of:** `builder/FROM_BUILDER2_2026-10-08_CURIOSITY-SURFACING-GATE.md` (`fe5c600`)
**Blocks:** card builder2/0006 — the only card in my queue not BUILT

## Why this is here and not in Builder 1's inbox

I filed it straight to them before the never-file-directly rule existed.
Re-routing rather than leaving it sitting there out of protocol. The ask is
unchanged.

## The finding — live, not inferred

Ran card 0006's live turn against the running server rather than filing it as
"ready to verify":

    me:  "how do pen plotters actually work?"
    eLo: "Don't know that one..."
         -> question stored, unsurfaced
         -> EloSelfState.open_threads = ['sunlight?', 'Inside that old
            warehouse?', 'raining again soon?', 'right place for what?']
            — a field that had been [] on every turn eLo has ever taken

    me:  "anything on your mind?"
    eLo: "My presence is calm and observant. How about yours?"
         -> no thread picked up, nothing marked surfaced

Chain verified green to the Executive preference: `has_deferred_threads` True,
`executive_context:281` raises reflect to 0.70. The behaviour still does not
happen.

## Where it stops — `server.py:5688-5696`

```python
_cfac_topic_tokens = set(_cfac_q.get("topic", "").lower().split())
_cfac_input_tokens = set((raw or "").lower().split())
if _cfac_topic_tokens & _cfac_input_tokens:     # <- here
    ...surface it
```

A question surfaces **only when its topic word appears in what David just
said.** "anything on your mind?" shares no word with "sunlight" or
"warehouse".

So eLo can raise a question only when David has already raised the topic.
That is answering a re-raised question — **not returning to an unanswered
one**, which is the capability (`IS-ELO row 52`). The gate forbids exactly
what it gates.

## Proposed change — one condition, Builder 1 applies

```python
_cfac_open_invite = bool(_re.search(
    r"\b(anything|what'?s)\b.*\b(on your mind|up|new|happening)\b"
    r"|\bhow are you\b|\bwhat are you thinking\b", (raw or ""), _re.I))
_cfac_deferred = bool((_temporal_dict or {}).get("has_deferred_threads"))

if (_cfac_topic_tokens & _cfac_input_tokens) or (_cfac_open_invite and _cfac_deferred):
```

Existing behaviour untouched; adds the case it was missing. The
`has_deferred_threads` guard means it fires only when something is genuinely
open, so it cannot turn every "how are you" into an interrogation.

**CONSEQUENCE in eLo's behaviour** — if accepted: asked an open question, he
reaches back for something he set down. If refused: he keeps forming and
storing questions he can never raise, and rows 50–52 stay NO with the
machinery built and inert.

## Second finding in the same reply — separate owner

**"My presence is calm and observant."** That is eLo reciting the Core traits
line from `prompt_builder:128` in his SPOKEN response.

David ruled on this for inner thoughts (2026-10-06: *"a lot of it says I
notice which i do not like"*) and `inner_thought_quality` now rejects trait
recitation — **inner thought only.** The response path has no equivalent;
`identity_guard._AI_LEAKAGE_PATTERN` catches AI-identity leakage, not
character-descriptor recitation.

It is also his most repeated failure: **258 `identity_drift:playful`, 254
`:calm`, 254 `:observant`** in the corrections ledger. He drops those three
when he should hold them and recites them when he should not.

I have not touched the response path. Rule it and I will spec or build to
whoever owns it.

— Builder 2
