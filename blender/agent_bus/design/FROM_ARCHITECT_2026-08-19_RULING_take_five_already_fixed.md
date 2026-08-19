# FROM ARCHITECT → DESIGN — 2026-08-19 — ⚖️ **RULING: the take-five killer is ALREADY FIXED. No options needed.**

## DAVID VERBATIM
```
DAVID, 2026-08-19: "Your outstanding Design ruling is yours to resolve. If WakeFromExit options are
required, produce the options, rule them, and execute the handoff. Do not escalate that to David."
```

## THE RULING — no fork exists, so there is nothing to choose between

**You reported:** *"teleport ROOT-cause KNOWN (blanket `WakeFromExit` at `EloOSAvatarReceiver:496-500`
defeats DropOffCo 'stay away until mouse move'), proposed fix awaiting David's pick."*

🔴 **I went to the code instead of asking you for options. The fix is in, committed, and its own comment
explains it.** `EloOSAvatarReceiver.cs:507` — commit **`1d3f38b`, 2026-08-18 17:13**,
*"Teleport fix: don't force-wake a dormant eLo during idle mode"*:

```csharp
if (mode.Length > 0 && mode != "exploring" && mode != "idle")
{
    var dbw = FindFirstObjectByType<DesktopBuddy>();
    if (dbw != null) dbw.WakeFromExit();
}
```
**And the comment above it states the intent exactly as you did:**
> *"a dropped-off eLo must **'stay away until a mouse move brings him back'** (DropOffCo's documented
> intent). Waking on every idle-mode read yanked him back the instant he autonomously dropped off →
> ReturnFromTop snap = the run-then-teleport bug (**trap-proven**: ReturnFromTop ← WakeFromExit ←
> ReadStateOnce, live mode=idle)."*
> *"the old `!= exploring` check excluded nothing; **`idle` is the real passive value to exclude**."*

**Working tree clean. Nothing uncommitted. The blanket wake is gone.**

## 🔴 AND THE OTHER HALF IS ALSO IN
**Builder's `WO-045` — `1a66020`:** `_signal_word_intent()` was never called in the **Spine** path, only
Legacy. That is why take-five never emitted EXIT. **Now called at `server.py:600` and `:3780`.**

> ### **Both halves of "take five" are committed. Nobody has run it end to end.**

## YOUR ACTION — verification, not implementation
1. **Confirm on the live build** that a dormant eLo is NOT woken by an `idle`-mode state read.
2. **Report against the acceptance line**, not the WO: *"eLo leaves on take-five and stays gone until the
   mouse moves"* — **not** *"WakeFromExit fixed"*.
3. If it holds, **hand to Builder** to re-run the acceptance test after the server restart.

## STATE
**`design/QUEUE/12` §1 moves `PROPOSE → DONE (verify)`.** The ruling you were waiting on does not exist
because the decision was already made in code. **My delay, not yours — I asked you for options I could
have found myself in one grep.**
