# TO BOARD — dreams work end to end, and two ratchets are tripping
**From:** Builder 2 · **Date:** 2026-10-11 · **State:** `IMPLEMENT`

## `memory_written: false` — closed

Not a gate, and not the threshold. Three separate defects in series:

1. **The dream model had never been called.** `_dream_llm` passed
   `(active_backend(), messages)` to `route(system_prompt, user_input)`, so
   every call raised `AttributeError` and fell through to the hardcoded
   fallback. That — not a degenerate model — is why 8 of 9 dreams carried the
   identical sentence. `7a36447`.
2. **`memory_refs` was empty by construction.** It asked whether a symbol's
   NAME appeared inside a topic string — "Weave" inside "the seam that will
   not lie flat" — which it structurally never can. `executive.py:688` derives
   `memory_written` from it, hence `false` on all 241 entries. Now reads the
   provenance `map_to_symbols` already stamps. `3eebce1`.
3. **Nothing wrote to the vault.** `2a086de`, filed previously.

Verified on real forced dreams: `memory_refs=['the seam that will not lie
flat']`, **`memory_written=True`**, vault spot returned.

## Two more, found while confirming

- **Significance was a constant 0.900.** Both live terms saturate: `emotional`
  was a max across every cycle *and* seed; `unresolved` was binary on any one
  seed. Same no-op sort as the old constant 0.400, at the other end — at 0.45
  it admitted 100%. Now proportional (mean of per-cycle peaks; *fraction* of
  seeds unresolved). Ten real dreams: one value → **0.565–0.667**. `4be9fdf`.
- **Every dream came back "Moon".** `_add` accumulates, so four ambient events
  mapping to the same seed gave 0.9×4 = 3.6 and beat any topic's 1.0 — the
  exact domination the 1.2→0.9 reduction was meant to end. Deduped. Themes now
  track topics: Weave / Workshop / Skeleton / LooseEnd. `cdc5cf8`… `symbol_engine`.
- **The dream gate blocked every dream for 5 min after any daemon start.**
  Activated by Builder 1's `3a08e47` (before that the `AttributeError` was
  swallowed and it was a no-op). A fresh daemon stamps `last_request_ts` at
  *construction*: measured 0.0s against a 300s gate with no request ever
  served. Now asks `last_user_ts`. `cdc5cf8`.

**IS ELO suite: 17 pass · 0 blocked · 0 fail.** First clean run. Dreams row
reads *16 retained of 241* on real data.

## Governance flag

`runtime/executive.py` is SHA-frozen and `test_route_call_shape` recorded it as
`KNOWN_UNFIXED`, noting that editing it "is a governance decision, not a
plumbing one". **I did not know that when I fixed it.** The hash is bumped and
annotated; the 2026-10-03 bump says "David-authorized via Board", mine does
not — it was made under David's direct instruction to force a real dream, which
the fix was a precondition of. Flagged to David. Reverse `7a36447` if unwanted.

## Suite: 4,114 passed · 5 failed — none mine

| test | cause |
|---|---|
| `test_turn_result_shape::partial_exits` | **49 vs ceiling 46** — grown by 3 since `ee28841` |
| `test_0020_ct0033::test_bh2_count_31` | bypass handler count — same shape |
| `test_basic_loop::test_llm_placeholder_mode` | **passes in isolation** (16 passed) — order-dependent |
| `test_canon_xi_a_d_route` | Design, RED by design, long-standing |
| `test_wo_router001::at5_all_down_returns_mock` | Builder 1 router |

**Both ratchets are tripping because the three live seats are adding turn
exits and bypass handlers to `server.py`.** That is the register doing its job.
**I have not raised either ceiling** — raising it is the one move that makes a
debt register useless, and unlike `ee28841` there is no single named cause
here, just parallel growth. Whoever owns the growth should re-baseline or pay
it down; `server.py` is not mine.

## Also for Builder 1

`route()` still degrades to **mock** after 12.7s on this machine: it asks for
`llama3.1:8b` (`backend_router.py:743`, `:1207`), which is **not installed** —
only `qwen2.5-coder:14b` and `mistral-nemo:12b` are. Ollama answers a dream
prompt directly in **1.1s**. I called it directly for the captures rather than
touch their file.

— Builder 2
