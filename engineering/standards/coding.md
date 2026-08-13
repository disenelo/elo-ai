# Coding Standards — eLo OS

**Status:** ACTIVE
**Authority:** Lead Systems Architect

---

## Language and Environment

- Python 3.11+ (miniconda, `~/miniconda3/bin/python`)
- All eLo OS runtime code lives in `~/elo-ai/`
- Unity C# code lives in DISENELO Presence (`~/Desktop/Output/DISENELO-eLoDesktopBuddy/`)
- Unity C# is handled by Unity Agent only — never edited directly in Claude Code

---

## File Organisation

```
runtime/         — cognitive spine, faculties, router
tools/           — data agents (weather, vision, news, etc.)
ambient/         — background presence engine
presence/        — presence scheduler
desktop/         — desktop shadow (window state, app context)
blender_bridge/  — state writer to blender_state.json
memory/          — memory files (JSON)
config/          — runtime configuration
tests/           — unit and integration tests
```

---

## Coding Rules

### No Silent Scope Creep

Build exactly what the implementation plan says. If a related improvement is noticed, document it — do not fix it alongside the current task.

### No Fallback Behaviour Unless Specified

If a component receives empty input, it returns empty output. It does not invent a default. It does not fire a pool response. Empty = nothing. The spec must explicitly require any fallback for one to exist.

### Never Raise to the User

All components catch their own exceptions. Failures are logged. They never propagate to the user as Python tracebacks.

```python
try:
    result = do_something()
except Exception as e:
    _log.debug("component_name: %s", e)
    return None  # or empty dict, empty string — whatever the interface specifies
```

### FREEZE_V1_LOCK

`runtime/executive.py` and `prompts/` are never modified. If a change to these files seems necessary, that is a signal the design is wrong. Revise the design.

### No Hard-Coded User-Facing Strings

All response pools live in `server.py` with clear names (`_FAREWELL_POOL_SOUTH_LDN`, `_INVADE_REPLIES`, etc.). No user-facing string is buried inside logic.

### State Writes Are Atomic

All writes to `blender_state.json` use the read-merge-write-atomic pattern:

```python
tmp = _STATE_PATH + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(state, f)
os.replace(tmp, _STATE_PATH)
```

Never write directly. Never truncate and rewrite. Always merge into existing state.

### Threading

Background threads (vision loop, ambient engine, presence scheduler) use `threading.Event` for clean shutdown. They are daemon threads. They never block the main request thread.

### No New Dependencies Without Review

Every new `import` from outside the standard library or existing `requirements.txt` requires explicit review. Reason: miniconda environment, deployment to Robot (Raspberry Pi 5), and offline mode all constrain what can be installed.

---

## Naming Conventions

| Item | Convention | Example |
|---|---|---|
| Module-level constants | `_UPPER_SNAKE` | `_FAREWELL_POOL` |
| Public functions | `snake_case` | `shadow_context()` |
| Private functions | `_snake_case` | `_detect_intent()` |
| Classes | `PascalCase` | `CognitivePlan` |
| Config keys | `snake_case` | `"refresh_interval_seconds"` |
| Response pools | `_NAME_POOL` | `_ANIM_REPLIES` |
| Regex patterns | `_NAME_RE` | `_INVADE_RE` |

---

## Comments

Write no comments unless the WHY is non-obvious. Do not comment WHAT the code does — the names do that. Comment hidden constraints, non-obvious invariants, and specific bug workarounds.

```python
# Atomic replace — blender_state.json is polled by Unity every ~100ms
os.replace(tmp, _STATE_PATH)
```

No multi-line comment blocks. No doc-strings for internal functions. One line max.

---

## Security

- `.env` is GITIGNORED. Never read it in tests. Never print its contents. Never commit.
- API keys are read at runtime via `os.environ.get()`. Never hard-coded.
- User birth data (18 Jan 1986, 01:17, Camberwell Green) never stored in memory files.
- ElevenLabs, Cerebras, AccuWeather, OpenAI, Gemini keys: `.env` only.

---

## Git

- Never auto-commit from within eLo OS (`logs/pending_commits.jsonl` — system never auto-commits).
- Commit messages describe WHY, not WHAT.
- No force-push to main without explicit authorisation.
- No amending published commits.
