# WP_E — Attention Faculty Audit

**Status:** PENDING
**Priority:** HIGH
**Depends On:** WP_B (One Brain frozen)
**Architecture Reference:** `docs/architecture/04_attention_faculty.md`

---

## Purpose

Audit, validate, and freeze the Attention Faculty. Attention is how eLo scores what matters in any given turn — intent weight, valence, momentum. It informs the Executive's tone and response strategy.

---

## Objective

At the end of WP_E:
- Attention scoring is validated against known inputs
- Valence detection is validated (positive/negative/neutral)
- Momentum tracking is validated across multi-turn conversations
- The Connection Surface (Phase 2.5) is validated
- The Attention Faculty is frozen

---

## Existing Architecture Review Required

**Files to audit:**

| File | Role |
|---|---|
| `runtime/attention/attention_model.py` (or equivalent) | Core attention computation |
| `tools/connection_surface.py` | Phase 2.5 — session pattern detection |
| `runtime/spine/spine.py` — attention path | How attention feeds into plan |
| `server.py` — `attn.compute()` | Attention computation per turn |
| `docs/architecture/04_attention_faculty.md` | Architecture specification |

**Known issues to investigate:**

1. **Connection Surface** — Phase 2.5 designed the Connection Surface as a session-pattern observer. Validate it is observing correctly and injecting only into g_ctx (not deciding).

2. **Attention drift** — in long sessions, does attention scoring drift? Does eLo become less responsive to emotional content after 30+ minutes?

3. **Loop detection** — `loop_detected=False` is hardcoded in the call. When does loop detection activate? Is it working?

---

## Gap Analysis

1. Is attention scoring visible anywhere in eLo's responses (does high attention produce shorter, more focused responses)?
2. Does the Connection Surface produce observations that actually change eLo's behaviour?
3. Is Phase 2.5 validated in a real session?

---

## Validation Plan

1. Run 30-minute session, observe if eLo's response tone tracks emotional valence
2. Send high-intensity input (frustration, celebration) — confirm attention score changes
3. Send identical inputs in sequence — confirm loop detection works
4. Read Connection Surface observations from g_ctx — confirm they are injected, not echoed
5. One Brain check: Attention Faculty scores — Executive decides what to do with the score

---

## Freeze Criteria

- [ ] Attention scoring validated against test inputs
- [ ] Valence detection validated
- [ ] Loop detection validated
- [ ] Connection Surface injection confirmed (not decision)
- [ ] Phase 2.5 runtime validated in real session
- [ ] One Brain compliance confirmed
- [ ] Regression tests pass
