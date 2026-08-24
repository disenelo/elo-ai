# FROM ARCHITECT → BUILDER · 2026-08-21 · XVII is read-side, and that's the LOOP-7 line

**Not a complaint — your card said "the read-side DoD" and that was honest.** Flagging where it lands.

`runtime/spine/spine.py:274-286`:
```python
_ls_recall(context={...}, k=1)
# Recall runs so lesson_store's internal state is fresh each turn.
# No attribution derived here — prompt injection is prompt_builder's job.
plan.lesson_id = ""   # D3 BLOCKED: attribution withheld until Executive unfreezes
```

**The lesson is recalled and then discarded.** That is exactly **LOOP-7** — *"lessons reach his words, never
his decisions"* — and it is **Presentable v1 acceptance test 3**: *"it feels alive because eLo UNDERSTOOD AND
ACTED, not because a timer fired."*

**Your 15 tests prove the read side. None prove the Executive used it, because it doesn't.** Under the new
DoD (built · **wired** · **exercised** · falsifiable) XVII is wired on the read path only.

🔴 **Do not fix this here.** `plan.lesson_id = ""` is the **D3 boundary** and unfreezing the Executive is
David's. Card `0074` (Volume VII) is where the ground for that decision gets written.
**Suggest marking XVII `✅ read-side proven · write-side D3-blocked` rather than plain proven** — so nobody
later reads it as LOOP-7 being closed.
