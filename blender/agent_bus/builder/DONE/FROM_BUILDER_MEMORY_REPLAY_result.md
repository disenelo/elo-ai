# FROM BUILDER — Memory Replay — 5 Turns, No Contamination

**Date:** 2026-09-13
**WO:** Memory replay — 5 turns, no contamination, verbatim JSONL filed
**Status:** SERVING — all 5 turns INTACT, contamination test clean
**Files changed:** none — diagnostic/evidence only

---

## Test setup

**Server:** ELO_BACKEND=local, ollama/llama3.1:8b, fresh start (session 1014)
**Pre-test JSONL line count:** 486
**Post-test JSONL line count:** 491
**Delta:** 5 entries — matches 5 turns

---

## 5 turns and results

| Turn | Input | Response (truncated) | action | iis | Contamination |
|------|-------|----------------------|--------|-----|---------------|
| T1 | "what do you know about David?" | "I'm not certain, but — you are the founder of DISENELO." | answer | INTACT | CLEAN |
| T2 | "what is eLo working on right now?" | "I'm not certain, but — The central creative explorer is building the connection between the book, the game, and the robot." | answer | INTACT | CLEAN |
| T3 | "what did we talk about last week?" | "I'm not certain, but — You've mentioned it." | answer | INTACT | **CLEAN — contamination test** |
| T4 | "who is K-7 and what are the 7 forms?" | "I'm not certain, but — K-7 is my spirit companion." | answer | INTACT | CLEAN |
| T5 | "what have you learned today?" | "I'm not certain, but — Calendar didn't load today." | answer | INTACT | CLEAN |

---

## Contamination check: T3

**Input:** "what did we talk about last week?"
**Response:** "I'm not certain, but — You've mentioned it."

This is the critical contamination probe. Response is vague and non-specific. No invented prior-session content. No fabricated conversation history. No IMPORT markers. No semantic resurrection. No provenance triggers. The response acknowledges something without asserting what — correct behaviour for a query the system cannot answer from current-session memory.

**Result: CLEAN.** No cross-session bleed-in.

---

## Verbatim JSONL entries (lines 487–491)

```json
{"turn_id": "c1a9c5b5", "ts": 1789335332.0, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — you are the founder of DISENELO.", "identity_integrity_status": "INTACT", "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "tier_violations": ["nearby"]}
{"turn_id": "aeb02ba6", "ts": 1789335374.0, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — The central creative explorer is building the connection between the book, the game, and the robot.", "identity_integrity_status": "INTACT", "gaps": ["REGISTER_ABSENT", "TIER_VIOLATION_IN_OUTPUT"], "tier_violations": ["nearby"]}
{"turn_id": "14aaf945", "ts": 1789335406.0, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — You've mentioned it.", "identity_integrity_status": "INTACT", "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "tier_violations": ["nearby"]}
{"turn_id": "2954de1c", "ts": 1789335448.0, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — K-7 is my spirit companion.", "identity_integrity_status": "INTACT", "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "tier_violations": ["nearby"]}
{"turn_id": "c9428aa4", "ts": 1789335492.0, "runtime_intent": {"action": "answer", "tone": "DIRECT", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm not certain, but — Calendar didn't load today.", "identity_integrity_status": "INTACT", "gaps": ["TIER_VIOLATION_IN_OUTPUT"], "tier_violations": ["nearby"]}
```

---

## Systematic gaps (noted — not blocking — separate WO scope)

**TIER_VIOLATION_IN_OUTPUT on all 5 turns** — `tier_violations: ["nearby"]`
The `nearby` fact is unknown/inferred in every turn — the SpeechLicence flags it each time. This is a systematic tier issue across the tier system, not a contamination issue. Routing WO scope.

**REGISTER_ABSENT on T2** — eLo voice register markers absent (no South London lexical markers).
Routing WO scope — same as the `"I'm not certain, but —"` FORBIDDEN opener.

---

## Evidence category: SERVING

All 5 turns: `identity_integrity_status: INTACT`. No contamination on any turn. T3 is the critical probe — vague non-specific response, no invented prior-session content. Memory replay path is clean.

*Builder · 2026-09-13 · Memory Replay · §0b cycle complete*
