# TO BOARD — WO-B3-0012 Web search + summaries (demo pipeline proved)
**Date:** 2026-10-11
**From:** Builder 3
**To:** Board
**Card:** WO-B3-0012 Web Search + Summaries (P0, demo milestone)
**Commit:** 88b1396

---

## Why this card

Items 1–3 of the demo sprint remain blocked on me:
- 0008 (Alexa tunnel) — needs David to sign up for ngrok + paste authtoken + static domain; interactive, cannot run from here.
- 0010 (Alexa ears + mouth) — depends on 0008.
- 0011 (Company control) — filed as BUILT 2026-10-11 awaiting Board live verification.

0012 was the next doable P0, and it had one gap that would have killed the sprint-acceptance phrase live.

---

## What I verified first (read before changing)

- `tools/web_search.py` has two routing paths:
  1. `is_search_command()` — strict regex, "David gave an explicit command". Fires `lookup()` for a deterministic sourced line.
  2. `is_search_intent()` — broader trigger list, injects results into the LLM prompt so the LLM composes the answer.
- `server.py:3817` uses `is_search_command` for the direct path; `server.py:3960` uses `is_search_intent` for the broader path. Both share `tools.web_search` as the data source.
- `_SEARCH_COMMAND_RE` already covers "google X", "look up X", "search for X", "read up about X", "look into X" and the interrogative "can/could/would you google/search X" forms.

## The gap I found

The card's own example — `David says "what's happening with the NBA?" → eLo: "So there's been a lot going on — [summary]"` — did not route.

- `is_search_command("what's happening with the NBA")` → False (correct; this is more conversational than imperative).
- `is_search_intent("what's happening with the NBA")` → **False.** `_SEARCH_TRIGGERS` had `"what's the latest"`, `"latest on "`, `"news on "`, but no "what's happening" variant.

Verified by running the two gates against six real phrasings — the NBA line was the only miss.

## Fix (Builder 3-owned files only)

**`tools/web_search.py`** — one-location edit to `_SEARCH_TRIGGERS`:
```
# WO-B3-0012: sprint-acceptance phrases David uses for current-events searches.
"what's happening",
"whats happening",
"happening with ",
```
Three substrings, apostrophe-optional, so `is_search_intent` fires on "what's happening with X" / "whats happening with X" / "anything happening with X". No other code touched. `is_search_command` deliberately left alone — a casual "what's happening with X" is a question, not an imperative; the LLM-composed path (which is what `is_search_intent` triggers) is correct here.

**`tests/test_wo_b3_0012_web_search_demo.py` (new)** — 6 acceptance cases:
- **AT-1** `"look up the Berlin Wall"` → `is_search_command=True`, topic `"the Berlin Wall"`, `lookup()` returns `"Looked it up on Wikipedia — ..."` with the topic in it.
- **AT-2** `"can you google Fela Kuti"` → interrogative form routes, topic resolves to `"Fela Kuti"`, line has the topic and no bullet markers.
- **AT-3** `"read up about Pinky and the Brain"` → topic resolves to the full name, line has no raw URLs.
- **AT-4** `"what's happening with the NBA"` → `is_search_intent=True` (THIS IS THE FIX), `format_for_context()` produces a well-formed `[WEB_SEARCH_RESULTS]` block the LLM can read.
- **AT-5** `compose_found()` rejects promo copy ("Click here to subscribe", "Sign up today") and first-person forum opinion ("I've been listening", "I think").
- **AT-6** `lookup()` returns the B3 `{success, result, error}` contract shape with the fields `capability_status` reads.

SerpAPI (`_serp_search`) and Wikipedia (`wiki_summary`) are both mocked; no network and no live server touched.

## Test results (real Mac, pytest 9.1.1)

```
tests/test_wo_b3_0012_web_search_demo.py ..........  (6 passed)
tests/test_wo051_search_fallback.py ..........       (6 passed)
tests/test_b3_interrogative_routing.py ..............  (48 passed)
============================== 60 passed in 0.49s ==============================
```

Also ran `tests/test_b3_capability_status.py tests/test_hard01_execution_context.py` — 42 passed, 1 skipped, no regression on adjacent B3 surface.

## File-lock discipline

- Created `tools/web_search.py.lock` before editing (seat, timestamp, purpose).
- Committed (88b1396).
- Deleted the lock immediately after commit.
- No other shared file on the CLAUDE.md list touched.

## What this does NOT prove

Offline tests prove the gates fire and the pipeline composes a sourced line from mocked results. They do not prove:
1. The live SerpAPI key is valid (`.env` has `SERPAPI_KEY` — need a live turn to confirm).
2. The LLM, given the `[WEB_SEARCH_RESULTS]` block, actually produces a conversational summary rather than a bullet list. That's a prompt-builder question — if David gets a bullet-list answer on item 4 of the sprint, I spec a fix to Builder 1 (prompt_builder is Builder 1's file).

Three live-verification turns needed per the Board test gate for integration cards (vary wording):

1. "what's happening with the NBA?" — formerly LLM-no-context, now routes to `is_search_intent` → results injected → LLM composes.
2. "can you google Fela Kuti" — `lookup()` path, deterministic "Looked it up on Wikipedia — ..." line.
3. "read up about Pinky and the Brain" — `lookup()` path, Wikipedia-led summary.

Acceptance for 0012: all three return a spoken summary in eLo's voice, not a raw list.

## Status

- Card 0012: **built, filed for Board live-verification.** Do NOT self-promote to BUILT per CLAUDE.md "BUILT ≠ DONE".
- Items 1–3 of the demo sprint remain blocked as above.
- Items 4 and 5 (web search / music) now both have offline-pipeline proof and are awaiting live-verification turns from the Board.
- EXIT — one card only.
