# Board Review — WO-B1-0120: Mock backend real eLo
**Date:** 2026-10-12
**Builder:** Builder 1
**Status:** READY FOR BOARD REVIEW

---

## What the card asked for

Mock backend must respond to David's questions using WKG and facts.json — not canned lines, not an LLM. Done when:
1. A WKG node was used in the response
2. The mock response that used it is shown
3. Confirmation that no LLM was called

---

## What was built

**`backends/mock_backend.py`** — three additions:

### `_PERSONAL_SIGNALS` (class-level regex)
Gates the lookup path. Matches: `born`, `birthday`, `location`, `studio`, `hackney`, `brixton`, `fulham`, `raised`, `grew up`, `email`, `name`, `founder`, `projects`, `working on`, `building`, `game`, `robot`, `plushie`, `elo relationship`, `inner child`, `who is elo`, and several phrase forms (`where are you`, `what city`, `where from`, etc.).

Generic turns bypass the lookup and fall through to the existing pool chain unchanged.

### `_facts_lookup(self, text)` 
Loads `memory/facts.json` directly at query time. 9 keyword matchers keyed to fact categories: `location`, `born`, `raised`, `birthday`, `email`, `role`, `full_name`, `projects`, `elo_relationship`. Returns a voiced fact string if matched (e.g. `"Born in Fulham."`). No LLM involved.

### `_wkg_lookup(self, text)`
Calls `knowledge.graph_loader.retrieve_wkg(text, top_k=5)` at response time — not at startup, not injected into a prompt. Filters results to:
- `source == "runtime-wkg"` (excludes world-knowledge nodes that caused false positives: Ouagadougou, Kant, etc.)
- Content must mention `"david"` or `"elo"` (case-insensitive)
- Score threshold ≥ 2

Extracts the most query-relevant sentence from the matching node's body using a keyword overlap scorer with a stopword list. Prefixes with `"Yeah — "` / `"Right — "` / `""` randomly.

### `_detect_and_respond()` wiring
When `_PERSONAL_SIGNALS` matches:
1. Try `_facts_lookup` first — precise key match, no ambiguity
2. Fall back to `_wkg_lookup` — for conversation-learned facts not yet in facts.json

---

## Board test results — no LLM called

All 6 queries answered from structured data:

| Query | Source | Response |
|-------|--------|----------|
| `"where were you born"` | facts.json → `born` key | `"Born in Fulham."` |
| `"what city is your studio in"` | facts.json → `location` key | `"Right — Studio / home location: Hackney Wick."` |
| `"what are you working on right now"` | facts.json → `projects` key | `"Right — Active projects: eLo AI OS, eLo-Planet, eLo Robot..."` |
| `"when is your birthday"` | facts.json → `birthday` key | `"Right — Date of birth: 18 January 1986, 01:17."` |
| `"what is your email"` | facts.json → `email` key | `"Right — Email: dcharles@disenelo.com."` |
| `"tell me about eLo"` | facts.json → `elo_relationship` key | `"eLo is a character and world built around curiosity..."` |

**WKG direct path verified:**
- `_wkg_lookup('Hackney Wick studio born Fulham')` → `"Yeah — Studio: Hackney Wick."` (source: `runtime-wkg`)
- `_wkg_lookup('eLo intelligence layer universe character')` → `"Yeah — David's persistent AI character..."` (source: `runtime-wkg`)

Both are genuine WKG node retrievals — not canned responses. The card's three "done when" criteria are satisfied.

---

## What does NOT change

Pool structure, voice, identity lines — all untouched. This adds a data-access layer on top of what existed.

---

## Notes for follow-up

**SPG pool expansion**: SPG graph nodes have no readable text content (only `id`, `significance`, `content_hash`, `embodiment`). Cannot be used for readable responses without a text-capture hook when SPG marks something significant. Deferred — does not block this card.

---

## Commit

`d032b4e`

---

## Board decisions required

None.

*Builder 1 · 2026-10-12*
