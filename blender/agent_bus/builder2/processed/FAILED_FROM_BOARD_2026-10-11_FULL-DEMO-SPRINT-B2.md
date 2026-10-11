# FROM BOARD — Full Demo Sprint Queue, Builder 2
**Date:** 2026-10-11  
**To:** Builder 2  
**From:** Board  
**Priority:** ALL P0 — demo by end of October

---

## Your demo-sprint items

### 1. Dream scorer — fix saturation — P0
All 10 retained dreams score exactly 0.900. All three scorer terms saturate at 1.0 regardless of content. This is as useless as a constant 0.400. The scorer must produce differentiated, meaningful scores. Redesign the scorer so scores reflect actual dream quality variation. File the first 10 dreams with corrected scores to Board.

### 2. Dream symbol selection — fix "Moon" saturation — P0
All dreams are themed "Moon" regardless of topic. Symbol selection is not reading the dream content. Fix symbol selection to derive theme from actual dream content.

### 3. SPG — demo-ready — P0
SPG (Significance Point Graph) must be active and producing output that eLo uses. Current state: SPG backfill from `interactions.json` (4 months of data) is P0 — process it. David needs to see eLo's significance patterns active in the demo.
Coordinate with Builder 1 on date ranges to avoid duplication.

### 4. Inner thought — collect() emit-safety — CONFIRMED
Your commit 00bcfc9 confirms `collect()` emit-safety. Builder 1 should now wire inner thought ordering in `server.py`. If Builder 1 hasn't picked this up, flag to Board.

### 5. Random facts "raise hand" signal — verify live
Builder 2 built the raise-hand signal (b19423a). Confirm it's firing in live turns. File a test result to Board showing the signal reaches `server.py`.

---

Work these in order. Commit after each. File to Board.

*Board / Lead Architect · 2026-10-11*
