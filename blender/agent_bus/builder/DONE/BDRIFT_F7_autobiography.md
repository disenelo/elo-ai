# BDRIFT-F7 — Autobiography: Retrieval → Self-Context → eLo Response

SOURCE: `docs/architecture/_intake/SOURCE_2026-08-22_DAVID_F7_F8_separate_work_packages.md`
AUTHORITY: David directive 2026-08-22 (verbatim capture above) · ADR-Exec-005 D1 · WO-081 (card 0081) · WO-117 (card 0083)

---

## FINDING

F-7 is the runtime maturity gap in eLo's autobiographical memory chain. David's required chain is:

```
experience
    ↓
verified autobiographical memory   (append_autobiography — gate: body_ack + verified=True + episode_ref)
    ↓
retrieval                          (recent_autobiography — exists, not wired to response path)
    ↓
self-context                       (GAP — content never reaches spine/executive)
    ↓
eLo response
```

The write side and the store exist and are correctly gated. The retrieval-to-self-context-to-response link is missing. Additionally, what constitutes an "experience" worthy of autobiography is not defined beyond body_ack — this ambiguity must be surfaced, not silently resolved.

David constraint (verbatim): "without allowing ordinary observations, generated text, or user input to silently become eLo's history."

---

## CURRENT BEHAVIOUR

| Location | What exists today |
|---|---|
| `self/emergent_cognition.py:112` | `_VALID_SOURCES = frozenset({"body_ack"})` — the only accepted source |
| `self/emergent_cognition.py:115–164` | `append_autobiography()` — gate: `verified=True`, `source in _VALID_SOURCES`, `episode_ref` non-empty string. Rejects silently (WARNING logged). Writes to `self/journals/autobiography.jsonl`. |
| `self/emergent_cognition.py:167–181` | `recent_autobiography(n)` — reads `self/journals/autobiography.jsonl`, filters `verified=True`, returns last n entries. EXISTS. NOT CALLED anywhere in the spine or executive path. |
| `self/journals/autobiography.jsonl` | 5 entries, all `kind: "action"`, all `event: "sat — body ACK confirmed"`, all `source: "body_ack"`, all `verified: true`. Sparse. |
| `runtime/self_interpret.py:35` | `_AUTOBIOGRAPHY = os.path.join(_ROOT, "self", "journals", "autobiography.jsonl")` — correct path |
| `runtime/self_interpret.py:59–76` | `_load_autobiography()` — reads file, filters `verified=True`. Called by `interpret()`. |
| `runtime/self_interpret.py:149–152` | `interpret()` uses `verified_count = len(auto_entries)` as a count for `derived_from`, but does NOT surface the content of autobiography entries into the returned `SelfInterpretation.text`. The actual event narratives are invisible to eLo. |
| `runtime/self_interpret.py:79–173` | `interpret()` is UNKNOWN as to whether it is called by `runtime/spine/spine.py` in the response path. Documented caller is `spine.py` (card 0083 §3) — **Builder must verify the wire exists and is exercised.** |

---

## REQUIRED BEHAVIOUR

```
body_ack event arrives
    ↓
append_autobiography(event, kind, verified=True, source="body_ack", episode_ref=<ack_ref>)
    ↓
self/journals/autobiography.jsonl  (append-only, provenance-gated)
    ↓
recent_autobiography(n) called at response-build time
    ↓
autobiographical content injected into self-context block
    ↓
self_interpret.interpret() reads entries — not just counts them
    ↓
SelfInterpretation.text carries the experiential record
    ↓
spine injects into eLo's response context
    ↓
eLo response grounded in lived, verified history
```

**What constitutes an "experience":** For v1 this is `body_ack` only (existing gate). Builder must NOT expand `_VALID_SOURCES` — that is an L3 decision. If there is a runtime case where another source should qualify, ESCALATE before touching `_VALID_SOURCES`.

---

## EXACT CHANGE BOUNDARY

Builder touches ONLY:

