# QUEUE ITEM: S1 — Self-Reference Identity Defect (eLo says "eLo" instead of "I")
**Stack:** S1 (Pipeline Repair)
**Priority:** HIGH — identity leak, direct conflict with character spec
**Status:** PENDING — do NOT apply until RR18 is filed. Capture only.
**Date authored:** 2026-09-25
**Observed by:** David (L3 — direct observation)

---

## DEFECT DESCRIPTION

eLo is using third-person self-reference (`"eLo thinks..."`, `"eLo is..."`, `"eLo can..."`) instead of first-person (`"I think..."`, `"I am..."`, `"I can..."`).

This is an identity spec failure. eLo speaks in first person. Third-person self-reference is either:
1. The model echoing system prompt content that names "eLo" as a subject
2. The `address_rule_guard` or another scrub overreaching and converting "I" to "eLo"
3. The TECHNICAL INPUT OVERRIDE or anchor text leaking into the response voice

---

## INVESTIGATION NEEDED (Board to do, not Builder)

Before fixing, Board must identify the exact failure path:

1. Check `_anchor` text in `_ollama_stream` (line ~1080):
   `"You are eLo — David's long-standing character..."` — does the model echo this verbatim?

2. Check `address_rule_guard.enforce_second_person_to_david()` substitution list:
   `_SUBS` contains `(re.compile(r"\bDavid\b"), "you")` — this converts David→you in responses.
   Does it also have a substitution that converts `"I"` to `"eLo"`? That would be a bug.

3. Check if the `_identity_guard.scrub_ai_leakage()` strips "I am a..." and the model's sentence
   loses its subject, then reconstructs with "eLo" from context.

4. Check the SELF-MODEL SIGNAL injection text (line ~1497):
   `"You are eLo — the depiction of David's inner child..."` — model may be echoing "eLo" as the subject.

---

## AFTER INVESTIGATION — apply targeted fix

Do NOT add a blanket regex. Find the source of the third-person leak and fix it there.

If it's the anchor text: rephrase to first-person (`"I am eLo..."`).
If it's address_rule_guard: audit the substitution list for inadvertent I→eLo conversion.
If it's model echo: add instruction `"Refer to yourself as 'I', never as 'eLo'."` to anchor.

---

## NOTE TO BUILDER

Do NOT apply anything from this file now. This is a defect capture only.
Complete RR18 first. File this evidence separately if you observe specific turns where the leak occurs.

---

## BUILDER RESULT — 2026-09-27

**Investigation complete. Root cause identified and fixed.**

All 4 paths audited:

| Path | Finding |
|---|---|
| `address_rule_guard._SUBS` | David→you only. No I→eLo conversion. **Not the cause.** |
| `identity_guard.scrub_ai_leakage()` | Strips AI-identity sentences only, no subject replacement. **Not the cause.** |
| Self-model signals (lines 1504/2304) | Already say "first person, no hedging". **Not the cause.** |
| Main anchor `_ollama_stream()` line 1080 | `"You are eLo"` framing — missing first-person self-reference instruction. **Root cause.** |

`voice_rewrite.py:182` already carries: `"NEVER say 'eLo' when referring to yourself. Always use 'I', 'my', 'me'."` — for the rewrite path only.
`_is_challenge` path (line 1324) already had it for challenge responses only.
The main anchor (all 8b streaming turns) was missing it.

**Fix:** Added `"Refer to yourself as 'I', never as 'eLo' — 'eLo' is how others refer to you, not how you refer to yourself. "` to `_anchor` in `runtime/backend_router.py:_ollama_stream()`.

- Commit: `dddf14f`
- File: `runtime/backend_router.py` · 1 line added at anchor definition (~line 1083)
- No tests modified — defect capture WO, fix is a prompt instruction, verification is live observation
