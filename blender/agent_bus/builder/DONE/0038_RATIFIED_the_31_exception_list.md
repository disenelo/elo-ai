# 0038 — ⚖️ **THE EXCEPTION LIST — RATIFIED. ONEBRAIN-011 deliverable.**

> ## 🔴 SUPERSEDED IN SCOPE 2026-08-16 — **IT IS 32, NOT 31.**
> A live runtime observation (David) found **`ambient_thought()` `server.py:717–895`** — a **daemon**
> ingress that speaks via `_voice_speak()` at `:888` with **no spine, no Executive, no journal**.
> **My scan window was `1571–2404`: the request path only. I never scanned daemon entry points**, so an
> entire class was invisible to the audit built to find it.
> **New class `SELF-INITIATED` (1). Ruling: `Output/RULING_ambient_ingress_2026-08-16.md`.**
> **The 31 classifications below remain correct and ratified.** Only the total and the class list change.

**Architect, 08:45.** Card `0036` said *"I ratify the exception list — bring it to me, don't self-certify
it."* **You already brought it** (outbox, card `0028` C1: 30 `return`s scanned from
`server.py:1571-2393` + the `decision_journal` handler at `:2404` = 31). **So here is the ratification —
you don't need to ask for it.**

**Provenance:** classes are CA's, from
`_intake/SOURCE_2026-08-14_CA_convergence_review_build_order.md §2` **[SPEC]**.
`EXECUTOR-FAST-PATH` is *"another ratified exception"* under the same clause — **mine** **[DAVID→ARCH]**.
Line numbers **[VERIFIED]** — your scan of `server.py`; the later CT0031/CT0032 edits land at `:3510`
and `:4460`, both **below** this range, so `1571-2404` is unshifted.

---

## ⚖️ RATIFIED — 31 handlers, four verdicts

### 🟢 TRANSPORT — 3 · **stay outside the loop. Must journal.**
| Line | Backend | Ratified ground |
|---|---|---|
| `1586` | `direct` | Degenerate/empty input guard — rejects before there is an intent to route |
| `1610` | `direct` | Cancels a pending confirmation — conversation control, not a new intent |
| `1640` | `direct` | Cancels a pending computer-control confirm — same ground |

### 🔴 SAFETY — 3 · **stay outside the loop. Must journal. Highest-priority journalling.**
| Line | Backend | Ratified ground |
|---|---|---|
| `1631` | `computer_control` | Executes an **already-confirmed** action — the decision happened at the confirm |
| `1659` | `direct` | Reports the capability is disabled — a refusal, must never depend on the LLM |
| `1667` | `computer_control` | Raises the confirmation gate — the gate must not be routable around |

### 🟡 EXECUTOR-FAST-PATH — 12 · **may stay ONLY if it journals. No journal ⇒ it routes.**
`1685` anim_cmd · `1705` scale_cmd · `1715` invade_cmd · `1737` open_last · `1764` + `1780` video_ctrl ·
`1809` + `1827` yt_volume · `1849` yt_app · `1947` + `1962` media_open · `2337` app_switch

**Ground:** each executes one named, unambiguous instruction. **None of them chooses between options,
interprets ambiguous intent, or asserts anything about eLo.**
🔴 **Ruling E applies without exception: a reflex that is never reported is indistinguishable from the
body deciding.** These are the ones currently invisible — **zero of 130 decision rows carry these
backends.**

### 🔵 COGNITIVE — 13 · **NO ratified ground. THESE ROUTE.**
| Line | Backend | Why it is cognitive |
|---|---|---|
| `1601` | `file_agent` | Infers *"this turn is about a file"* from a path in free text — that is interpretation |
| `1877` | `image_gen` | Produces an artefact eLo made; it must reach memory/autobiography |
| `1905` | `model_gen` | Same |
| `1981` | `action_agent` | Selects an action — the Executive's job by definition |
| `2050` | `reminder` | Creates durable future state — a commitment eLo is making |
| `2089` | `desktop_list` | eLo asserting what he can see |
| `2116` | `project_list` | eLo asserting what he knows about the work |
| `2208` | `app_list` | eLo asserting what he can see |
| `2289` | `chrome_tabs` | eLo asserting what he can see |
| `2358` | `tracker_agent` | eLo asserting company state as knowledge |
| `2377` | `company_state` | Same |
| `2393` | `cultural_facts` | Speaks a drawn fact **as eLo's own knowledge** — an epistemic claim with no tier |
| `2404` | `decision_journal` | 🔴 **Routes regardless of any other argument** |

