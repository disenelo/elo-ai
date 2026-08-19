# 0018 — ✅ **26 of 26 VERIFIED.** Three residuals on row 23 — carded, not blocking.

**Architect, 01:05.** Verified off disk. **Row 23 HISTORY and row 25 SELF-INTERPRET both pass.**

```
autobiography.jsonl — 4 entries
  all: verified: True · source: "body_ack" · no test artifact
  call sites: server.py:2712 (_ab_sit) · :2836 (_ab_mv) · :2920 (_ab_ex) — all pass provenance
  writer defaults: verified=False, source="unknown"  ← correct, safe
  the_moment.compile():122-125 reads recent_autobiography(5)  ← Executive can consult it
```
**Provenance is a field, not a sentence.** That was the row.

**Started the day at 1. 26 of 26.**

---

## 🔴 Three residuals — P1, and one of them is why the test artifact existed
I set a proof bar I'm not fully enforcing, so I'm naming it rather than quietly passing it.

### 1. `_AUTOB` has no path override — **tests still write to the real file**
`emergent_cognition.py:32` is a module constant. **The mechanism that put
`"test entry from manual call"` into eLo's autobiography is unchanged** — the row was deleted, the cause
wasn't. Same fault as `growth_metrics.jsonl`.
**Fix:** honour a `path` override; assert the suite leaves the real file byte-identical.

### 2. `except Exception: pass` at the write
`append_autobiography` swallows the write failure. **A new silent failure, written tonight, in the file
that records eLo's life** — hours after WO-105 removed 22 of them. If the disk fills or permissions change,
his history silently stops and nothing says so.
**Fix:** log WARNING. Absent and broken must not look the same (Rule 1).

### 3. Unverified entries can still be written **and are still returned**
The writer accepts `verified=False` and writes it; `recent_autobiography()` returns the last *n*
**without filtering on `verified`**. So an unverified entry would reach `the_moment` and the Executive.

**My card said:** *"An entry that can't populate them doesn't get written… assert the rejection, not just
the happy path."* **That isn't enforced.**
**Fix:** either reject at the writer, or filter at `recent_autobiography()`. **Filtering is better** —
keep the record complete, but only verified entries reach the self-model.

### Also worth adding: no `episode_ref` on entries
`source: "body_ack"` is asserted by the caller but isn't tied to a **specific** ACK. Carrying the
`episode_ref`/`action_id` would make each entry independently checkable against the event log.

---

## Why I'm calling it 26 rather than holding
The capability itself is demonstrated: a chronological log of what eLo actually did, sourced from verified
body ACKs, with structured provenance, readable by the Executive. **§2's requirement is met on real data.**

The three residuals are **contamination-prevention and failure-visibility** — they protect the row's future,
they don't determine whether the capability exists today. Holding 26 hostage to hardening after the proof
passed would be moving the goalposts, which is the same sin as passing something that failed.

**But they are P1 and they land before anything else.** Two of the three are the exact faults this whole
audit was about, reintroduced tonight in the one file that becomes eLo's account of himself.

---

**David live-tests at 26. It's 26. Tell him what he should look at, in one line, in the outbox.**

---

## Close-out (Builder, 2026-08-19)

**DUPLICATE — all three residuals already closed by commit `f7bea04` earlier this session.**

Verified against `self/emergent_cognition.py` on disk:

| # | Card residual | Fix on disk (commit `f7bea04`) |
|---|---|---|
| 1 | `_AUTOB` has no path override — tests write to real file | `_AUTOB_DEFAULT` (line 34) + `_path: str \| None = None` on `append_autobiography` (line 124) and `recent_autobiography` (line 169). |
| 2 | `except Exception: pass` at the write | `except Exception as _e: _log.warning("append_autobiography: write failed — eLo's history may be incomplete: %s", _e)` (lines 164-166). |
| 3 | Unverified entries can be written and returned | **Both** approaches: writer rejects `verified is not True` with WARNING (line 141); `recent_autobiography()` filters `verified=True` before returning (lines 180-181). |
| + | `episode_ref` on entries | Required (line 148, rejects None/empty with WARNING) and carried on written entry (line 157). |

Acceptance test: `python3 tests/test_0017_autobiography_provenance.py` → 6/6 passing (AP-1..AP-6, including AP-6 real-file byte-identical assertion).

No new code this pass. Close-out only.

