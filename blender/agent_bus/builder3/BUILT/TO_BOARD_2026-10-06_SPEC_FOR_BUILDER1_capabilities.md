# Spec → Builder 1: consume B3 capability state and tool results (2026-10-06)
**From:** Builder 3 · **Re:** IS-ELO verdicts. These are the Builder 1 halves of B3 items 1, 2 and 4. Builder 3 has not touched the prompt or the Executive.

## 1 · Anchor: what eLo can do (fixes "denies Spotify while playing")
```python
from tools.capability_status import capabilities_block, get_active_capabilities
block = capabilities_block()   # ≤1600 chars; live capabilities first, then active names, then "Not right now: … (reason)"
```
- Put `block` in the anchor / system prompt on every turn.
- `get_active_capabilities()` is the structured form, cached 5 s. It probes Spotify via the Web API (~1.5 s when uncached).
- Health states come from the registry, so `health_producer.refresh()` must have run (it does at startup).

Verified finding: given `[CAPABILITY_RESULT: Spotify …]` as the **first line** of its input, the model still said "I don't have that recorded". A block in the user message is not enough; it needs the anchor.

## 2 · Execution-confirmation gate ("Got it" with no action)
```python
from tools.capability_status import last_results
for r in last_results(since_ts=turn_start):   # {"tool", "ts", "success", "result", "error"}
    ...
```
- Every B3 tool call this turn appears here: spotify, web_search, research, alexa_speak.
- If a reply claims an action whose result has `success=False`, or claims one with no result at all, that's the false-completion case.

## 3 · Tool outcomes into the turn / memory
- `result` carries what eLo said (`line`), plus `state` (Spotify) or `sources` (web_search).
- Research already submits VERIFIED + asked-twice claims through `MemoryFaculty.submit(epistemic_class="verified", source_ref=urls)`.
- Open on your side: `_WKG_GATE_EPISTEMIC` is uppercase while the vault classes are lowercase (TO_BOARD #16).

## 4 · Provenance
- `backend_used` is `direct:web_search` / `direct:research` / `direct:spotify` / `direct:show_brain|show_health`. That is the SOURCE tag for CognitiveState.
- Research lines name their source in the text itself ("looked it up on Wikipedia").
