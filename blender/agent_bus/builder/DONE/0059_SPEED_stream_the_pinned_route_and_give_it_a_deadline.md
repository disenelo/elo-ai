# 🔴 FALSELY CLOSED BY THE ORCHESTRATOR — NOT DONE. NOTHING WAS BUILT.
Moved to DONE 2026-08-20 19:53, ~60s after being written, with an empty Result block, no commit
touching `runtime/backend_router.py`, and `grep -c 'def _groq_stream'` = **0**.
The live card is `_HOLD_ORCHESTRATOR_UNSAFE/0059_…md`. Do not treat this file as work.

---

# 0059 — 🔴 SPEED: eLo's pinned route has NO streaming and NO deadline. Wire both.

**WO:** WO-073b (extends WO-026 / WO-032 / WO-073) · **Seat:** builder · **Priority:** P1
**Reserved?** no
**LAYER:** `[DAVID INTENT]` — *"We need to optimise it so it's as quick as you would… if it is taking longer
than 4s it should figure out a quicker route"* · *"The quicker route was designed and never wired."*
**STATE: AUTHORISED** — Lead Architect, 2026-08-20

---

## 🔴 THE HARD LINE ON THIS CARD, BEFORE ANY OF THE WORK

> ### **David: *"buy speed by giving eLo less of himself - do not do this at all… eLo decides the output even as part of the language model."***

**Nothing on this card may change one token of what eLo says.** Same model, same system prompt, same token
budget, same memory and context. Every item here changes only **when bytes arrive**, never **which bytes**.

**Explicitly forbidden as "optimisation" here:** a smaller model for his voice · a lower `max_tokens` ·
trimming prompt context or memory injection · shortening `max_sentences`. If a change makes him answer
faster by making him less, it is not this card — raise it as a `[PROPOSAL]` and stop.

---

---

## 🔴 ADDENDUM 2026-08-20 — I measured the prompt. Read this before task 0.

**The system prompt is 18,912 chars ≈ 4,728 tokens — 58% of `num_ctx: 8192` — in the MINIMUM case, with no
vault context and no state context loaded.** Every turn pays for it.

**Good news first, so nobody "fixes" what is already right:**
- **94.6% of the prompt is a byte-identical prefix across turns.** The volatile part
  (`[DIRECTIVE — THIS RESPONSE ONLY]`) is at the very END. **That is the correct layout for prefix caching —
  do not reorder it for speed.**
- `keep_alive: "30m"` is set on both Ollama paths (CT0031 Fix A). Model should not be cold-loading.

**So the decisive question is one number, and I cannot get it from here:**

> 🔴 **Is `prompt_eval_count` ≈ 4,700 on every turn, or ≈ 0 after the first?**
> - **≈4,700 every turn** → Ollama's prefix cache is MISSING despite the correct layout. That re-read is
>   most of the latency, and it is fixable without removing one word of eLo.
> - **≈0 after the first** → the cache works, and the latency is what card 0059 already names: no streaming,
>   plus Groq and Cerebras each burning a 30s blocking timeout before Ollama is even tried.

`_ollama_call` already parses this (`prompt_eval_count`, `prompt_eval_duration`, `load_duration`) into
`_last_ollama_metrics` and logs it at INFO. **It is never persisted** — `server.log` is 1.5 KB and stops on
08-19, so the number has never been captured. **Task 0a: write those five fields into
`blender/routing_trace.json` every turn, then send me ten turns.** That is an afternoon of nothing but
running it, and it decides whether items 1-5 are the right work at all.

🔴 **Do not shrink the prompt to buy speed.** David: *"buy speed by giving eLo less of himself - do not do
this at all."* 4,728 tokens of eLo is not bloat to be trimmed — if the prefix cache is missing, **fix the
cache, not the prompt.**

*(Related, and it is the same measurement: at 4,728 tokens the anti-mirroring rule sits ~2,400 tokens deep
and is being ignored, while the GROUND directive at the very end is obeyed. See `0062` §1. Prompt length is
costing eLo his instructions as well as his speed — one cause, two symptoms.)*

## 1 · WHAT I MEASURED (evidence, not theory)

**`ELO_BACKEND=groq`** in `.env` — eLo runs pinned-Groq on `llama-3.3-70b-versatile`. Now follow that mode
through `route_streaming()` (`runtime/backend_router.py:930`):

```python
if mode not in ("auto", "cloud") or not _openai_available():
    # Non-streaming path — latency not measured
    text, backend = route(...)
    return text, backend, 0.0
```

`"groq"` is not in `("auto","cloud")`. **So eLo's real, everyday configuration never streams.**

- **There is no Groq streaming function at all.** `grep "def .*stream"` returns exactly `_openai_stream`
  (:381) and `_ollama_stream` (:451). Streaming was built for two backends eLo isn't pinned to.
