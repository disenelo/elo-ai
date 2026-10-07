**WO:** COG-POOL-RETEST · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
Confirm whether COG-008/010/012/017 pass or remain red after WO-VAULT-POOL-FIX-001 landed.

## Result
- commit: (no new code — read-only)
- test: no pytest tests exist for COG-008/010/012/017
- notes: `python3 -m pytest tests/ -k "cog008 or cog010 or cog012 or cog017..."` → 0 selected.
  These are live server acceptance tests, not pytest unit tests. Static analysis evidence
  was already filed on 2026-10-05:
  
  `engineering/evidence/CAP/COG/WO-CAP-COG-008_012_010_017_fix_verification.md`
  
  That file confirms:
  - Root cause was voice_rewrite._needs_rewrite() collapsing factual content to short affirmations
  - Fix: content-preservation guard at runtime/voice_rewrite.py:257
    - if len(cleaned) > 100 AND len(stripped_rewrite) < 25% of original → rewrite rejected
  - Static analysis of all four confirmed guard=True → REWRITE REJECTED ✅
  
  COG-008 (engineering): 365→13 chars blocked ✅
  COG-010 (visual identity): 320→38 chars blocked ✅  
  COG-012 (self-description): 280→32 chars blocked ✅
  COG-017 (emotional support): 350→27 chars blocked ✅
  
  Live re-test with Ollama recommended for BOARD VERIFIED status. Blocked by live server
  rule during active David session. Static analysis confirms unblocked.
