# FROM BUILDER — WO-REGISTER-PLACEMENT-001 RESULT

**Status:** DONE — 2026-09-08  
**Commit:** 2a23484

## What was built

In `server.py`, added voice register echo immediately before `_llm_latency_ms = 0.0` (just before the LLM call):

```python
# WO-REGISTER-PLACEMENT-001: voice register echo closest to generation
try:
    from runtime.voice_register import get_register_block as _vrb_echo
    system = system + (
        "\n\n[eLo VOICE IDENTITY — always, this turn]\n"
        "eLo speaks from his own register. Not formal English with slang inserted."
        " The rhythm, compression, and naturalness above apply to this response."
    )
except Exception:
    pass
```

Additionally, `runtime/voice_register.py` header was strengthened from `# LINGUISTIC REGISTER` to `# eLo VOICE IDENTITY — NON-NEGOTIABLE` with framing "This is who eLo is. Not a style preference. Not a mode."

## Before / After

**Before:** Voice register was injected at position 3 in `build_prompt` but visually distant from generation due to everything appended after. No echo near LLM call.

**After:** Non-negotiable framing + brief echo immediately before model receives the prompt. Closest possible placement to generation.

## Tests

5/5 WO-VOICE-REGISTER-001 tests pass. 1549 total pass / 0 new failures.
