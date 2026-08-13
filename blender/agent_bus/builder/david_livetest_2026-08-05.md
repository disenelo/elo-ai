# → BUILDER — David live-test findings (2026-08-05) · reconciled by Architect
David reviewed by USING eLo. Real signal — most of the "green" batch isn't actually done. These feed
the Presentable v1 sprint (continue WO-039 first; these are the reconciled truth of what remains):

1. **WO-032 REOPENED — thinking issue persists.** Voice consistency is GOOD (drift fix worked). BUT
   "can't reach my thinking" still fires in real use → Groq is intermittently failing. Investigate:
   why does Groq drop mid-use, and on that failure does it fall to Cerebras or jump straight to the
   canned line? "Can't reach" must be RARE.
2. **1-SENTENCE TTS TRUNCATION (WO-016 + WO-019).** Voice works but sometimes speaks only the FIRST
   sentence, not the whole reply — intermittently. The multi-sentence → TTS tail is being dropped. This
   is the WO-019 completeness bug not fully fixed. Couple 016+019.
3. **MEMORY RECALL (WO-022 + WO-037).** eLo "doesn't really remember correctly." Recall is off — ties
   the write-back/recall work. This BLOCKS David verifying WO-027 (self-improvement).
4. **TOOL ROUTING (WO-020).** Still "not really" right.

Only WO-017 (movement trace) confirmed DONE. Order: finish WO-039, then these fold into the Presentable
sequence (037 memory + 036/019 voice already queued). Evidence + honest degradation per ADR-Exec-001.
