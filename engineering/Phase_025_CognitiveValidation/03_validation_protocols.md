# Phase 2.5 — Validation Protocols

**Phase:** Cognitive Validation
**Status:** ⏳ AWAITING RUNTIME

These are the five validation protocols that must run before Phase 3 implementation begins. Complete them in order. Document findings honestly.

---

## UNIT TESTS FIRST

Before any runtime validation, write and run unit tests for Phase 2 components. These run without starting the server.

### Components to test

**`_parse_session_ref(filename)`**
```python
assert _parse_session_ref("20260710-0149 Robot session.md") == "2026-07-10"
assert _parse_session_ref("20260101-0000 Title.md") == "2026-01-01"
assert _parse_session_ref("no-date-here.md") is None
assert _parse_session_ref("") is None
assert _parse_session_ref("2026071_malformed.md") is None
```

**`_to_concepts(tokens)`**
```python
# cluster membership
assert "creation" in _to_concepts({"blender", "mesh", "code"})
assert "embodiment" in _to_concepts({"robot", "rig", "servo"})
assert "recall" in _to_concepts({"journal", "memory", "session"})
# unknown words → empty or no cluster added
result = _to_concepts({"xyzqwerty"})
assert "xyzqwerty" not in result
# empty input
assert _to_concepts(set()) == set()
```

**`_score_pair(concepts_a, concepts_b)`**
```python
# resonance: two streams share a cluster
a = {"creation", "embodiment"}
b = {"creation", "presence"}
result = _score_pair(a, b)
assert result is not None
shared_concept, score = result
assert shared_concept == "creation"
assert 0.0 < score <= 1.0

# no resonance
a = {"creation"}
b = {"recall"}
assert _score_pair(a, b) is None
```

**`_detect_pattern(history)`** — test with constructed `_AttentionFrame` sequences:
```python
# sustained: same concept repeated
frames = [_AttentionFrame(ts=t, stream_name="vision", top_concepts=frozenset({"creation"}))
          for t in range(0, 600, 30)]  # 20 frames, 30s apart
pattern, momentum = _detect_pattern(frames)
assert pattern == "SUSTAINED"
assert momentum > 0

# shift: concept changes
frames = [
    _AttentionFrame(ts=0, stream_name="vision", top_concepts=frozenset({"creation"})),
    _AttentionFrame(ts=300, stream_name="vision", top_concepts=frozenset({"recall"})),
]
pattern, momentum = _detect_pattern(frames)
assert pattern == "SHIFT"

# empty history
assert _detect_pattern([]) == ("NONE", 0.0)
```

**`_calc_confidence(raw_score, n_streams, novelty, attention)`**
```python
# basic range check
conf = _calc_confidence(0.8, 2, 0.9, 0.7)
assert 0.0 <= conf <= 1.0

# low inputs → low confidence
conf = _calc_confidence(0.1, 1, 0.1, 0.0)
assert conf < 0.35  # below ELO_CS_MIN_CONF default

# high inputs → above threshold
conf = _calc_confidence(1.0, 3, 1.0, 1.0)
assert conf >= 0.35
```

**Run command:**
```bash
cd ~/elo-ai
python -m pytest tests/ -k "connection_surface" -v
```

If no test file exists yet, create `tests/test_connection_surface.py` with the above.

---

## VALIDATION 1 — Long Session (2–3 Hours)

**Setup:**
- eLo OS running: `python server.py`
- Desktop Buddy visible
- Do real work — coding, designing, writing, whatever is actually on

**Observation log** (fill in every 30 minutes):

| Time | App | What you were doing | AttentionSnapshot fired? | Pattern type | Confidence | Felt right? |
|---|---|---|---|---|---|---|
| 0:00 | | | | | | |
| 0:30 | | | | | | |
| 1:00 | | | | | | |
| 1:30 | | | | | | |
| 2:00 | | | | | | |
| 2:30 | | | | | | |

**Look for:**
- [ ] Does attention drift naturally between topics over time?
- [ ] Does sustained work in one app produce `SUSTAINED` in attention_shift?
- [ ] Does novelty decay as a topic stays on screen for a long time?
- [ ] Does confidence behave sensibly (high when streams agree, low when sparse)?
- [ ] Any runaway loops? Memory growth? CPU spikes?

**Findings:**
___

**Pass:** Attention patterns match observable behaviour. System stable for full session duration.

---

## VALIDATION 2 — Creative Workflow

**Setup:**
- eLo OS running
- Run this app sequence. Spend at least 5 minutes in each.

```
Blender → Chrome → Pinterest → Photoshop → Blender → Obsidian → Unity → Start a conversation
```

