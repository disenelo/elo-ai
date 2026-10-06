# WIRE — Websearch: add spine call for search intent (2026-10-05)
**From:** Board / Lead Architect
**To:** Builder 3
**Date:** 2026-10-05
**Priority:** P0 — Kickstarter critical
**Source:** Live verification 2026-10-05

---

## State of play

Everything is built. Nothing is wired.

| Component | Status |
|---|---|
| `tools/web_search.py` | EXISTS — full SerpAPI + DDG fallback, engine routing, `is_search_command()`, `resolve_search_topic()`, `search_topic()`, `compose_found()` |
| `SERPAPI_KEY` in `.env` | EXISTS — confirmed present |
| `dispatch_web_research()` in `capability_registry.py` | EXISTS — calls `tools.web_search.search()`, returns results list |
| Call in `spine.py` | MISSING — zero references |
| Call in `backend_router.py` | MISSING — zero references |

The gap: the user's message never reaches `is_search_command()`. The spine processes the turn as a normal LLM request. Websearch never fires.

---

## The wire to add

In the spine's request handler (where user input is received and before LLM call), add:

```
1. from tools.web_search import is_search_command, resolve_search_topic, search_topic, compose_found

2. if is_search_command(user_message):
       topic = resolve_search_topic(user_message, recent_user_turns)
       if topic:
           canonical_name, results = search_topic(topic)
           if results:
               spoken = compose_found(canonical_name, results)
               # inject into response context OR set as elo_response directly
               # spoken is eLo's voiced result: "Looked it up — [what he found]"
```

Check `spine.py` for the exact insertion point — where the user turn is processed and before `backend_router.py` is called for LLM generation. The search result replaces the LLM call for this turn, or is injected as context so the LLM builds on real facts.

---

## `resolve_search_topic` signature

```python
resolve_search_topic(text: str, recent_user_turns: list[str] | None = None) -> str
```

Pass the last 2-3 user turns as `recent_user_turns` so it can resolve vague references like "look it up" → "Pinkie and the Brain" (from the prior turn).

---

## Evidence required

David says "do a websearch on Pinkie and the Brain" → eLo responds with real search results in his voice (compose_found output). No LLM filler. Real content from the web.
