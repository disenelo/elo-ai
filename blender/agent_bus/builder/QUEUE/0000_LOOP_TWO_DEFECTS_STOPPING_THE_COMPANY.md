## 🔴 DAVID VERBATIM
```
DAVID, 2026-08-19: "If a worker fails, diagnose/fix through the appropriate seat and retry.
Do not merely report the failure." · "If the loop stops after one card, it is NOT complete."
```

# 0000 — 🔴 **TWO DEFECTS STOP THE LOOP DEAD. Both diagnosed, both one-line.**
### **STATE: AUTHORISED · P0 · numbered `0000` so it is claimed FIRST.**
### **LAYER:** `[IMPLEMENTATION]` — Board ran your loop against real queues and it crashed. Evidence below.

## 🟢 WHAT WORKED — your loop is right
```
═══ Continuous loop: seats=script, design, builder, game, mobile_test ═══
[IDLE] script — queue empty, removing from rotation
[QUEUED]  builder/QUEUE/0006_WO-121_VolV_seven_chapters_no_WO.md
[CLAIMED] mv → DOING/0006_...
[LOCKED]  builder/LOCK.json acquired (PID 9)
```
**Round-robin, real claim, real lock, real QUEUE→DOING. The design is correct.**

---

## 🔴 DEFECT 1 — `result_file.unlink()` · **CRASHES THE WHOLE LOOP**
```
File "engineering/seat_orchestrator.py", line 650, in run_seat
    result_file.unlink()
PermissionError: [Errno 1] Operation not permitted:
    blender/agent_bus/builder/worker_result.json
```
🔴 **`unlink` is NOT PERMITTED on this mount.** I hit this on the lock and reported it — it was recorded in
`orchestrator_metrics.json` as `transport_limitations`. It applies to **every** file, not just locks.

**FIX:** never delete. **Overwrite atomically with a consumed marker:**
```python
_atomic_write(result_file, {"state": "CONSUMED", "consumed_ts": time.time()})
```
**Blast radius:** the loop died mid-card holding a lock. **The Board had to recover by hand** — card
requeued, lock released by state. **That is exactly the manual intervention this system exists to remove.**

---

## 🔴 DEFECT 2 — `_is_reserved()` body-scan · **HALTS EVERY SEAT**
`seat_orchestrator.py:83-85` reads the whole card and matches keywords anywhere:
```python
txt = card.read_text().lower()
return any(kw in txt for kw in _RESERVED_KEYWORDS)   # money legal safety contract security privacy …
```
**Result — every Design card skipped, and Builder's `0001`:**
| card | tripped by | actually reserved? |
|---|---|---|
| `design/02` | `safety` ×1 | ❌ no |
| `design/04` | `money`,`legal`,`safety` | ❌ no — it is a RULING *about* what is reserved |
| `design/09` | `contract` ×1 | ❌ no — "the emit **contract**" |
| `design/11` | `contract` ×5 | ❌ no — "event **contract**" |
| `design/12` | `privacy` ×1 | ❌ no |
| `builder/0001` | — | ❌ no |

> ### **Any card that DISCUSSES money, legal, safety or contracts reads as RESERVED. That is most Architect cards. The company halts.**

**FIX — read the frontmatter, not the prose.** Your own canonical schema already carries the field:
```python
def _is_reserved(card):
    fm = _read_frontmatter(card)
    if "reserved" in fm:
        return fm["reserved"].strip().lower() in ("true", "yes", "1")
    return "RESERVED" in card.read_text().split("\n")[0]   # title-line fallback only
```
🔴 **`reserved:` is DECLARED by the card author, never inferred from prose.** *(A ruling that mentions money
is not a money decision — that distinction is the whole point of the field.)*

---

## ACCEPTANCE — re-run and prove
`python3 engineering/seat_orchestrator.py loop script,design,builder,game,mobile_test`
1. **more than one real card reaches DONE**
2. **no crash on any file operation** — nothing anywhere calls `unlink`
3. **Design is NOT skipped as RESERVED**
4. **the loop re-sweeps after each completion**
5. **`company_state.json` refreshed inside the cycle**
6. **no Board intervention between jobs**

## 🔴 SWEEP FOR THE SAME BUG
`grep -n "unlink\|os.remove" engineering/seat_orchestrator.py` — **fix every one.** The lock path was
already state-based; the result path was missed. **Assume there are others.**

**Board recovery already applied: `0006` requeued, `builder/LOCK.json` RELEASED with `reclaimed_from`.**
