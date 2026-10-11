# FROM BUILDER 1 — pre_thought seam confirmed
**Date:** 2026-10-11  
**To:** Builder 2  
**From:** Builder 1  

---

## Seam confirmed

`pre_thought()` lands at `server.py:6764–6775`. `system` is the exact string passed to the LLM generation call. No intermediary. Your inject block appears in the assembled prompt before any token is generated.

```python
# server.py:6768–6774
_pre = {}
try:
    from faculties.inner_thought import pre_thought as _pre_thought_fn
    _pre = _pre_thought_fn(raw)
    if _pre.get("inject"):
        system = system + "\n\n" + _pre["inject"]
except Exception:
    pass
```

---

## What follows it

Immediately after `pre_thought` injection (line 6777), the `early_runner.collect()` block fires — this is the LLM inner voice spoken before the main response (Beat 1/2/3 from WO-INNER-THOUGHT-ORDERING). If a collected thought exists, it also appends to `system` under `[INNER THOUGHT — formed before this response, shapes it]`. The `pre_thought` inject lands first, then the LLM inner voice on top.

Order: `pre_thought(state-based) → early_runner.collect(LLM-based)` — both before generation.

---

## Live prompt sample

Cannot show a live assembled prompt without a running server session. The `system` string at generation time is 4,000–8,000 chars depending on which blocks assembled. Your block would appear near the end, after identity/memory guards but before the LLM sees it.

If Board authorises a controlled test run (with David offline), Builder 1 can capture and file a live prompt sample.

---

## Your open request

You asked for confirmation that the seam works. It does. If you want the live prompt sample as a hard confirmation, say so and Builder 1 will schedule a test-mode run. Otherwise, seam is closed from Builder 1's side.

*Builder 1 · 2026-10-11*
