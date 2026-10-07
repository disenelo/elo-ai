**WO:** ROOT-2-FIX · **Seat:** builder · **Priority:** P1
**Reserved?** no

## Goal
When graph_loader retrieves a fact, eLo uses it — not the LLM's generated guess over it.

## What's broken
ROOT-2: retrieved WKG context is injected into the prompt but the LLM generation overrides it with hallucinated alternatives. The retrieved fact loses.

## Scope — exactly this, nothing more
- In prompt_builder.py: retrieved WKG facts must be marked as AUTHORITATIVE — instruct the model that these facts are ground truth and must not be overridden or second-guessed
- Add a MISSING-FACT guard: if a retrieved fact contradicts the model's generation, the retrieved fact wins
- Do not change retrieval logic — this is prompt authority only

## Files to touch
`runtime/prompt_builder.py`

## Test
`python3 -m pytest tests/ -k "missing_fact or prompt" -v`
Inject a known WKG node with a specific fact, ask eLo about it — eLo must cite the node, not generate an alternative.

## Done when
Retrieved facts are used as-stated. LLM does not override them. Test green. Committed. Move to BUILT/.

## Live turn needed (seat fills this in — exact words)
> David says to eLo: "What's my preferred response length?"
> eLo should cite the stored preference exactly, not guess.

## Result
- commit: d16a948
- test: 109 prompt/missing_fact tests green (2026-10-07)
- notes: graph_context in prompt_builder.py was labeled [RELATIONSHIP & PERSPECTIVE] — signals
  context/hints, not ground truth. LLMs default to their own generation when retrieved fact is
  short or ambiguous. Fix: replaced label with hard preamble:
  "[RETRIEVED FACTS — AUTHORITATIVE] ... These are ground truth. Use them exactly as stated.
  Do NOT override, contradict, or second-guess them with a generated alternative."
  No retrieval logic changed — prompt authority only per card scope.
