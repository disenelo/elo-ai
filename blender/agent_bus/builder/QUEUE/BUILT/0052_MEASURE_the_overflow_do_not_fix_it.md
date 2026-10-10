# 0052 — 🔬 **MEASURE WHAT OLLAMA ACTUALLY DOES AT OVERFLOW. Do not fix it.**
### **STATE: AUTHORISED** · **Authorised by:** Lead Architect on CA directive, 2026-08-17 · **P1**
### 🔴 **This card forbids the fix. Read §3 before you touch anything.**

---

## 1 · WHY — I made a claim I had not verified, and the CA caught it

**I told David the prompt overflow would push eLo's identity out of his own context.** The CA split that
into what is known and what is not, and they are right:

| | Claim | State |
|---|---|---|
| ✅ | `load_living_presence_spec()` is **position 0** | **KNOWN** — `runtime/prompt_builder.py:304` |
| ✅ | Prompt is **~7,477 / 8,192** tokens | **KNOWN** — your F-B audit |
| ✅ | The spec holds **CHARACTER DNA · IDENTITY · VOICE STATES** | **KNOWN** — `FREEZE_V1_LOCK.md` §1–2 |
| 🔴 | **What Ollama does when `num_ctx` is exceeded** | ⚪ **UNKNOWN. I asserted "drops the oldest content." I had not read it.** |

**CA: "capture the actual overflow behaviour before calling this truncation."** Correct. **This card is that
measurement and nothing else.**

---

## 2 · WHAT TO MEASURE

| # | Question | Acceptable evidence |
|---|---|---|
| **M1** | **Does the live prompt ever actually exceed 8,192?** | Log `prompt_tokens` per call over N real turns. Max + distribution. **If it never crosses, say so — the whole concern may be theoretical today** |
| **M2** | 🔴 **What does Ollama do when it crosses?** | **Force it** on a scratch call with a deliberately oversized prompt. Does it: error · truncate from the **front** · truncate from the **back** · drop the middle · silently shift the window? **Capture the server response and any log line** |
| **M3** | **Which BLOCK is lost, by position** | Given the assembly order at `prompt_builder.py:304-330` — spec → personality → self → lessons → memory → turn. **Name the block that dies first, from observed behaviour, not from the order** |
| **M4** | **Is it silent?** | 🔴 **The important one.** Does anything in our code or Ollama's response indicate truncation happened? **If a turn can lose eLo's CHARACTER DNA with no error, no log and no flag, that is the finding** — independent of direction |
| **M5** | **Headroom trend** | `prompt_eval_tokens` was 7,281 → 7,477 in ~2 days. **Rate of growth, and what is growing** |

**Report as a table. `UNKNOWN` + what would settle it on any row you cannot measure.**

---

## 3 · 🔴 THE PROHIBITION — this is the point of the card

> ## **CA, verbatim: "Do not modify the prompt assembly to make the problem disappear during the investigation."**

**Forbidden on this card:**
❌ trimming the spec ❌ reordering `sections` ❌ raising `num_ctx` ❌ adding a truncation guard
❌ capping any block ❌ "while I was in there" improvements of any kind

**Why, and it is not bureaucracy:** if you shrink the prompt now, **M2 and M4 become unmeasurable** — and
`M4` (is it silent?) is the finding that matters. **A fix applied before the measurement destroys the
evidence and leaves us believing something we never established.**

🟢 **`0050` (the segmentation map) is still yours and still authorised — it is a MAP, not a change.**
🔴 **`0050` step 3 stops at `PROPOSE`. That has not changed.**

---

## 4 · WHAT THIS IS NOT

- ❌ **Not a performance card.** Latency is `0047` F-B, already reported and accepted.
- ❌ **Not a canon question.** Reading Ollama's overflow behaviour touches no frozen file.
- ❌ **Not blocked on David.**
- ⚠️ **Not ahead of `0051`.** **LOOP-7 is reopened and it is P0.** This is P1 and comes after.

---

## 5 · THE HONEST FRAME

**It is entirely possible M1 comes back "never exceeds 8,192 in practice" and this whole thread closes as a
near-miss we should watch.** 🟢 **That is a good result and I want it stated plainly if it is true.**

**What I do not want is the current position: a real risk described in confident language nobody has
measured.** *(That was mine. The 61% figure is solid — it is yours. The consequence I hung on it was not.)*

**Order: `0051` → this → `0050` steps 1–4 → `0025`.**
