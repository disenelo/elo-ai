# WO-CAP-COG-001 — Result: Language Understanding

**Date:** 2026-09-20
**WO:** WO-CAP-COG-001
**Source:** `docs/architecture/_intake/SOURCE_2026-09-19_eLo_KEY_CAPABILITY_MAP.md §1`
**Seat:** Builder
**Status:** CLOSED — LIVE VERIFIED 27/29 PASS

---

## What was done

Fixed four blocking issues and ran 7 multi-turn contextual evidence sessions covering all 29 source §1 language types.

### Files changed

| File | Change |
|---|---|
| `tools/system_agent.py` | Word-count guard in `detect()` — inputs >10 words skip risky verb patterns; only unambiguous actions fire on long inputs |
| `runtime/backend_router.py` | SARCASM SIGNAL + input rewrite in `_ollama_stream()` and `route_streaming()` |
| `runtime/backend_router.py` | TECHNICAL SPEC SIGNAL in both paths — formal/academic language detection |
| `runtime/backend_router.py` | POETIC/METAPHOR SIGNAL in both paths — creative metaphor detection |
| `engineering/evidence/CAP/COG/WO-CAP-COG-001_evidence.md` | Full evidence file |

### Root causes fixed

1. **Slang routing bug (`direct+system_gate`)** — `_SYSTEM_INTENTS` `close` pattern matched "not even close to" in natural speech. Fix: word-count guard skips verb patterns on inputs >10 words.

2. **Sarcasm blind** — model took positive surface words at face value. Fix: dual-regex detection + `_ollama_user_input` rewrite strips the irony and presents actual meaning.

3. **Academic/formal spec ignored** — model read specification language as emotional communication. Fix: `_TECH_SPEC_RE` detection injects TECHNICAL SPEC SIGNAL.

4. **Poetic/metaphor rejected** — model pushed back on creative metaphors as bad suggestions. Fix: `_POETIC_RE` detection injects POETIC/METAPHOR SIGNAL.

---

## Source §1 coverage — all 29 language types

| Language type | Verdict |
|---|---|
| English | ✅ PASS |
| British English | ✅ PASS |
| American English | ✅ PASS |
| regional English | ✅ PASS |
| slang | ✅ PASS |
| street language | ✅ PASS |
| informal speech | ✅ PASS |
| formal speech | ✅ PASS |
| technical language | ✅ PASS |
| academic language | ✅ PASS |
| poetic language | ✅ PASS |
| metaphor | ✅ PASS |
| analogy | ✅ PASS |
| sarcasm | ✅ PASS |
| irony | ✅ PASS |
| humour | ⚠️ PARTIAL |
| understatement | ✅ PASS |
| exaggeration | ✅ PASS |
| ambiguity | ✅ PASS |
| implication | ✅ PASS |
| euphemism | ⚠️ PARTIAL |
| idioms | ✅ PASS |
| cultural references | ✅ PASS |
| abbreviations | ✅ PASS |
| acronyms | ✅ PASS |
| misspellings | ✅ PASS |
| speech-to-text errors | ✅ PASS |
| fragmented sentences | ✅ PASS |
| stream-of-consciousness | ✅ PASS |

**27/29 PASS · 2/29 PARTIAL · 0/29 FAIL**

PARTIAL: humour (response flat but register understood), euphemism (caught but generic). Not blocking.

---

## Full evidence

`engineering/evidence/CAP/COG/WO-CAP-COG-001_evidence.md`

---

## Status

LIVE VERIFIED. WO-CAP-COG-001: CLOSED.

*Builder · 2026-09-20*