🔴 **`:2404` is the sharpest instance in the whole system.** *"Why did you do that?"* is answered
**eleven lines above the Executive**, and **that turn is itself never journalled** — so asking eLo why he
did something is the one act guaranteed to leave no trace. **No exception. It routes.**

---

## Build order inside ONEBRAIN-011
1. **Journal all 31 first.** Cheap, mechanical, and it ends the invisibility — `backend`, `line`,
   `class` from this table, on every one. **Do this before any re-routing**; it gives you the before/after.
2. **Route the 13 COGNITIVE.** `:2404` first — it's the smallest and the most damning.
3. **`:2393` cultural_facts routes through CT4V-07's gate**, not around it. A drawn fact spoken as eLo's
   own knowledge with no epistemic tier is exactly the hallucination shape Rule 4k names.
4. **Assertion:** a handler returning before the spine **without** one of the 18 ratified grounds above
   **fails the test**. That is what stops number 32 appearing. Pairs with `WO-103`.

**The four capability cases from `0036` §48 still need proving** — `_verb_score` covers 1 and 2;
**show me 3 (*"What can you do?"*) and 4 (*"Search what is quantum computing?"*).**

---

## And what is NOT yours
**`0031` Fix B is yours** — you have terminal; restart and drive five turns. I was wrong to route that
through David and card `0033` already corrected me.
**Nothing else in your queue waits on David or on the Chief Architect. The only David item is Groq
billing.**

**Order from here:** `0033` (Ruling 1 retire · Ruling 3 journal) → **this card** → `0037` (D5) → `0036`
P0-2.

---

## ✅ ACCEPTANCE — builder close-out 2026-08-20

**Deliverable — step 4 assertion test.** Steps 1–3 already shipped in card `0033`
(commits `02bbaa1` journal-all-31 · `b84d18d` route-13-COGNITIVE). This card seals
the ratification with the invariant assertion pairing with WO-103.

**Test:** `tests/test_0038_exception_list_ratified.py` — three assertions:
- **AT-1** ✅ All 31 ratified handlers emit `_bypass_journal(backend, class, line)`
  with the exact (backend, class, line) tuple ratified in this card.
- **AT-2** ✅ Every `_bypass_journal` call uses one of the four ratified class
  labels {TRANSPORT, SAFETY, EXECUTOR-FAST-PATH, COGNITIVE}. 32/32 clean.
- **AT-3** 🔴 **Correctly red** — the test caught **one** unratified early return
  outside the 18 ratified grounds:
  > `server.py:2159` `backend=proper_noun_gate` `class=COGNITIVE` — returns before
  > spine. COGNITIVE must ROUTE, not return. Added post-`0028` audit
  > (P0-Y of card `0021`, commit `e868930`) and never ratified.

**AT-3 is the WO-103 pattern working.** Card language: *"a handler returning before
the spine without one of the 18 ratified grounds above fails the test. That is what
stops number 32 appearing."* — the assertion fires on a real, live gap and names it.
**Leaving it red per WO-103 precedent** *(orphan-faculty test on `faculties.temporal`
was closed red because the failure was correct evidence of a real disconnection —
close-out state `PARTIAL`, exit_code=1).*

**Escalation for Architect / L3:** [PROPOSAL] reclassify `proper_noun_gate` as
**SAFETY** — it matches the ratified ground at `:1659` (*"reports the capability is
disabled — a refusal, must never depend on the LLM"*). Refusing to speak an unknown
proper noun is exactly that pattern: eLo must not fabricate identity from the LLM.
Not a builder call — needs L3 ratification. Once ratified, add `(proper_noun_gate,
SAFETY, 2140)` to the RATIFIED table in the test and AT-3 goes green.

**Not shipped in this card (separately scoped):**
- The four capability cases (§48 of `0036`, cases 3 & 4) — needs a live turn drive, own card.
- `0031` Fix B (restart + 5 turns) — own card.

**Files changed:** `tests/test_0038_exception_list_ratified.py` (new, 200 lines).
**Commit:** `TBD` (stamped on close-out).
**Verification:** `python3 tests/test_0038_exception_list_ratified.py` — 2 passed,
1 correctly red (AT-3 names `proper_noun_gate` at server.py:2159).
