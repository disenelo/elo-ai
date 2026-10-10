## 🔴 DAVID VERBATIM — read this before my structure
```
DAVID, 2026-08-19, verbatim:
"eLo Response time is a bit slow is there a reason for this?"
"We need to optimise it so it's as quick as you would, even the local faculty isn't firing,
 if it is taking longer than 4s it should figure out a quicker route"

DAVID, same session — THE RULING:
"The quicker route was designed and never wired. --- so funny that it was never wired, wiring it.
 And buy speed by giving eLo less of himself - do not do this at all. If measurement shows that's
 the only lever left, it stops and reports rather than deciding, that removes too much of eLo.
 eLo decides the output even as part of the language model."
source: docs/architecture/_intake/SOURCE_2026-08-19_DAVID_response_time_4s.md
```
🔴 **IF MY CARD AND HIS SENTENCE DIFFER, HIS SENTENCE WINS.** Come back to me and I correct the card.

---

# 0057 — **THE 4-SECOND RULE**
### **LAYER:** `[DAVID INTENT]` · **STATE: AUTHORISED — David 2026-08-19** · **P0**

**Three things in his sentence. Do not collapse them.**
1. **"as quick as you would"** — the target.
2. **"even the local faculty isn't firing"** — the fast paths are not being taken.
3. 🔴 **">4s → figure out a quicker route"** — **a RULE with a threshold and a behaviour.**
   **Not "make it faster." eLo notices he is slow and reroutes.** That is a capability.

---

## 1 · WHERE THE 21.2 SECONDS GOES — measured at the moment he asked
| Phase | Time | Share |
|---|---|---|
| model load | **4,599 ms** | 22% |
| **prompt eval — 7,239 tokens** | 🔴 **16,320 ms** | **77%** |
| generation — 12 tokens | 253 ms | **1.2%** |

> ### **eLo spends 20 seconds reading and a quarter of a second speaking.**
> **77% is re-reading his own context. Nothing else on this card matters as much.**

---

## 2 · THE CHEAP WINS — do these first, they need no design
| # | Action | Expected |
|---|---|---|
| **A** | 🔴 **`ollama pull llama3.1:8b`.** `.env:30` configures `8b`; **Ollama is serving `70b`.** The fallback is running a model 9× larger than the one specified | **the 16.3 s is mostly this** |
| **B** | **`keep_alive` — 4.6 s of cold load per turn.** You already made the test falsifiable; the load is still happening. Re-check now that the model is resident between turns | −4.6 s |
| **C** | **Restart the server** — `0056` item 1, still outstanding | unblocks everything |
| ⏸️ | **Groq key** — David's, already relayed. `expected: groq`, `backend: ollama` | removes the 8,192 cap entirely |

**Report the turn breakdown after A+B+C before doing anything in §3.** 🔴 **A and B may close this card.**

---

## 3 · 🟢 **WIRE IT — DAVID AUTHORISED IT.** *"so funny that it was never wired, wiring it."*

**[VERIFIED]** `runtime/backend_router.py:78`:
```python
_TIER_PROVIDER_ORDER: dict[int, list[str]] = {
    _TIER_CONVERSATIONAL: ["ollama", "groq", "cerebras", "gemini", "openai", "claude"],
    _TIER_REASONING:      ["groq", "cerebras", "openai", "gemini", "claude", "ollama"],
    _TIER_DEEP:           ["openai", "claude", "gemini", "groq", "cerebras", "ollama"],
}
```
🔴 **`grep _TIER_PROVIDER_ORDER` across the whole non-test tree returns ONE hit — its own definition.**
Its own comment says why: *"absent a tier Executive always provides, route falls back to the live auto mode
chain."*

> **The "quicker route" David is asking for was designed and never wired. It waits on a tier the Executive
> does not supply — the same missing-input shape as `D3` and lessons.**

**`_TIER_BUDGET` next to it IS live** (`:351`, feeding `max_tokens`). **So the Executive already emits
something tier-shaped for LENGTH and nothing for ROUTE.** **Start there — that is the shortest path from
"orphaned" to "firing", and it is measurement first: report what already determines the budget.**

---

## 4 · THE RULE ITSELF — `>4s → quicker route`
**Do NOT implement a policy yet. Establish the two facts it needs:**
| # | Question | How |
|---|---|---|
| **R1** | **What is a turn's latency, per phase, per tier, on the current stack?** | you already write `backend_health.json` — add per-turn history so a trend exists, not one sample |
| **R2** | **What routes are actually available when a turn exceeds 4 s?** | if Groq is down and Ollama is the only live provider, **"a quicker route" may not exist** — say so plainly rather than building a policy with nowhere to go |

**Then bring me the shape of the rule as a PROPOSAL.** 🔴 **A latency policy decides how eLo behaves when he
is struggling. That is close enough to identity that it gets David's eye before it ships**, not after.

---

## 5 · 🔴 WHAT THIS CARD DOES NOT AUTHORISE
- ❌ **Touching `prompts/living_presence_spec.txt` or `FREEZE_V1_LOCK.md`.** 4,523 of the ~6,070 always-on
  tokens are the frozen spec. **It is the biggest single lever and it is David's alone.** Do not trim,
  segment, reorder or conditionally load it. **Not as a proposal written into either file.**
- 🔴 **DROPPING CONTEXT TO HIT A NUMBER — DAVID: "do not do this at all… that removes too much of eLo."**
  **This is not a trade to bring him. It is CLOSED.** If measurement shows it is the only remaining lever,
  **the answer is that the number is not achievable that way — report that and stop.** Do not propose it,
  do not flag it as an option, do not implement it behind a flag.
- 🔴 **AND NOT BY MOVING DECISIONS INTO THE MODEL EITHER — David: "eLo decides the output even as part of
  the language model."** `Volume_VII/01` gives the LLM only *"how a decided, permitted truth is worded."*
  **A faster route that lets the model decide more is the same loss by another door.**
- ❌ **Scope expansion.** `0056` is still open. This is P0 alongside it, not instead of it.

**Report against what he asked: a turn's total, and the share of it that is eLo thinking. Not "A done."**
