# WO-B3-0012 — Web Search + Summaries
**Seat:** Builder 3  
**Priority:** P0 — demo milestone  
**Date:** 2026-10-11

---

## What

eLo searches the web and returns a summary in natural language — not a raw list of links.

David says "what's happening with the NBA?" → eLo: "So there's been a lot going on — [summary]"  
David says "look up [topic]" → eLo: [short conversational summary of top results]

## How

- Verify `tools/web_search.py` is wired and routing correctly
- If intent routing isn't catching "look it up", "what's happening with X", "search for X" → spec the routing fix to Builder 1's inbox (do not touch `spine.py`/`backend_router.py` yourself)
- The result must be a conversational summary, not bullet points or raw search output

## Acceptance

Board tests: 3 different natural language search requests. All must return a spoken summary in eLo's voice, not raw results.

---
## Builder 3 (interactive) 2026-10-11: BUILT
- Seat commits 88b1396 + 76a660a; Board gate signed off. Checked: "what's happening with the NBA?" → is_search_intent True (the server's search path, server.py ~L4103).
- Live-turn gate (David): 3 search turns per BOARD-GATE_B3-0012.