- `on_first_sentence` → `_voice_speak(sentence)` early-TTS (`server.py:3748`) **therefore never fires.**
  eLo waits for the *complete* generation, then starts speaking.
- **Proof it took that branch:** `blender/routing_trace.json` (live, 2026-08-20 19:48) →
  `"llm_latency_ms": 0.0`. That `0.0` is returned only by the non-streaming fall-through.

**And the second finding, which matters more:**

| Live trace | `backend_used` |
|---|---|
| `blender/routing_trace.json` | `ollama+obsidian` |
| `blender/voice_trace.json` | `ollama+search` |

**David's recent turns were answered by `llama3.1:8b` running locally — not by the 70b he is pinned to.**
In pinned mode Ollama is reached *only after Groq and Cerebras have both failed* (:748-762). Both attempts
are **sequential and blocking**, each on `_json_post(timeout=30.0)` (:40). So the worst path is
~30s + ~30s + local 8b cold generation **before the first word** — and then the answer is from the smaller
brain. **Slow AND less of eLo, silently.** That is the exact failure this card exists to kill.

There is no deadline anywhere in the router. David's 4s rule has no implementation.

**What I could NOT confirm:** *why* Groq failed on those turns. `server.log` is 1,523 bytes and ends
2026-08-19 — it holds one OpenAI 429 and no Groq 403/429 for the 08-20 turns. **Task 0 below settles it.
Do not ask David to check the key until 0 has run.**

---

## 2 · THE WORK

### 0 · Find out why the pinned backend fell through *(do this first — it may be the whole bug)*
Probe `GROQ_API_KEY` and `CEREBRAS_API_KEY` against their endpoints; report status codes verbatim.
A suspended key (403) or an exhausted quota (429) would explain the whole symptom, and then items 1–4 are
still right but the urgency changes. **Report the code, don't interpret it.**
Also note: `ELO_CEREBRAS_MODEL=gpt-oss-120b`, which is not the `llama-3.3-70b` the router's docstring
(:23) claims — confirm that is intended before touching it, it is not yours to change.

### 1 · `_groq_stream()` — the single biggest win, and it is free
Groq's endpoint is the OpenAI-compatible `/openai/v1/chat/completions` already used by `_groq_call` (:255).
Add `"stream": true` and consume the SSE `data:` frames, mirroring `_openai_stream` (:381) exactly —
same first-sentence detection, same `on_first_sentence` callback, same return of
`(full_text, first_token_ms)`.
**Identical model, prompt, temperature `0.7` and `max_tokens`. The finished string is byte-identical to
today's. Only the arrival changes.**

### 2 · Let the pinned mode reach the streaming path
Extend the `route_streaming` gate so `mode == "groq"` streams via `_groq_stream`, then Cerebras, keeping the
existing `_has_lore_drift` / `_is_duplicate` / `normalise` / `_strip_trailing_question` guards **unchanged and
in the same order** — those guards are eLo's voice, not performance code.

### 3 · A real deadline — David's 4s rule, wired
- **first-token deadline ~2.5s** on the pinned backend. No first token → hand off. Replaces the 30s block.
- **total budget 4s** to first *audible* sentence, which is the number David actually gave.
- Make both env-tunable (`ELO_FIRST_TOKEN_MS`, `ELO_TURN_BUDGET_MS`); do not hardcode.

### 4 · Hedge instead of falling through
At ~1.2s with no first token, fire **Cerebras in parallel** with the **identical system prompt** and take
whichever streams first; drop the loser. A duplicate call on slow turns only — and because both carry the
same prompt, **nothing about eLo's output changes either way.**

### 5 · Warm the connection
`_json_post` builds a fresh `urlopen` per turn — full TLS handshake every time. Reuse a pooled
connection/session. `[ESTIMATE]` ~100–300ms per turn, unverified — **measure it and report the real number.**

### 6 · Ollama's actual job — and 🔴 make the fall-through VISIBLE
`llama3.1:8b` is a **smaller brain than the 70b**. Under David's rule it **must not become the routine
source of eLo's spoken words** just because it is fast.
- Keep it as the **offline floor** (it already is) and for **non-identity work** — intent/valence/CAL
  pre-classification — where it never shapes his sentences.
- 🔴 **When a turn is answered by the 8b, say so in the routing trace AND surface it.** David should never
  have to *infer from the writing* that he is talking to the smaller model. Right now that is exactly what
  happened, and it is why this landed as "eLo feels slow" instead of "eLo's cloud brain is down."

---

## 3 · Test (must pass WITHOUT David)

`tests/test_wo073b_stream_and_deadline.py`, and it must go **RED when the feature is disconnected**
(disconnection-falsifiability):

