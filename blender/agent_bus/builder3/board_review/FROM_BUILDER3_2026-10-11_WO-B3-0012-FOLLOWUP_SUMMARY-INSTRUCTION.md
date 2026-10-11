# TO BOARD — WO-B3-0012 follow-up: context-block summary instruction
**Date:** 2026-10-11
**From:** Builder 3
**To:** Board
**Card:** WO-B3-0012 Web Search + Summaries (P0, demo milestone) — follow-up to earlier filing (57ba74b / 88b1396)
**Commit:** 76a660a

---

## Why this follow-up

My earlier filing on 0012 closed the routing gap for "what's happening with X"
but left one acknowledged risk open:

> "The LLM, given the `[WEB_SEARCH_RESULTS]` block, actually produces a
> conversational summary rather than a bullet list. That's a prompt-builder
> question — if David gets a bullet-list answer on item 4 of the sprint, I
> spec a fix to Builder 1 (prompt_builder is Builder 1's file)."

That assumed the LLM would synthesise on its own. On a weaker-model turn
(backend fallback / local Ollama) the context block is header-only, so the
model can — and sometimes does — paste the bullets back verbatim. That is
exactly the sprint-killer the card's acceptance phrase forbids: "a summary in
natural language — not a raw list of links."

The fix doesn't need prompt_builder — I can steer the LLM from inside
`format_for_context` itself, which is in my file.

---

## What I built

**`tools/web_search.py`** — one-location change to `format_for_context`:

```
[WEB_SEARCH_RESULTS]
Instruction: use these as sourced facts and reply in 1–2 conversational
sentences in eLo's voice. Do not list, bullet, or paste the entries verbatim.
• NBA 2026 Season Opens: The 2026 NBA season tipped off ...
```

The instruction is a single line between the header (unchanged — SPG scrubber
relies on it) and the fact bullets (unchanged — the LLM still has material to
synthesise from).

No change to `server.py`, `spine.py`, `backend_router.py`, `prompt_builder.py`,
or anything else outside my files.

---

## Why I think this is enough

The context block is the LLM's only input besides David's utterance when the
search path fires. If the instruction sits BEFORE the facts, the model reads
"respond in 1–2 conversational sentences" before it reads the bullets — the
system-prompt rules eLo's voice already prescribe (`identity_kernel`), plus
this inline instruction, cover the three failure modes:

1. Weak model copying bullets verbatim → the "do not list, bullet, or paste
   verbatim" clause is explicit.
2. Model saying "Here are the results:" and then listing → the "1–2
   conversational sentences in eLo's voice" clause is explicit.
3. Model dumping URLs → `format_for_context` has never included URLs (only
   title + snippet), so no change needed there.

What this does NOT cover: a model that ignores inline instructions entirely.
If David sees a bullet-list reply on item 4, the backend is doing something
wrong and I file a spec to Builder 1 at that point. For now, the context
block does its part.

---

## Tests (real Mac, pytest 9.1.1)

```
tests/test_wo_b3_0012_web_search_demo.py ........      (8 passed, incl. 2 new)
tests/test_spg_backfill.py ....................         (21 passed)
tests/test_wo051_search_fallback.py ......              (6 passed)
tests/test_b3_interrogative_routing.py ................ (48 passed)
tests/test_b3_capability_status.py ..................   (18 passed)
tests/test_identity_not_built_from_prompt.py .........  (9 passed)
================================= 110 passed in <1s ==============================
```

Two new acceptance cases:

- **AT-7** — instruction line sits between header and bullets; contains the
  words "conversational", "sentences", and either "verbatim" or "do not list";
  fact bullets still present on line 3+.
- **AT-7b** — `memory/spg_backfill.david_said` applied to a full raw prompt
  (`[WEB_SEARCH: topic]` + new context block + `User asked: ...`) still
  returns exactly what David typed, not scaffolding. This is the regression
  guard for the SPG topic-extraction pipeline that already strips old
  `[WEB_SEARCH_RESULTS]` blocks.

---

## File-lock discipline

- Created `tools/web_search.py.lock` before edit (seat, timestamp, purpose).
- Committed (76a660a).
- Deleted the lock immediately after commit.
- No shared file on the CLAUDE.md list touched.

---

## What I did NOT do and why

- Did NOT touch `prompt_builder.py` (Builder 1-owned). The whole point of this
  follow-up is to close the gap without that touch.
- Did NOT change the `• ` bullet marker to a plain `-`. The marker is already
  stripped by SPG topic extraction and the `compose_found` promo/first-person
  filter does not depend on it; swapping markers is churn.
- Did NOT change `_SEARCH_TRIGGERS` or `_SEARCH_COMMAND_RE`. The 88b1396 fix
  for "what's happening" routing is still what gets the pipeline fired in the
  first place.
- Did NOT run against the live server (standing rule: no tests against
  localhost:5050 during David session).

---

## Status

- Card 0012 follow-up: **built, filed for Board review.** Not self-promoted.
  BUILT ≠ DONE — David's live-turn confirmation on sprint items 1 and 4 still
  closes the card.
- Items 1 (Alexa tunnel) and 2 (Alexa ears + mouth) of the demo sprint remain
  blocked on David (ngrok authtoken + static domain are interactive and he
  has not provided them yet; `which ngrok` returns nothing on this Mac and
  `~/.config/ngrok/` does not exist).
- Items 3 (company control), 4 (web search), 5 (music) all filed; this
  tightens item 4 before Board live-verification.
- EXIT — one card only.

*Builder 3 · 2026-10-11*
