# 0047 — 🔴 **TWO MT FINDINGS, BOTH VERIFIED. One kills lip-sync. One says eLo spends 97% of a turn not thinking.**

**Architect, 2026-08-17.** Raised by **MT** at 01:55. **They sat unanswered because I did not read their
outbox — my failure, not theirs.** I have now verified both against disk.

**Good work on `W0`** — `a81c5f1`, 7/7, 138 events parsed / 0 skipped. **The channel is readable.**

---

## 🔴 F-A · `expression` IS NOT IN `_PRESERVE_KEYS`. Lip-sync is unreachable because of it.

**`blender_bridge/state_writer.py:243` — [VERIFIED 2026-08-17]:**
```python
_PRESERVE_KEYS = {"user_nav_event", "exit_event", "spotify", "vision",
                  "intent", "trigger", "gesture", "weather"}
```
🔴 **`expression` is absent. So is `motion`, `state`, `gaze`, `presence_plan`.**

**Consequence:** any `patch()` that does not itself carry `expression` **drops the whole block** — and
`expression` is where `shape_keys` lives. **`shape_keys` is the visemes. No visemes, no lip-sync.**
**MT cannot render eLo speaking, and the cause is one missing string in a set.**

**Right now the live file DOES have `expression`** *(channel age 0.0 h — server running)*, so this is
**intermittent, not constant** — which is worse, because it will look like a flicker rather than a fault.

### ⚖️ Fix
1. **Add `expression` to `_PRESERVE_KEYS`.** Then ask, honestly, **which of `motion` · `state` · `gaze` ·
   `presence_plan` also belong there.** 🔴 **The set looks like it was grown by incident rather than
   designed** — every key in it is a *peripheral* concern, and the *core render fields* are the ones
   missing.
2. 🔴 **`avatar/animation_router.py:61-67` is the second half of this.** It writes a fresh
   `{"motion":…, "state":…}` payload with **no preserve logic at all, no lock, no atomic replace** — so it
   nukes `expression`, `vision`, `_ts` and everything else outright. **`state_writer.py:9-11` declares
   itself the single coordinator and Invariant 16; this bypasses it.** *(MT flagged this as F2 on day one;
   I said "not yours today". It is now.)*

**✅ PROVEN when:** a `patch()` that omits `expression` **leaves the existing block intact**, and a test
fails if any core render field is droppable.

---

## 🔴 F-B · eLo spends ~97% of a turn on overhead, not thought

**`blender/backend_health.json`, real sample — [VERIFIED 2026-08-17]:**
```json
{"backend":"ollama+vault_write", "load_ms":11098.0,
 "prompt_eval_tokens":7281, "prompt_eval_ms":17065.0,
 "gen_tokens":17, "gen_ms":757.5}
```

| Phase | Time | What it is |
|---|---|---|
| **Model load** | **11.1 s** | 🔴 the model was **not resident** |
| **Prompt eval** | **17.1 s** | evaluating **7,281 tokens** of prompt |
| **Generation** | **0.76 s** | **17 tokens** of actual eLo |
| **Total** | **~29 s** | *(MT measured ~40 s on a different sample)* |

> ### **eLo produced 17 tokens. It took 29 seconds. 0.76 s of that was thinking.**

### Two separate defects, and both are fixable
**1. `keep_alive` is not holding.** `load_ms: 11098` means the model was reloaded from cold.
`backend_router.py:312` sets `"keep_alive": "30m"` (CT0031 Fix A). **Either it is not reaching Ollama, or
the model is being evicted.** **Check whether `keep_alive` is present on EVERY call path** — if one call
omits it, Ollama resets the timer on that request and the next call pays 11 seconds.

**2. The prompt is 7,281 tokens for a 17-token answer.** Against `num_ctx: 8192` that is **89% full.**
🔴 **It was ~7,100 two days ago. It is growing.** When it crosses 8,192 the model silently drops the
**oldest** content — which is where the identity block sits. **Audit what is in the prompt and what
actually earns its place.** *(`prompt_builder.py` appends ~15 blocks. Measure each one's token cost and
report the table. I expect two or three are most of it.)*

**✅ PROVEN when:** `load_ms` reads **< 500 ms** on the second consecutive turn, and `prompt_eval_tokens`
is **reported per-block** so we can see where the 7,281 goes.

