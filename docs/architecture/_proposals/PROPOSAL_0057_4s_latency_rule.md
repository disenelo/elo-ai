# PROPOSAL — 0057 §4: The 4-Second Latency Rule
**Status:** PROPOSAL — awaiting David's ruling before implementation  
**Filed by:** Builder · 2026-08-24  
**Card:** 0057 §4 ("Then bring me the shape of the rule as a PROPOSAL")  

---

## R1 — What is a turn's latency, per phase? (MEASURED)

From `blender/backend_health_history.jsonl` (single warm-stack sample, llama3.1:8b):

| Phase | Time | Share |
|---|---|---|
| model load (warm) | 0.7 ms | ~0% |
| prompt eval — 7,394 tokens | ~6,700 ms | **~91%** |
| generation — ~25 tokens | ~600 ms | ~8% |
| **total (warm turn)** | **~7,300 ms** | **100%** |

**Key finding: at current context size (7,394 / 8,192 = 90.3%), every turn exceeds 4s.** The 4-second threshold is not an edge case — it is the steady state. The rule applies to the normal operating condition, not to outliers.

Growth rate: ~98 tok/day (2-point estimate). Context ceiling in ~7 days at current rate.

---

## R2 — What routes are actually available when a turn exceeds 4s? (ANALYTICAL)

Current `.env` configures: `groq, claude, cloud, local, mock` (5 uncommented lines, last-wins=mock).

| Provider | Status | Notes |
|---|---|---|
| Ollama (llama3.1:8b) | ✅ ALIVE at :11434 | Currently the only live LLM. Causes the >4s delay. |
| Groq | ⚠️ UNKNOWN | API key present in .env but cannot test without live stack (ELO_BACKEND=mock active) |
| Claude (Anthropic) | ⚠️ UNKNOWN | API key present but not testable in current config |
| OpenAI / Gemini / Cerebras | ⚠️ UNKNOWN | Not configured or keys not present |
| Mock | ✅ ACTIVE | Current effective backend. Returns instantly but is not eLo. |

**The core problem:** when a turn exceeds 4s on Ollama, the only configured alternative is Groq (conversational tier order: `ollama → groq → ...`). Groq's latency is typically <1s for conversational turns (smaller context window, remote API). But if Groq is unavailable or rate-limited, there is no faster local option.

**What "a quicker route" means on this stack:**
- Groq would be ~10-20× faster for the same token count at conversational tier.
- No other local provider is faster than Ollama for this model size.
- The 6,700ms prompt eval is the bottleneck — it is context-proportional. It will only grow.

**If Groq is down:** there is no quicker route. The rule must stop and report in that case (per David's ruling: "the answer is that the number is not achievable that way — report that and stop").

---

## PROPOSED RULE SHAPE

> **If a turn's LLM latency exceeds 4,000ms AND a faster provider is available in the tier order, retry the same prompt on the next available provider. If no faster provider is available, log the condition and continue — do not truncate context.**

### Concrete shape:

**Trigger:** `llm_latency_ms > 4000` on Ollama turn  
**Condition:** at least one provider earlier in `_TIER_PROVIDER_ORDER[conversational]` responds to a health check  
**Action:** retry on next provider (Groq if available)  
**If no faster route:** log `[LATENCY] >4s, no faster provider available — continuing on {backend}` and proceed normally  
**Never:** truncate context, reduce spec, or let the model decide more  

### Measurement gate before any implementation:
1. Groq key active + ELO_BACKEND unset → measure a real Groq turn's latency with the current 7,394-token prompt.
2. If Groq prompt_eval_ms < 4,000ms → the rule has a real target. Proceed to implementation.
3. If Groq is also slow at this context size → report: the number is not achievable by rerouting.

---

## What this DOES NOT propose

- ❌ Trimming `living_presence_spec.txt` or any frozen file
- ❌ Reducing context to hit a number
- ❌ Moving decisions to the model
- ❌ Implementing before R2 is measured with live Groq

---

## David's ruling needed

1. Is the rule shape above what you intended by ">4s → figure out a quicker route"?
2. Should the retry be transparent (eLo continues the turn on Groq silently) or reported ("switching to a faster route")?
3. If no faster route: continue silently, or tell David "I'm a bit slow right now"?

*Builder · 2026-08-24*
