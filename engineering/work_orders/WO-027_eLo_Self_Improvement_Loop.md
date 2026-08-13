---
id: WO-027
title: "eLo self-improvement loop — behaviour eval + LLM-judge scoring + escalate-on-failure routing + reviewed correction-memory (in-context learning, no live fine-tuning)"
owner_seat: SEAT-ENG-001 (Builder) + SEAT-EXE-004 (Architect — eval set + review policy)
occupant: Builder (Python) + Architect
priority: P2
reason: "David 2026-08-02: build a self-improving loop — evaluate eLo's responses, route failures to a stronger model/critic, and learn from corrections via a memory buffer injected as few-shot context. Avoids unstable live fine-tuning; uses in-context learning (ICL)."
review_required: L1 → L3 (David owns the correction-review policy)
risk: medium — corrections shape future behaviour; MUST be human-reviewed by default to avoid personality drift
status: READY — sequence after WO-026 (builds on the same backend router)
created: 2026-08-02
builds_on: WO-026 (streaming + fast/deep model routing), memory/embedding_store.py, wo_test_runner, wo_policy
---

# WO-027 — eLo self-improvement loop (eval → escalate → reviewed-correction memory → inject)

The paste's architecture, **mapped onto what DISENELO already has** — build only the gaps. Core principle
(from the source, correct): **do NOT do live fine-tuning** (unstable/expensive); use **in-context learning
(ICL)** via a reviewed memory buffer.

## Reuse (already exists — do not rebuild)
- **Router / model escalation:** `runtime/backend_router.py:route()` (fallback chain) + **WO-026** fast→deep
  model routing. Escalation = route to the deeper model **with the failure reason attached**.
- **Evaluation harness:** `wo_test_runner` + `tests/` (pass/fail + tier). `test_conversation_quality.py`.
- **Embeddings / vector store:** `memory/embedding_store.py` + `embedding_cache.json` (semantic retrieval
  already possible — extend, or add ChromaDB/Faiss if cleaner).
- **Critic / human correction + guardrails:** David = the approval gate; `COMPLETION_LOG.md` = correction
  record; `wo_policy` = auto-vs-human tiers; `company_state_writer` safety gate + kernel loop-detection.

## Build (the gaps)
### 1. Behaviour golden-set
- A structured eval dataset for eLo's **behaviour** (not code): `{input, expected_routing/answer-style,
  eval_criteria}`. Seed it from the real failures we fixed (WO-019 voice, WO-020 routing drift,
  WO-022 memory recall) so regressions are caught automatically. JSON/DataFrame; runnable via the runner.
### 2. Scored evaluation (LLM-as-judge) + escalate-on-failure
- Beyond binary: an **LLM-as-judge score** (is this eLo-true? correct routing? direct answer?) using the
  routing traces (`blender/routing_trace.json`, `voice_trace.json`) as evidence.
- On a low score → **route to the deeper model with the error/trace attached** (WO-026 deep model) for a
  corrected response. Sandbox any code-execution checks (the paste's `exec()` — must be sandboxed, reuse
  the test sandbox, never raw exec on model output in prod).
### 3. Reviewed correction-memory (ICL)
- Store `(input, corrected_response, why, trace)` pairs in the embedding store / a `corrections` vector DB.
- On future turns: **semantic search → inject top-3 closest past corrections** into eLo's system prompt as
  "examples of how to answer correctly."
- **HUMAN-REVIEWED BY DEFAULT (David 2026-08-02):** a correction only enters the injected memory after
  review. Tier it via `wo_policy`: safe/test-gated fixes may auto-enter (🟢); anything touching eLo's
  **voice/personality/routing** requires David (🔴). Auto-appending unreviewed corrections risks the exact
  personality-drift / wrong-routing we already debugged — the review gate is protective, not bureaucratic.

## Acceptance
1. Golden-set runs via `wo_test_runner`; the WO-019/020/022 failure cases are in it and pass.
2. LLM-judge scores a response; a low score escalates to the deep model with the trace, and the second
   answer is re-scored.
3. A reviewed correction is stored with an embedding; a semantically-similar later question injects it as
   a top-3 example (verify the injection appears in the assembled prompt).
4. Correction-review policy enforced: personality/voice/routing corrections cannot enter injected memory
   without David; safe ones can auto-enter. Frozen kernel green.
5. `tests/test_wo027_self_improvement.py` (≥6 cases). Handback: a demo where a seeded failure is caught,
   escalated, corrected, reviewed, stored, and improves the next similar answer.

## Notes
- Sequence after WO-026 (shared router). Optional prod tooling the source names (Promptfoo/Ragas for eval,
  NeMo Guardrails) can be evaluated later — start with the custom runtime you already have.
- 🔴 on the correction-review policy (it shapes eLo's mind); 🟢 on the plumbing.