1. **`runtime/self_interpret.py`** — extend `interpret()` to surface actual autobiography entry content (event text, kind, episode_ref) into `SelfInterpretation.text`, not just count them. Minimum: if `auto_entries` is non-empty, include the most recent verified entry's event text as a grounded claim with its episode_ref as the source citation. Maintain the falsifiability rule (card 0083 §2): every claim cites a count or a reference that exists in `derived_from`.

2. **Spine wire** (`runtime/spine/spine.py` or wherever `interpret()` is called) — verify `interpret()` is actually called in the response path and its output reaches the prompt. If the wire is missing, add it. If it exists, confirm it is exercised (a test must go RED when the wire is cut).

3. **Tests** — add/extend a test that:
   - writes a verified body_ack entry to a temp autobiography file
   - calls `interpret()` with that file
   - asserts the returned `SelfInterpretation.text` contains the event content (not just counts)
   - cuts the spine wire and asserts the text does NOT reach eLo's context (regression)

---

## DO NOT CHANGE

- `self/emergent_cognition.py:112` — `_VALID_SOURCES` — do not expand without David L3
- `self/emergent_cognition.py:115–164` — `append_autobiography()` gate logic — do not weaken
- `self/journals/autobiography.jsonl` — append-only; do not rewrite or migrate
- `runtime/executive.py` — FREEZE_V1_LOCK
- Any canon or Volume documents

---

## INPUTS

- Trigger: a `body_ack` event is confirmed (existing signal path, not built here)
- At response time: `recent_autobiography(n)` called with the real file path
- `interpret(state, autobiography_path)` receives the `EloSelfState` and the path

---

## OUTPUT

- `SelfInterpretation` dataclass with `.text` containing grounded autobiographical claims (not hollow counts)
- `.derived_from` list that includes `{"source": "autobiography", "key": <episode_ref>, "count": 1}` for surfaced events
- `.verified_events` = number of verified autobiography entries read

---

## ACCEPTANCE TEST

All four conditions required (Rule 4j):

1. **Built** — `interpret()` in `self_interpret.py` returns `SelfInterpretation.text` that includes the event text from at least one verified autobiography entry (not just "I have N verified events").
2. **Wired** — `spine.py` (or the documented caller) calls `interpret()` and the returned text reaches the prompt/self-context block on a real turn.
3. **Exercised** — run a real turn after a body_ack event; eLo's response context contains autobiographical content traceable to the verified entry.
4. **Falsifiable** — cut the `recent_autobiography()` call inside `interpret()` (or cut the spine wire); the test goes RED.

Specific assertion: given one autobiography entry `{"event": "sat — body ACK confirmed", "verified": true, "source": "body_ack", "episode_ref": "test-ref-001"}`, `interpret(state)` must return a `SelfInterpretation` whose `.text` contains `"sat"` or `"body ACK"` and whose `.derived_from` includes an entry referencing `"test-ref-001"`.

---

## REGRESSION TEST

What must stay RED if the wire is cut:

- Test: inject a verified autobiography entry → call `interpret()` → assert `.text` references the entry → CUT `recent_autobiography()` call → assert `SelfInterpretation` is `None` or `.text` does NOT reference the entry.
- Existing card 0083 tests (15/15 passing for Volume XVII) must still pass after the change.

---

## EVIDENCE REQUIRED

Builder must produce:

1. `git diff` showing only the files listed in EXACT CHANGE BOUNDARY
2. Test run output showing the new test passing
3. Confirmation that the spine wire exists and is exercised (file:line reference)
4. Confirmation that existing card 0083 tests still pass (15/15)
5. Log showing at least one call to `interpret()` on a real turn that produced non-empty `SelfInterpretation.text` with autobiography content

---

## ESCALATION CONDITION

Stop and raise to Architect if:

- The spine wire (`spine.py`) does not exist and cannot be added without touching `runtime/executive.py` (FREEZE_V1_LOCK)
- A runtime case surfaces where something other than `body_ack` should qualify as a source — do not expand `_VALID_SOURCES` unilaterally; that is L3
- `interpret()` is called in the response path but the result is discarded by a downstream component — that is an architecture question, not a Builder edit
- The test cannot be made falsifiable without creating new fixtures that would conflict with card 0083 test state