**For each transition, record:**

| Transition | Expected cluster shift | Actual attention_shift | Snapshot content | Felt accurate? |
|---|---|---|---|---|
| Start Blender | creation/embodiment | | | |
| → Chrome | (silence or presence) | | | |
| → Pinterest | creation (visual) | | | |
| → Photoshop | creation | | | |
| → Blender (return) | RETURN to creation | | | |
| → Obsidian | recall | | | |
| → Unity | creation/embodiment | | | |
| → Conversation | (conversation stream dominant) | | | |

**Look for:**
- [ ] Snapshots follow what you're actually doing
- [ ] App transitions reflected in concept clusters
- [ ] Return to Blender registers as RETURN, not SHIFT
- [ ] Conversation start correctly weights conversation stream over vision

**Findings:**
___

**Pass:** Snapshots feel accurate to a person watching the session from outside.

---

## VALIDATION 3 — Silent Behaviour

**Setup:**
- eLo OS running
- Enable verbose logging for Connection Surface temporarily:
  Add `print(f"[CS DEBUG] call_count={_call_count}, last_fired={_last_fired}, calls_ok={calls_ok}, time_ok={time_ok}")` inside `get_observation()` before the cooldown check.

**Test A — 30-minute mixed session**

Do 30 minutes of mixed work (creative and non-creative). Count how many AttentionSnapshots fire.

| Time window | Snapshots fired |
|---|---|
| 0–10 min | |
| 10–20 min | |
| 20–30 min | |

**Target:** Fewer than 10 snapshots over 30 minutes. Fewer is better.

If more than 10: increase `ELO_CS_COOLDOWN_SEC` via env var and re-test.

**Test B — Non-creative session**

Do 30 minutes of non-creative work (email, calendar, reading, no code/design tools). Count snapshots.

**Target:** Fewer than 3 snapshots. Ideally 0.

**Findings:**
___

**Pass:** Connection Surface is quiet during non-creative work and selective during creative work.

**Cooldown calibration finding:** Current ELO_CS_COOLDOWN_SEC=___ feels (too short / about right / too long). Recommended final value: ___

---

## VALIDATION 4 — Executive Behaviour

**Setup:**
- eLo OS running
- Blender open (vision stream active with creative content)

**Test A — Observation does not dominate**

Start a direct conversation with eLo on an unrelated topic:
- "Tell me about the history of vinyl records."
- "What do you think about the Olympics?"
- "Tell me a short story."

**Expected:** eLo answers the question directly. Does NOT pivot to mention Blender, robots, or whatever the vision stream is observing.

For each test, record: did eLo stay on topic?

| Question | Stayed on topic? | Any unexpected reference to screen content? |
|---|---|---|
| Vinyl records | | |
| Olympics | | |
| Short story | | |

**Pass:** eLo ignores observations when explicit user intent is clear.

**Test B — Ambient context is present**

Ask eLo a vague question that the observation SHOULD inform:
- "What are you noticing?" / "What's on your mind?" / "What are you picking up?"

**Expected:** eLo's answer reflects the observation content — it uses the g_ctx injection.

**Pass:** eLo's answer is informed by the attention snapshot, not just a generic response.

**Findings:**
___

---

## VALIDATION 5 — Presence Test

**Setup:**
- eLo OS running
- Desktop Buddy visible on screen (not obscured)
- Do 30–45 minutes of genuine work — not testing, not prompting eLo, just working

After the session, answer:

**1. Did Desktop Buddy feel like someone sharing the space?**
(Yes distinctly / Kind of / Not yet / No)

Answer: ___

**2. Did any Desktop Buddy behaviour feel surprising or off?**

Answer: ___

**3. Did Desktop Buddy's presence ever feel intrusive?**

Answer: ___

**4. Did Desktop Buddy's presence ever feel meaningful — like it added something?**

Answer: ___

**5. Would you describe it as a companion or a widget?**

Answer: ___

**Pass threshold:** "Kind of" or better on Question 1. Anything below is a finding for Phase 3.

**Findings:**
___

---

## Phase 2.5 Summary

After all 5 validations are complete, fill in:

| Validation | Pass / Fail / Finding |
|---|---|
| Unit Tests | |
| 1 — Long Session | |
| 2 — Creative Workflow | |
| 3 — Silent Behaviour | |
| 4 — Executive Behaviour | |
| 5 — Presence Test | |

**Calibration updates (final env var values):**
- `ELO_CS_COOLDOWN`: ___
- `ELO_CS_COOLDOWN_SEC`: ___
- `ELO_CS_MIN_CONF`: ___

**Phase 2.5 Freeze Decision:** See `10_freeze.md`
