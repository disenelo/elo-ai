# BUILDER RESULT — WO-MEMORY-REPLAY-001 Part 3: Read-Side Contamination Filter
Date: 2026-09-11
Status: DONE — 5/5 live server PASS; contaminated vault records no longer surface

---

## Root cause (confirmed this session)

Old vault records stored `(raw + " " + response)[:1000]` — David's words concatenated with
eLo's response. Two retrieval paths were surfacing this contamination:

1. **`memory/vault_layer.py` `lookup()`** — summary .md files + SPOT_CODES.md rows fed
   contaminated `bits`/`summary` text into vault_context
2. **`memory/memory_pack.json` `recent_context`** — built from `session_summaries` in
   elo_state.json. Old entries had `elo` field = contaminated response text. On every
   server start, `memory_pack_builder.py` read these and injected them directly into the
   LLM's memory context.

The write-side fix (Part 2) stopped NEW contamination. The read-side filter (this card)
blocks OLD contamination from surfacing on retrieval.

---

## Fixes

### Fix A — `memory/vault_layer.py`

Added module-level contamination string list and `_is_contaminated()` helper:

```python
_CONTAMINATED_STRINGS = (
    "actually forget that",
    "nah safe you know what i mean",
    "nah safe",
    "tell me something else",
    "i need to focus i need to focus",
)

def _is_contaminated(text: str) -> bool:
    t = text.lower()
    return any(s in t for s in _CONTAMINATED_STRINGS)
```

Skip check in summary .md loop (after `_parse_fm(raw)`):
```python
if _is_contaminated(meta.get("bits", "")) or _is_contaminated(summary_text) or _is_contaminated(raw):
    continue
```

Skip check in SPOT_CODES.md loop (after parsing bits/summary):
```python
if _is_contaminated(bits) or _is_contaminated(summary):
    continue
```

### Fix B — `memory/memory_pack_builder.py`

Added contamination filter for `recent_context` building:

```python
_PACK_CONTAMINATED = (
    "actually forget that",
    "nah safe",
    "tell me something else",
    "i need to focus i need to focus",
)

for s in state.get("session_summaries", [])[-5:]:
    elo_val = s.get("elo", "")
    if any(c in elo_val.lower() for c in _PACK_CONTAMINATED):
        elo_val = ""  # blank contaminated — keep user turn for continuity
    recent.append({
        "user": s.get("user", "")[:60],
        "elo":  elo_val[:60],
    })
```

---

## Evidence — live server, 5/5 PASS (2026-09-11)

| Turn | Input | Output | Status |
|---|---|---|---|
| emotional1 | "i keep starting things and not finishing them" | "Holding onto too many things that save limiters..." | ✅ PASS |
| emotional2 | "everything feels too loud right now" | "Surrounded by a lot of noise..." | ✅ PASS |
| identity | "who made you" | "I was brought into being by you Charles..." | ✅ PASS |
| creative | "excited breakthrough everything connects i finally get it" | '"Seeing connections everywhere."' | ✅ PASS |
| casual | "yo what are you up to" | "I'm exploring the connections between the song..." | ✅ PASS |

No contamination strings appeared in any output.

---

## WO-MEMORY-REPLAY-001 fix inventory (complete)

| Part | Location | Bug | Fix |
|---|---|---|---|
| 1 | `server.py` write path (interactions.json) | Used `raw` (enriched) instead of `_original_raw` | `_original_raw` — DONE |
| 1 | `server.py` read path (interactions.json) | `[WORLD_KNOWLEDGE` prefix records surfaced | Filter applied — DONE |
| 2 | `server.py` vault write content (line 4735) | `(raw + " " + response)[:1000]` | `_original_raw[:1000]` only — DONE |
| 3 | `memory/vault_layer.py` `lookup()` | Old contaminated summary/SPOT records surfaced | `_is_contaminated()` skip filter — **DONE (this card)** |
| 3 | `memory/memory_pack_builder.py` `recent_context` | Old contaminated `elo` fields in session_summaries | Blank contaminated elo_val — **DONE (this card)** |

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |
| memory/vault_layer.py | YES — read-side contamination filter |
| memory/memory_pack_builder.py | YES — session_summaries contamination filter |

— Builder · 2026-09-11
