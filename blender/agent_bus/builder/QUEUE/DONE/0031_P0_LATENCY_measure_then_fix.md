# 0031 — 🔴 **P0 · RESPONSE LATENCY: 20-30s per turn.** Measure → fix → re-measure.

**Seat:** builder · **Priority:** **P0 — this shapes every live test David runs** · **Gate?** none
**Not a bug report. A plan with targets.**

---

# STEP 1 · INSTRUMENT FIRST — do not fix blind (15 min)
We are guessing at the split. Ollama returns the numbers; we just don't read them.

`/api/chat` returns these fields — **log all four every turn:**
```
load_duration        ← model coming off disk (cold load)
prompt_eval_count    ← tokens actually processed  ⚠️ compare to what we sent
prompt_eval_duration ← PREFILL cost
eval_count / eval_duration ← GENERATION cost
```
**Add them to `backend_health.json` and log at INFO.**

**`prompt_eval_count` is the critical one** — if it's materially lower than the tokens we sent, **the
prompt is being truncated** and the identity/world blocks never reach the model. That single number
resolves the `num_ctx` UNKNOWN without guesswork.

**Report the four numbers for 5 turns before changing anything.**

---

# STEP 2 · THE FOUR FIXES — ordered by effect ÷ effort

### Fix A · `keep_alive` — **one line, kills cold loads**
`_ollama_call` (`backend_router.py:302-309`) sets no `keep_alive`. **Ollama's default unloads after 5
minutes idle** — so a turn after any pause pays a full 8B load from disk, **and loses the KV cache with
it.**
```python
"keep_alive": "30m",
```
**Expected: removes several seconds from every post-idle turn, and preserves the prefix cache between
turns (see Fix D).** Measure `load_duration` before/after — it should go to ~0 on turn 2+.

### Fix B · Streaming on the local path — **the biggest *perceived* win**
`backend_router.py:308` sets `"stream": False`. Streaming exists (`route_streaming:780`,
`_openai_stream:357`) and is **OpenAI-only.** WO-026's response-speed work never covered Ollama.

**With Groq down, there is no streaming at all** — David waits for all 256 tokens before one character
appears.
**Build:** an `_ollama_stream` mirroring `_openai_stream`, wired into `route_streaming`'s fallback chain.
**Target: time-to-first-token under 2s.** Total time barely changes; the *experience* changes completely.
**Measure TTFT explicitly — it is the number that matters here, not total duration.**

### Fix C · `num_ctx` — **stops silent truncation**
Never set (`:307`). Default is commonly 4096. **`living_presence_spec.txt` alone is 17,842 chars ≈ 4,460
tokens** — it overflows the default *by itself*, before the **fifteen** appended blocks.

⚠️ **If Step 1 shows `prompt_eval_count` < tokens sent, this is why P0-X didn't fix the name bug** — the
identity block is appended near the end and would be the first thing dropped.
```python
"num_ctx": 8192,
```
**Costs memory; measure `prompt_eval_duration` before/after.** If 8192 is too slow on his machine, that's
evidence for Fix D rather than a reason to leave it truncating.

### Fix D · Cut the prompt — **the real fix, and the one that needs judgement**
4,460 tokens of static spec + 15 dynamic blocks, re-sent every turn.

**Prefix caching only helps while the leading bytes are byte-identical and the model stays resident.**
Fix A protects residency. **Your job is to protect the prefix:**
1. **Audit block order.** Anything that changes per turn must come **after** everything static. If a
   dynamic block is currently emitted *before* a static one, the cache breaks at that point every turn.
2. **Then reduce.** 15 blocks is too many. Which are needed on *every* turn versus only when relevant?
   **`[CAPABILITIES]` and `[WORLD_KNOWLEDGE]` are obvious candidates for conditional injection.**
3. **Report the token count per block** so we can see where it actually goes.

🔴 **Constraint — `prompts/` is FREEZE_V1_LOCK'd.** Restructuring the spec itself is **not** in scope.
D is about **order and conditional inclusion of the appended blocks**, not editing the spec. If you
conclude the spec must shrink, **raise it — don't do it.**

---

# STEP 3 · RE-MEASURE AND REPORT
| Metric | Now | Target |
|---|---|---|
| Time to first token | = full generation (~20-30s) | **< 2s** |
| `load_duration` turn 2+ | unknown, suspected multi-second | **~0** |
| `prompt_eval_count` vs sent | **unknown — suspected truncating** | **equal** |
| Total turn | 20-30s | measurable, honest number |

**Report the four Ollama numbers before and after. Not "it feels faster."**

---

## Why this is P0 despite being infrastructure
Every live test David runs goes through this. **A 25-second wait with no streaming makes a working eLo
feel broken**, and it has been quietly shaping his read of every other defect tonight.

And if Step 1 shows truncation, **it partially invalidates tonight's identity and world-knowledge fixes** —
we'd have been debugging content that never reached the model.

**Sequence:** Step 1 → Fix A → Fix B → Fix C → measure → then Fix D with numbers in hand.
**Do this before `0030` C2** — if the prompt is truncating, C2's acceptance test can't be trusted either.