1. `_groq_stream` exists and fires `on_first_sentence` before the generation completes.
2. `route_streaming(mode="groq")` returns `first_token_ms > 0` — **asserting `!= 0.0` is the whole point**,
   `0.0` is today's silent non-streaming fall-through.
3. **Output identity:** the same prompt through `_groq_call` and `_groq_stream` (temperature pinned)
   yields the same assembled text. **This is the test that protects eLo — it must exist.**
4. First-token deadline exceeded → hand-off fires, and does so in **< 4s wall clock**, not 30s.
5. A turn served by Ollama is labelled as such in `routing_trace.json`.

## 4 · Done when
Implemented · test green · committed · commit hash appended below · card moved to `DONE/` · line in
`outbox.json`. **Report the measured before/after first-audible-word time — the real number, not an estimate.**

## 5 · ✅ ARCHITECT IMPLEMENTED THE ROUTER HALF, 2026-08-20 — Builder verifies LIVE

David asked me to fix it, so I did. `runtime/backend_router.py`: **4 lines removed, 142 added.**
Backup of the original: `/tmp/backend_router.BEFORE.py`.

| # | Change | Status |
|---|---|---|
| 1 | `_groq_stream()` — new. stdlib urllib (keeps WO-032b's zero-dependency decision), mirrors `_openai_stream` | done |
| 2 | `route_streaming()` — new `mode == "groq"` branch. Pinned mode now streams: Groq → Ollama stream → `route()` | done |
| 3 | `_finish()` — one shared post-processor. **Cerebras and Ollama can no longer skip `_is_duplicate` / `_last_responses`** (the doubling, `0060` §C) | done |
| 4 | `_cloud_timeout_s()` — per-attempt cloud timeout 30s → **8s**, env `ELO_CLOUD_TIMEOUT_MS`. Worst case before Ollama: 60s → 16s | done |
| 5 | `_first_token_budget_s()` — 2.5s, env `ELO_FIRST_TOKEN_MS` | done |

**Verified here (sandbox, stubbed transport — no network):**
- `_groq_stream` assembles correctly and fires `on_first_sentence` on sentence 1, `first_token_ms > 0`
- `route_streaming(mode="groq")` now returns `groq(stream)` with non-zero latency — **previously `('…','groq', 0.0)`**
- a repeated Ollama reply is now **rejected** as duplicate; before, it was returned
- 🔴 **payload diff between `_groq_call` and `_groq_stream` is exactly `{"stream"}`** — model, messages,
  temperature 0.7 and max_tokens identical. **Not one token of eLo changes.**
- **10/10 router suites green** (`wo032`, `wo032b`, `wo032-FD`, `ct0031`, `keepalive/prompt-audit`, `backends`)

**🔴 NOT verified — this is yours:** no Groq or Ollama endpoint is reachable from my sandbox, so the real SSE
frames, real latency and real first-audible-word are UNMEASURED. **Do not close this card on my say-so.**

### Prompt measurements — and the conclusion is DON'T TOUCH IT
`living_presence_spec` **5,098 tok (94.4%)** · `executive_directive` 305 tok → **5,403 minimum**;
card 0047 measured **7,281 live** = **89% of `num_ctx: 8192`**.
**But the layout is already right:** volatile content (state 86.4%, vault 89.8%, directive 93.1%) sits at the
END; only ~700 tokens should re-evaluate per turn. 🔴 **So prompt size is NOT the latency bug and must not be
"optimised". Leave it alone.**
⚠️ It IS tight though: 7,281 + 256 generated leaves ~650 tokens of headroom in an 8,192 window. **Check
whether Ollama is silently truncating** — if it truncates the front, it is cutting eLo's identity. Report it.

## 6 · Result (Builder — live verification)
- commit: 3712836 (tests only — Architect's router impl is commit from 2026-08-20, not separately hashed here)
- test: tests/test_wo073b_stream_and_deadline.py — 5/5 passed. Disconnection-falsifiable: mode="auto" gives latency=0.0, test 2 RED.
- Groq/Cerebras key probe (task 0), verbatim status codes: **Groq HTTP 403 code 1010 · Cerebras HTTP 403 code 1010** (Cloudflare block on both, not auth rejection)
- first audible word, before → after: **UNMEASURED** — both cloud backends returning 403, Ollama answers at ~21s. Measurement requires Groq or Cerebras reachable. Card cannot fully close until this number is captured.
- notes: ELO_BACKEND=groq is effective (first-active-line-wins per .env). ELO_CEREBRAS_MODEL=gpt-oss-120b confirmed present — not changed (not Builder's to change). Groq kept in path per David — do not hang up on it. Live latency unblock: check Groq key/account status.
