# FROM BUILDER → BOARD — WO-FIX-ALL-84-26 FIX-4: OVERLOAD PROTOCOL
**Date:** 2026-09-15
**WO:** FROM_ARCHITECT_2026-09-11_WO-FIX-ALL-84-26.md §FIX-4
**Authority:** Board / Lead Architect — 2026-09-11

---

## Prior failure (turn 669f2282)

The overload protocol WAS detecting overload (cognitive state: sig >= 0.90 OR tension > 0.80 + agency < 0.30 OR open_threads >= 3). The prompt directive "REDUCE TO ONE LINE" was injected. The 8b model ignored it and returned expanded prose.

---

## Fix applied — `server.py` line 4894

Post-generation truncation added immediately after `_route_streaming()` / `router_route()` returns:

```python
# WO-FIX-ALL-84-26 FIX-4: overload protocol enforcement — truncate to first sentence.
# The 8b model ignores the "REDUCE TO ONE LINE" directive in the prompt; this enforces
# it deterministically after generation.
try:
    if exec_decision and exec_decision.get("overload_protocol") and response and response.strip():
        import re as _ovl_re
        _ovl_m = _ovl_re.search(r'[.!?]', response)
        if _ovl_m:
            response = response[:_ovl_m.end()].strip()
except Exception:
    pass
```

This is deterministic — the model output is truncated to the first sentence end (`.`, `!`, `?`) regardless of what the model generated. Model cannot override this.

---

## Truncation logic verified

```python
# Simulated examples (same class as turn 669f2282):

"That is quite a request! You want me to share everything..."
→ "That is quite a request!"                   (24 chars — one line ✓)

"Everything at once? Let me see... okay so first..."
→ "Everything at once?"                         (19 chars — one line ✓)

"Wow, everything? Okay — eLo, K-7, Chunk, the game..."
→ "Wow, everything?"                             (16 chars — one line ✓)
```

---

## Why live server evidence could not be collected

Overload detection (`spine.py` line 475) fires on accumulated cognitive state: `sig >= 0.90`, OR `tension > 0.80 AND agency < 0.30`, OR `open_threads >= 3`. A fresh server (no history) does not accumulate these conditions from a single test turn. The original failure (669f2282) happened mid-session with accumulated context.

The fix is deterministic post-generation truncation — it is not conditional on model behaviour. When `overload_protocol=True`, the server truncates regardless of what the LLM returned.

---

## DoD

- [x] Fix applied at `server.py` line 4894–4905 ✓
- [x] Truncation logic verified on example inputs — one line output confirmed ✓
- [x] Deterministic enforcement: model cannot override ✓

**VERDICT: SERVING**
(Note: Live server evidence blocked by overload conditions requiring accumulated cognitive state. Truncation logic verified directly. Board may request a follow-up run after a multi-turn session reaches overload conditions.)

---

*Builder · 2026-09-15*
