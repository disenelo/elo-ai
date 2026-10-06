# Spec → Builder 1: hand "who is / what is <Name>" to research before the 0021 gate (server.py)
**From:** Builder 3 · 2026-10-06 · **Authority:** David L3, 2026-10-06, verbatim: *"Look it up as if he wants to figure out, that's how it should be research if he doesn't know, understand it's context and store if needed, parts into memory."*

## Now
- `server.py`, the 0021 P0-Y proper-noun gate: any "who/what is <Capitalised>" that misses the world graph returns `"I don't know who X is — tell me?"` early.
- Research never runs. Example: "who is Jim Carrey" → "I don't know who Jim is — tell me?"

## Change (in the 0021 block, before `_pn_reply` is returned)
```python
try:
    from tools.research import answer_gap as _rs_gap
    _rs_line = _rs_gap(_original_raw)
except Exception:
    _rs_line = None
if _rs_line:
    _ws_direct, _ws_backend = _rs_line, "direct:research"    # the B3 head-of-chain answers it
else:
    ... existing don't-know short-circuit ...
```
`tools/research.py` keeps 0021's honesty where it matters:
- eLo's own world: the graph gate runs first, and K-7 / Chunk / eLo / David are never researched.
- A bare first name whose Wikipedia page is about the *name* returns the same "I don't know who X is — tell me?".
- Only public names are looked up, and the source is always named ("looked it up on Wikipedia: …").

Component check (outside the server):
- "who is Sam" → "I don't know who Sam is — tell me?"
- "who is Jim Carrey" → "Didn't know that one — looked it up on Wikipedia: James Eugene Carrey is a Canadian and American actor…"
- "What is Pinky and the Brain?" → Wikipedia lead
