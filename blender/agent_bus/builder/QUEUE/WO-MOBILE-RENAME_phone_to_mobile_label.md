# WO-MOBILE-RENAME — Rename embodiment label `phone` → `mobile`

**Authority:** David L3 (2026-08-30) — verbatim: "Phone should be mobile as that's the same thing it's a mobile device, you are the Mobile Tester, MT."
**Source:** `FROM_MT_2026-08-30_QBODY_proprioception_mirror_BLOCKERS.md` BLOCKER 1
**Priority:** P1 (unblocks MT emitter consistency)
**Owner:** Builder (spine-side rename)

---

## What changed

David ruled the mobile body's embodiment label is `"mobile"`, not `"phone"`.

Current shipped code in `runtime/mobile_embodiment.py`:
```python
state.embodiment = "phone"          # line 40
"to": "phone"                       # line 53 (relay)
# embodiment stays "phone"          # line 79 (comment)
```

All three must become `"mobile"`. All tests asserting on the string `"phone"` for embodiment must be updated to `"mobile"` as well.

---

## ⚡ VERIFY FIRST

1. `grep -r '"phone"' runtime/mobile_embodiment.py` — enumerate every occurrence
2. `grep -rn 'embodiment.*phone\|phone.*embodiment' tests/` — find test assertions
3. Rename all occurrences (string rename only, no logic change)
4. Run existing WO-MOBILE-001 test suite — must still pass

---

## Acceptance Tests

- **AT-1:** `mobile_embodiment.py` contains zero occurrences of the string `"phone"` (as an embodiment value)
- **AT-2:** Existing WO-MOBILE-001 tests pass (updated to `"mobile"`)
- **AT-3:** No other spine file or test is broken by the rename
- **AT-4:** `executive.py` NOT TOUCHED (FREEZE_V1_LOCK). `"phone"` may appear in comments as "phone device" — only the embodiment value string changes.

---

## Sequence note (Board)

MT's UP-channel emitter will also say `"mobile"`. Board is sequencing this spine rename BEFORE or WITH MT's emitter to avoid a split-label window. Builder close = unblocks MT.

---

## Return

`DONE/FROM_BUILDER_WO-MOBILE-RENAME_phone_mobile_result.md` · AT pass count · commit hash

*Board / Lead Architect · 2026-08-30*
