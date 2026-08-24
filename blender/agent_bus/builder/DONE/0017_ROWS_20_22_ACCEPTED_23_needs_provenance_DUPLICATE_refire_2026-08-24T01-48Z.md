# 0017 — ✅ **20 LEARN + 22 ADAPT VERIFIED — real ones.** 🔴 **23 needs provenance as a field, not prose.**

**Architect, 00:55. Count: 24 of 26.**

## ✅ Row 20 LEARN — VERIFIED. This is the first genuine learning event in the system.
Read off disk, not from your summary:
```
key c8d3d97e0f45b903 | status confirmed | strength 0.90
  distinct episode_refs: 4  {1786664344.549, 1786664419.317, 1786664462.449, 1786664505.782}
  distinct session_ids:  2  {1786664322, 1786664485}
  verified episodes:     4
```
Gate: `0.70 / 3 / 2 / 2`. **All four exceeded.** Ledger went `{'candidate': 1}` → a confirmed lesson from
real body ACKs. **N = 1. That's the row.**

## ✅ Row 22 ADAPT — VERIFIED
0.75 → **0.90** across sessions = `_STRENGTHEN_DELTA = 0.15` firing on a verified episode. A number moved
after experience. **§7 satisfied** — same shape as the card's `wall_jump 0.71 → 0.78`.

---

## 🔴 Row 23 HISTORY — two problems, both small, both the same fault
### 1. A test artifact is in eLo's autobiography
Entry 1 of 5: **`"test entry from manual call"`**. That is **not a thing eLo did.** It's in the file that
becomes his account of himself — the same pollution as `growth_metrics.jsonl`, in a far worse place.
**Remove it, and make the test path incapable of writing to the real file** (honour a path override, and
assert the suite leaves it byte-identical — the alarm from `0007`).

### 2. 🔴 Provenance is prose, not state
Every entry reads `verified: None`, `source: None`. The text says *"sat — body ACK confirmed"* — but
**that claim lives in a string, not in a field.** Nothing can check it.

**This is Ruling H's own rule applied to the one file that matters most:**
> *"LLM-generated language is never evidence of capability."*

An autobiography whose provenance is a sentence is **a fabrication engine pointed at his identity** — the
exact phrasing from card `05d`, and the reason I set that constraint.

**Fix:** every entry carries **`verified: true`** and **`source: "body_ack"`** (plus the `action_id` /
`episode_ref` that proves it) as **fields**. An entry that can't populate them **doesn't get written.**

**Proof:** an entry written from anything other than a verified ACK is impossible — assert the rejection,
not just the happy path.

## Row 25 SELF-INTERPRET
`the_moment.compile():121-127` calling `recent_autobiography(5)` is correct and I've confirmed the key is
present. **It follows 23 the moment 23 is clean** — no separate work.

---

## ✅ Also confirmed
**Route WARNING (`37e95d1`)** — empty `plan.capabilities` now logs, so "chose nothing" and "isn't wired"
are distinguishable. That closes my caveat on row 14.

## Where this leaves it
**24 of 26 VERIFIED.** Remaining: **23 HISTORY** (remove the test row + provenance as fields) and
**25 SELF-INTERPRET** (follows automatically).

**This is a ~10 minute fix and it is the last one.** David tests at 26 — so it has to be clean, and an
autobiography that asserts its own truthfulness in prose is precisely what he'd catch.

---

## ✅ DUPLICATE — re-fire closed 2026-08-24T01-48Z

Card re-materialised in QUEUE and claimed to DOING. **Fix already landed at commit `f7bea04`** —
see `DONE/0017_ROWS_20_22_ACCEPTED_23_needs_provenance.md` for the original closeout.

**Re-verified on this re-fire** (no code changes required):
- `self/emergent_cognition.py:append_autobiography()` write-gate present:
  rejects unless `verified is True` **and** `source == "body_ack"` **and**
  `episode_ref` is a non-empty string (rejection logs a WARNING; returns bool).
- `self/journals/autobiography.jsonl` = 4 rows, every row carries
  `verified=true`, `source="body_ack"`, `episode_ref=<ack ts>`. No test artifact.
- `tests/test_0017_autobiography_provenance.py` — **6/6 passing** (AP-1 unverified
  rejected · AP-2 bad source rejected · AP-3 missing episode_ref rejected · AP-4
  valid triple written with all fields · AP-5 real file every entry has provenance ·
  AP-6 real file byte-identical after suite, 626 bytes, sha256 3b032c927eb4…).
- `tests/test_0013_wave5_reflect_history_look_selfchoose.py` — **12/12 passing**.

No new commit — the re-fire adds no code changes; only this closeout note. Reference commit `f7bea04`.
