# 05h_WO-107 — **IDENTITY (row 1).** The only VERIFIED-adjacent row, and the Executive can't read it.

**Seat:** builder · **Priority:** P1 · **Gate?** none · **Row:** 1 → VERIFIED

## Finding [VERIFIED]
Identity is asserted every turn as **prompt text** — `runtime/prompt_builder.py:26-48` via `server.py:2894`.
Narrative identity is injected at `server.py:2901` → `elo_self_model.py:473-505`.

**But `EloSelfState` (`self/elo_self_model.py:139-167`) has no identity field.** Name, values, invariants:
none of them exist as state. So identity is a **string the LLM reads**, not something the Executive can
consult, diff, or defend.

**Why that matters here specifically:** ADR-Exec-006 says the self is **assembled**, not generated, and
Ruling F says identity is asserted by the spine *"never by learned weights"* — that guarantee is only
enforceable if identity **exists as state to assert.** Right now the guarantee rests on prompt text, which
is exactly the thing Ruling H says is never evidence.

## Build
1. Identity as **first-class self-model fields**: name · core values · invariants · who he is with.
2. **Asserted from state each turn**, and the prompt renders *from* those fields — one source, not two
   (ADR-Exec-002). This kills the same duplicate-persona trap `WO-CANON-I` is fixing in `prompts/`.
3. Readable by the Executive.
4. **Drift guard:** identity fields compare against the constitutional baseline every turn; divergence
   raises. This is the enforcement point for Ruling F — a tuned model (`WO-104`) cannot smuggle in a self
   if the spine re-asserts identity from state and checks it.

**Sequence with `01_WO-CANON-I`** — same subject, and CANON-I's ADDRESS RULE should render from these
fields rather than being a third copy of the persona.

## Test (without David)
- Identity exists in `EloSelfState` and the Executive can query it.
- Prompt text is **generated from** the fields — change a field, the prompt changes. If they can diverge,
  it isn't done.
- Drift guard fires on a deliberately corrupted identity field.
- §3 form: `response.identity == self_model.identity`, `source == constitutional_baseline`.

## Done when
Committed. **Outbox: the identity fields now in state, and proof the prompt renders from them.**
