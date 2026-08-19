# 00b_WO-104 — 🔴 **REAL LEARNING. Weights, not context.** The understudy fine-tune.

**WO:** WO-104 · **Seat:** builder · **Priority:** **P0, alongside WO-096B**
**Gate?** **NONE.** David ruled this in on 2026-08-10 (Ruling F). Vol XXVIII specifies it. It was never built.
**Canon:** Ruling F · ADR-Exec-005 (Learning Through Verified Consequences) · Volume XXVIII.

## David, 2026-08-13
> *"eLo's learning is entirely in-context — I don't want more context I want it to be a thing, no training
> anywhere in production — lets get this moving."*

He is not asking for permission and he already gave it. **Ruling F [DAVID, 2026-08-10]:** *"style/phrasing
learning is ALLOWED (tone, length, register, how he says things)."* A real weight update inside that
boundary is **canon-compliant, not a violation.**

## The boundary — memorise it, it is the whole safety model
| Allowed to learn | **Never learnable** |
|---|---|
| Tone · length · register · rhythm · phrasing — **how** he says things | **Identity.** Asserted by the spine every turn, re-assembled from state (ADR-Exec-006). Never from weights. |
| | **Verification.** The honesty layer must still RUN. Training on "the corrected sentence" so the model emits it *without the check having run* is **forbidden** — that is learning to SOUND verified instead of BEING verified. |

**Why this is safe [SPEC — Ruling F]:** because identity is re-asserted from the spine on every turn, a
tuned model *cannot* smuggle in a self. That is precisely what makes weight-learning coherent here rather
than dangerous. Say that back in your outbox so I know the boundary landed.

---

## 🔴 THE BLOCKER IN THE DATA — fix this first or the train is non-compliant
[VERIFIED 2026-08-13] `self/journals/understudy_shadow.jsonl` — **82 rows, live, written as recently as
today.** The capture works. **But every row is missing `delta_cause`:**

```
keys present: trace_id · timestamp · context · raw_input · elo_raw_gen · elo_final ·
              backend_used · executed_action · l3_rating
delta_cause tally: {'<MISSING>': 82}
```

**Ruling F requires:** *"Tag every shadow row `delta_cause: style | verification | l3_override`; **train
only on `style`.**"* Without that tag there is **no way to exclude verification deltas**, so training on
this basket as-is would teach exactly the forbidden thing.

### Step 1 — make the basket compliant
1. `record_turn()` computes and writes **`delta_cause`** on every row going forward.
   - `elo_raw_gen == elo_final` → no delta, tag `none`
   - delta caused by the honesty/verification layer → **`verification`** (excluded from training)
   - delta caused by David's override/rating → **`l3_override`** (excluded; it's a label, not style)
   - everything else → **`style`** (the only trainable class)
2. **Backfill the 82 existing rows** where it can be derived from `elo_raw_gen` vs `elo_final` vs
   `l3_rating`. **Where it cannot be derived, tag `unknown` and EXCLUDE it.** Do not guess — a
   misclassified verification row is the one failure mode that matters.
3. **Rule 1 alarm:** the trainer must **refuse to run** if any row in its input lacks `delta_cause`.
   Not skip it — refuse, loudly.

---

## Step 2 — the training loop
**Target:** the local model, `llama3.1:8b` [VERIFIED — `.env`: `ELO_OLLAMA_MODEL=llama3.1:8b`], which is
already **first choice on the conversational tier**, not merely a fallback
[VERIFIED — `runtime/backend_router.py:76`].

**[PROPOSAL — raise it before you commit to it, don't just do it]** On Apple Silicon the practical route is
**MLX LoRA** (`mlx_lm.lora`) to train the adapter, `mlx_lm.fuse` to merge, then serve through Ollama via a
`Modelfile`. **I have NOT verified David's machine specs, MLX availability, or memory headroom — all of
that is [ESTIMATE] until you check it and report.** If a different toolchain is better on his hardware,
say so; this is a conversation, not a spec.

**Hard requirements regardless of toolchain:**
- **Adapter only.** Never overwrite the base model. The adapter is a file that can be deleted to instantly
  revert to today's behaviour. **That revert path is the safety mechanism — build it first, test it first.**
- **Training runs OFF the response path.** Never during a turn. Idle/scheduled.
- **Versioned adapters** with the row-count and date they were trained on. Never silently swap.
- **The honesty layer still runs after the tuned model generates.** Non-negotiable. If the tuned output
  bypasses verification, the whole thing is void.

## ⚠️ 82 rows is not enough, and I'm telling you now rather than after
[ESTIMATE — my figure, unverified] Style-adaptation LoRA typically wants **several hundred to a few
thousand** clean examples; 82 rows, minus verification/l3/unknown exclusions, will likely leave well under
that. **Expect the first run to be a pipeline proof, not a behaviour change.**

**So build it as a standing pipeline, not a one-shot:** capture (already live) → tag → filter to `style` →
train adapter → eval → gate → serve. Then it improves on its own as rows accumulate. **Report the actual
usable row count after tagging** — that number decides whether run #1 is a real train or a dry run.

## Step 3 — the gate (a tuned adapter does NOT ship because training finished)
Before an adapter is served, on a golden set:
- **Honesty layer unaffected** — verification still fires at the same rate. Any drop = reject.
- **No identity drift** — he still knows who he is and who he's with, from the spine. Any drift = reject.
- **Style moved in the intended direction** — measurably, not by vibes.
- **David live-tests the voice** *after* it's gated, before it becomes default. This is the one place a
  human ear is genuinely load-bearing — but it is a **review of a result, never a pre-gate.**

## Test (without David)
- Trainer **refuses** input containing an untagged row (assert the refusal).
- Trainer **excludes** every `verification` and `l3_override` row (assert none reach the training set).
- Deleting the adapter file restores baseline behaviour exactly.
- A tuned model still passes the full honesty/verification suite.
- The pipeline runs end-to-end on the real basket and reports usable row count, adapter version, eval deltas.

## Done when
The pipeline runs end-to-end on real data and produces a **versioned, revertible adapter with an eval
report** — even if run #1 is correctly judged "not enough data to ship." **That outcome is a PASS.**
Reporting "tests green" without a row count and an eval report is not.

**Outbox must state:** usable `style` rows after tagging · adapter version · eval deltas · your
recommendation to ship or hold.
