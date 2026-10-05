# Evidence — P0 Movement Verb Routing Fix
**WO:** FROM_ARCHITECT_2026-10-05_MOVEMENT-VERB-ROUTING-FAIL.md
**Date:** 2026-10-05
**By:** Builder 1
**Commit:** ebf0ab0

---

## Fix 1 + Fix 2 — Movement verbs route to movement system, not LLM

**File:** `runtime/spine/presence_faculty.py`
**Change:** Added 14 missing movement verbs to `_SIGNAL_WORDS` at end of dict (after all height-targeted entries to preserve priority order).

**New entries:**
| Signal word | Intent |
|---|---|
| `peek` | `explore` |
| `can you peek` | `explore` |
| `can you climb` | `explore` |
| `climb` | `explore` |
| `walljump` | `explore` |
| `wall jump` | `explore` |
| `wall-jump` | `explore` |
| `can you wall jump` | `explore` |
| `exit run` | `explore` |
| `hop` | `explore` |
| `jump` | `explore` |
| `land` | `idle` |
| `warp` | `explore` |
| `teleport` | `explore` |
| `disappear` | `step_out` |

**Priority preservation verified:**
- `climb to the middle` → `{"name": "climb_height", "height": 0.5}` — CORRECT (height-targeted entry earlier in dict wins)
- `stop jumping` → `idle` — CORRECT (idle complaint rules precede bare "jump" in iteration order)
- `parkour` → `explore` — CORRECT (unchanged existing entry)

**Routing verification (python -c):**
```
OK: 'peek' -> 'explore'
OK: 'climb' -> 'explore'
OK: 'walljump' -> 'explore'
OK: 'wall jump' -> 'explore'
OK: 'can you wall jump' -> 'explore'
OK: 'exit run' -> 'explore'
OK: 'hop' -> 'explore'
OK: 'jump' -> 'explore'
OK: 'land' -> 'idle'
OK: 'warp' -> 'explore'
OK: 'teleport' -> 'explore'
OK: 'disappear' -> 'step_out'
OK: 'climb to the middle' -> {'name': 'climb_height', 'height': 0.5}
OK: 'parkour' -> 'explore'
OK: 'stop jumping' -> 'idle'
All OK
```

**Result:** "peek"/"climb"/"walljump"/"wall jump"/"exit run" now route to `_signal_word_intent` → `explore` intent → presence faculty → movement system. They never reach the LLM. Fixes the echo pattern ("Climb?") simultaneously — LLM sees nothing.

---

## Fix 3 — NAME RULE scrub

**File:** `server.py`
**Location:** After AI-leakage identity scrub (~line 6989), before WO-GUARD-001.

**Code added:**
```python
_NR_PAT = _re.compile(r'\b(the user|a user|the human)\b', _re.IGNORECASE)
if _NR_PAT.search(response):
    _logging.warning("NAME_RULE_SCRUB: prohibited self-reference found — replacing with 'David'")
    response = _NR_PAT.sub("David", response)
```

**What it does:** If `elo_final` contains "the user" / "a user" / "the human" as a self-referential term, replaces with "David" and logs a WARNING. Catches the cases where the anchor in `_ollama_stream` fails under model pressure. David never sees these terms.

---

## Fix 4 — LLM bleed-through

Addressed by Fix 1+2: once "peek"/"climb"/"walljump"/"exit run" are caught by `_signal_word_intent`, they route to the movement system and the LLM never generates a response for them. Generic filler ("That's valid. And worth pressing on.") cannot appear.

---

## Test results

```
10 passed — presence faculty tests
3023 passed, 0 regressions — full suite (sentinel test_xi_ad2_parity_proven deselected, intentional red)
```

---

## Live evidence required (Board review gate)

Send "peek" to eLo → routes to navplanner, eLo does not say "I don't have that recorded."
Send "climb" → same.
Send "walljump" → same.
Check elo_final for "the user" → none (or NAME_RULE_SCRUB fires in logs).

Builder 1 · 2026-10-05

---

## Addendum — server.py sync (2026-10-05, session 2)

The original fix (commit ebf0ab0) applied the movement verb vocabulary to `runtime/spine/presence_faculty.py`.
Server.py has its own copy of `_SIGNAL_WORDS` at line 399, used by `_movement_intent()`.

This addendum syncs the same entries into server.py's dict:

- `peek` → `explore`
- `walljump` → `move/wall_jump`
- `wall-jump` → `move/wall_jump`
- `climb` (bare, after compound entries) → `move/wall_jump`
- `exit run` → `move/step_back_run_fire`
- `warp` → `explore`
- `teleport` → `explore`
- `disappear` → `step_out`

Also added: `MVVERB_ECHO_SCRUB` post-gen safety net at server.py (after AI-leakage scrub). If response
matches `^<movement-verb>\s*\?\s*$`, replaces with "On it." and logs WARNING.

Syntax verified: `py_compile.compile('server.py', doraise=True)` PASS.

Builder 1 · 2026-10-05 (addendum)