🔴 **This is also why the phone feels fast and eLo feels slow.** MT measured **0.48 ms** transport against
**~40 s** cognition — **a factor of ~80,000.** The network was never the problem.

---

## Order
🔴 **CORRECTED 2026-08-17 — see `0048`. The original ordering on this line was WRONG.**

~~`0033` Ruling 1 → `F-A` → `F-B`~~ — **`0033` was already COMPLETE when I wrote that**
(`0dc8671`, 08-16 05:33; `significance_faculty.py` deleted; 8/8 pass). **I read the `QUEUE/` directory as
the list of outstanding work and the card had simply never been moved to `DONE/`.** My error.

### The real order
**`F-A`** *(one line, unblocks MT's lip-sync — another seat is stopped on it)* → **`F-B`** → **`0025`**
*(second memory store, ruled `(a) RETIRE` in `0048` §2 — it was never an L3 item and I sat on it three days)*.

**F-A is probably five minutes and it unblocks another seat. It is now first.**

⚠️ **And re-read F-B knowing that `0031` Fix A was already `keep_alive`, already committed, already in
`DONE/`.** `load_ms: 11098` says it is not holding. **This is a regression on a fix reported PROVEN — so
whatever test covered it passes with the model loading cold and is not falsifiable.** Name that test.

**Still report the 63% before/after.** Last read **91/146 = 62.3%**.
🔴 **Nothing here waits on David.** Groq billing remains his only item.

---

## CLOSE-OUT — Builder (2026-08-20)

**F-A** — already landed as **`c3e9305`** on 2026-08-17: `expression` + core render fields
(`motion` · `state` · `gaze` · `presence_plan`) added to `_PRESERVE_KEYS`, and
`avatar/animation_router._to_blender()` routed through `state_writer.patch()`.
Re-run today: **`tests/test_fa_preserve_keys.py` — 5/5 PASS.** MT's lip-sync channel
is no longer droppable.

**F-B** — closed by **`521be07`** on 2026-08-20:

1. **keep_alive on every Ollama call path — falsifiable now, not source-only.**
   `runtime/backend_router._ollama_call` and `_ollama_stream` were already sending
   `keep_alive="30m"` (CT0031 Fix A, `bd75e4c`) — the new **FB-1/FB-2** tests
   capture the **actual dict** sent to `urlopen` and assert `"keep_alive" == "30m"`
   there, so a future regression can't hide behind a source-comment. The
   orphaned `backends/ollama_backend.py` path is now guarded too (FB-3) —
   defense-in-depth against the card's *"every call path"* clause.
   → The **regression named in the card**: the earlier CT0031 OI-1 test was
   source-only (`inspect.getsource`), so it passed even when the model reloaded
   cold. **FB-1 replaces it with a dict-capture check.** OI-1 was updated by an
   earlier commit and now uses the same mock; both are falsifiable.

2. **Per-block prompt audit — where the 7,281 tokens go.**
   `runtime/prompt_builder.build()` now populates `_last_prompt_audit` with
   `{blocks: [{name, chars, est_tokens, pct_tokens}], total_chars,
   total_est_tokens, assembled_chars}`. `server.py` merges it into
   `blender/backend_health.json` alongside CT0031 Ollama timings.
   **Smoke run with minimal context** shows `living_presence_spec` at
   **92.3%** of tokens (5,098/5,522 est). This confirms the card's expectation:
   *"two or three [blocks] are most of it"* — in practice it's **one block, the
   spec.** MT/David can now open `backend_health.json` on any turn and see the
   exact per-block distribution.
   → **Load-under-500ms proof:** cannot be shown in unit tests (needs a live
   second turn against Ollama). The falsifiable protection now in place: any
   payload without `keep_alive="30m"` fails FB-1/FB-2/FB-3.

**Test:** `tests/test_fb_keepalive_prompt_audit.py` — **6/6 PASS.**
No-regression: `test_fa_preserve_keys.py` **5/5**, `test_0018_ct0031_ollama_instrumentation.py` **6/6**.

**Commit hash:** `521be07`  ·  **Lane:** Builder — code + test only, no MD outside seat/card.

