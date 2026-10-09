# RATCHET FINDINGS — Builder 1 Filing
**Date:** 2026-10-09  
**Filed by:** Builder 1  
**WO causing exceedance:** WO-0104 (`0dcc363`)

---

## Summary

Both ratchets were tripped by exactly one addition each — the capability dispatcher math fast-path added in WO-0104. Both additions are correct by design. Board decision needed: rebaseline or fix the exit shape.

---

## partial_turn_exits (ceiling 45, current 46)

**Count at commit `057df91` (pre-WO-0104):** 45  
**Count at current HEAD:** 46  
**Delta:** +1

**The new exit — L2911 in `_process_turn()`:**
```python
return {"response": _cap_val, "mode": "direct", "backend": "capability_dispatcher"}
```

**Is it correct?** Yes. This is the FACT-tier math fast-path. It follows the same shape as every other EXECUTOR-FAST-PATH handler in the function (e.g. L2833, L2859, L2891, L2929 — all `{"response", "mode", "backend"}`). The pattern is consistent.

**Does it get normalised at runtime?** Yes. `_process_turn()` callers apply `_tr_norm(result)` at the chokepoint; the partial dict is normalised before it reaches the response pipeline. The test is a source-level AST count, not a runtime shape check.

**Why it crossed the ceiling:** The ceiling was already at 45 (raised from the original 41 to accommodate prior WOs). WO-0104's one addition pushed the count to 46, one over.

**Which exits did WO-0104 add? Any incorrect?** One exit only (L2911). It is correct — identical pattern to all other fast-path handlers.

---

## _bypass_journal (ceiling 55, current 56)

**Count at commit `057df91` (pre-WO-0104):** 55  
**Count at current HEAD:** 56  
**Delta:** +1

**The new call (alongside L2911 exit):**
```python
_bypass_journal(_original_raw, backend="direct", handler_class="EXECUTOR-FAST-PATH", line=0)
```

**Is it correct?** Yes. Every fast-path handler that returns early calls `_bypass_journal` before returning — this is the protocol. WO-0104 followed it correctly. The ceiling of 55 captured pre-0104 state; 56 is one over.

**What bypassed that shouldn't?** Nothing. All 56 calls are legitimate bypass handlers (EXECUTOR-FAST-PATH, TRANSPORT, COGNITIVE, SAFETY categories). The test BH-7 verifies all EXECUTOR-FAST-PATH handlers have a `_bypass_journal` call — WO-0104's new handler is one such entry.

---

## Board options

**Option A — Fix the exit shape (Builder 1 can do this)**  
Instead of returning the partial dict directly, pass it through `_tr_norm()` before the return. The test counts AST-level partials; this would reduce the count to 45. The `_bypass_journal` count stays at 56 (it's independent of the return shape). Still need to rebaseline BH-2 ceiling from 55 to 56.

**Option B — Rebaseline both ceilings**  
Raise test assertions: `assert len(partial) <= 46` and `expected 56 _bypass_journal calls`. This records the new watermark. Builder 1 can do this if authorized — but Board said NOT to raise ceilings unilaterally.

**Option C — No change (accept exceedance)**  
Accept that both tests will fail until Board acts. Not recommended — ratchets exist to catch genuine growth.

---

## What Builder 1 will NOT do without Board authority

- Raise either ceiling
- Delete the capability_dispatcher fast-path (it is correct and live)
- Mark these tests as expected-failure

Builder 1 awaits Board direction.
