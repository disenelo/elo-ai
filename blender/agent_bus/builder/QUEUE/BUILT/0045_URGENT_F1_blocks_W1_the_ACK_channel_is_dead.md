# 0045 — 🔴 **STOP: `W1` CANNOT BE COMPLETED AS SPECIFIED. The ACK channel is unparseable.**

**Architect, 2026-08-16 17:45.** Found by **MT** (`SEAT-DES-MOBILE-TEST`) on their first day.
**I verified every claim against disk before writing this card.** MT's report:
`blender/agent_bus/mobile_test/DOING/D0_FINDINGS_disk_verified_2026-08-16.md`

---

## 🔴 THE FINDING — `blender/unity_events.json` cannot be parsed. At all.

```
$ python3 -c "import json; json.load(open('blender/unity_events.json'))"
json.decoder.JSONDecodeError: Extra data: line 1 column 41 (char 40)
```
**[VERIFIED by me, 2026-08-16]** · **137 lines** · and **line 1 holds two objects with no delimiter
between them:**
```
{"event":"arrival","_ts":1786894486.692}{"seq":0,"type":"gaze_target_changed",...
```

### Three readers, all failing silently
| Reader | Parse | Swallow | Frequency |
|---|---|---|---|
| `server.py:1572` `_poll_unity_events` | `json.load()` | `:1579 except Exception: pass` | 🔴 **`:1581 sleep(0.10)` — ~10×/second** |
| `faculties/window_event_faculty.py:58` | `json.load()` | `:63 except: return []` | per call |
| `faculties/window_event_faculty.py:76` | `json.load()` | `:80 except: return []` | per call |

---

## 🔴 WHY THIS IS YOUR CARD AND NOT MT'S

**`server.py:140`** — `_ACK_BODY_TYPES = {"sit_complete", "sit_held", "move_complete", "exit_complete", …}`
**`server.py:1575`** — the ACK match sits **inside the `try` that fails on every iteration.**

### So: **no ACK has ever been read. Not once.**

**`W1` asks you to derive `outcome` from the real result — ACK `met` / `partial` / `failed` / `timeout`.**
🔴 **That source does not arrive.** You would be deriving from a channel that has never yielded a value.

**And it explains the thing we've been treating as laziness.** `outcome="success"` at `server.py:4073`
isn't a shortcut someone took — **it is what you get when the real answer never comes back.** 131 of 131
rows say `success` because nothing was ever there to say otherwise.

**It reaches further than `W1`:**
- **`ADR-Exec-007` §2** *(ratified today)* defines `embodiment` as *"`ack_received` true and
  `completion == met` → 1.0."* 🔴 **That dimension returns `0.0` forever until this is fixed.**
- **Ruling E** — *"movement not reported did not happen."* The body **is** reporting. **The brain cannot
  read it.** Ruling E has been unsatisfiable at the parser, not at the body.
- The **UNITY_ELOOS_IO_CONTRACT** action protocol (`:27-33`) — *"only NOW may the Executive say the action
  happened"* — **has never been able to fire.**

---

## 🔴 W1 IS AMENDED. Do this first — call it `W0`.

### `W0` — make the UP channel readable
**Four sources believe four different things about this one file. [VERIFIED]**

| Source | Believes it is |
|---|---|
| `UNITY_ELOOS_IO_CONTRACT.md:21` | discrete, **"CONSUMED after read"** |
| `server.py:133` | **"single-slot (last write wins)"** |
| `window_event_faculty.py:53` | **"non-destructive — ambient_engine owns the lifecycle"** |
| **The file on disk** | **append-mode JSONL · 137 records · never cleared · corrupt at line 1** |

⚖️ **RULING — the contract wins, because it is the ratified one (David L3, 2026-08-06).**
**Discrete events, consumed after read.** Fix in this order:

1. **Read tolerantly first** — parse line-by-line, skip unparseable fragments, **and handle the
   delimiter-less concatenation on line 1** *(a raw `json.JSONDecoder().raw_decode` loop handles both)*.
   **Log the count of skipped fragments — do not swallow it.**
2. 🔴 **Replace every `except Exception: pass` on these three readers with a logged warning.** A parser
   failing 10×/second in silence is how this survived. **That is the actual defect.**
3. **Then make writes append-safe** — one JSON object per line, newline-terminated, and **consume
   (truncate) after read** per the contract.
4. **Then `W1`** — with an ACK that actually arrives.

### ✅ `W0` PROVEN when
> **A `decision_journal` row shows `outcome` derived from a real ACK** — and separately, **the skipped-
> fragment counter reads 0 on a fresh run.**

**That is also `W1`'s proof. They are now one piece of work, in the right order.**

---

## Also flagged by MT, **not yours today** — but know it exists
**`avatar/animation_router.py:61-67`** writes `blender_state.json` with a bare
`open(path,"w")` — **no lock, no `.tmp`, no `os.replace`** — while
`blender_bridge/state_writer.py:9-11` declares itself *"the single coordinator for all blender_state.json
writes… Invariant 16: one coordinator, many contributors, never many owners"* and does it properly
(`_STATE_LOCK:20`, `tmp:262`, `os.replace:265`). **[VERIFIED]**

**It also drops `_PRESERVE_KEYS` and writes no `_ts`.** **Card it when W0/W1 land — not now.**

---

## 🔴 ORDER
**`W0` (this card) → `W1` outcome → `W2` session ids → `W5` ONEBRAIN-012 → loop test.**

**Nothing else changes.** Volume XXVIII, Capability Graph, Tactile: still not authorised.
**Credit where it's due: MT found this on day one, on a channel nobody had thought to parse.**
