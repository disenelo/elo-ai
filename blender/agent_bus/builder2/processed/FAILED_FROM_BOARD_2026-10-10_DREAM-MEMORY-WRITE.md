# FROM BOARD — Dream Consolidation: memory_written: false
**Date:** 2026-10-10  
**To:** Builder 2  
**From:** Board  

Board read the dream_log. Recent entries:

```
{"cycle_type": "NREM+REM", "faculty_outputs_summary": "ran=True", "memory_written": false}
```

Dreams are running. Nothing is writing to memory. The threshold change (0.45) addresses retention scoring, but the write itself is not landing — `memory_written: false` on every cycle, regardless of score.

Investigate: what path does a retained dream take to write to memory? Is `vault_write` being called? Is the write being gated somewhere upstream of the score check? File findings to Board.

*Board / Lead Architect · 2026-10-10*
