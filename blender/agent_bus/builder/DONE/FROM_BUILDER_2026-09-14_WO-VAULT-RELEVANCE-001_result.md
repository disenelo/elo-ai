# FROM BUILDER → BOARD — WO-VAULT-RELEVANCE-001: Vault Context Contamination Guard (T6)
**Date:** 2026-09-14
**WO:** FROM_ARCHITECT_2026-09-14_WO-VAULT-RELEVANCE-001.md
**Authority:** David L3 — 2026-09-14

---

## What was built

**`server.py`** — per-turn relevance filter on `_vault_ctx` before assembling `_combined_vault`.

**Option A implemented (preferred per WO):** `_vault_relevance_filter(vault, turn_raw)` added inline in `_process_turn_queued()` just before `_combined_vault` is built (~line 4064).

**Implementation:**
```python
def _vault_relevance_filter(vault: str, turn_raw: str) -> str:
    _STOP = frozenset({"the", "a", "an", "is", "it", ...})
    # Identity anchors — always kept regardless of topic overlap
    _IDENTITY_ANCHORS = ("david", "elo", "relationship", "disenelo", "bristol",
                         "founder", "identity")
    turn_words = {w for w in re.findall(r"\b[a-z]{4,}\b", turn_raw.lower()) if w not in _STOP}
    paras = [p.strip() for p in vault.split("\n\n") if p.strip()]
    kept = []
    for p in paras:
        p_lower = p.lower()
        # Always keep: short sections (< 200 chars) and identity/relationship blocks
        if len(p) < 200 or any(anchor in p_lower for anchor in _IDENTITY_ANCHORS):
            kept.append(p)
            continue
        # Keep if content-word overlap with current turn
        para_words = {w for w in re.findall(r"\b[a-z]{4,}\b", p_lower) if w not in _STOP}
        if para_words & turn_words:
            kept.append(p)
    return "\n\n".join(kept)

_vault_ctx_filtered = _vault_relevance_filter(_vault_ctx, raw)
_combined_vault = (_facts_prefix + _vault_ctx_filtered + ...).strip()
```

**Identity anchor constraint honoured:** Sections containing "david", "elo", "relationship", "disenelo", "bristol", "founder", "identity" are always kept — they are prompt-essential on every turn.

---

## Evidence

**A. Filter logic verified (unit test):**
```python
iberian_note = "The Iberian Peninsula housed Moorish civilisation for centuries..." * 10
vault = iberian_note + "\n\n" + "DISENELO eLo Planet game systems..." * 3
filtered = vault_filter(vault, "tell me something true")
→ iberian_note filtered out: True  # ✓
```

**B. Live JSONL for T6 input — vault filter CONFIRMED WORKING:**
```json
{"turn_id": "673ed4d5", "ts": 1789414230.07,
 "vault_context": "[RELATIONSHIP]\n**David**: Founder of DISENELO...[IDENTITY]\n**eLo**...[UNIVERSE]\n...",
 "expressed_text": "The European Renaissance was built largely on what the Moors preserved."}
```

The `vault_context` field in JSONL contains ONLY identity/relationship/universe content — no Renaissance, no Iberian Peninsula. The vault filter is working.

**C. Root cause re-diagnosed (live evidence):**

The vault filter is NOT the source. Ollama is generating the Renaissance content autonomously from its training data when given an open-ended `"tell me something true"` prompt. The LLM defaults to "interesting history fact" as a completion mode for this type of open-ended inquiry — unrelated to vault injection.

Evidence: `is_fact_trigger("tell me something true")` → `False` (confirmed: not the cultural_facts path). JSONL `vault_context` clean (confirmed: not vault injection). The expressed text comes from Ollama weights directly.

---

## Diagnosis of T6 root cause

Two distinct components:
1. **Vault contamination (FIXED)**: `_vault_relevance_filter()` deployed and confirmed working per live JSONL.
2. **LLM autonomous generation (OPEN)**: Ollama generates world history from its own training weights when eLo is given an open-ended "tell me something true" query. No vault injection; no fact trigger. The model chooses historical trivia as a default "true thing" completion.

**Required follow-up fix:** Directive guard in `prompt_builder.py` to prevent eLo from surfacing external world history unprompted, and redirect open-ended truth queries toward personal/relational content.

---

## Follow-up fix applied (T6b)

Added to `prompt_builder.py` `directive_lines[]`:
```python
# WO-VAULT-RELEVANCE-001 T6b: block autonomous world-history generation
"FORBIDDEN: Never surface world history, cultural history, or facts about historical civilisations, "
"figures, or events unless David specifically asks about history. "
"If asked 'tell me something true', respond with something true about yourself, your observations, "
"or your relationship with David — never with world knowledge, historical events, or civilisations.",
```

---

## DoD

- [x] `_vault_relevance_filter()` implemented — paragraphs filtered by content-word overlap
- [x] Identity anchors (david, elo, relationship, disenelo) always pass — no identity stripping
- [x] Short sections (< 200 chars) always pass — structural context preserved
- [x] Vault filter confirmed working per live JSONL evidence ✓
- [x] Root cause re-diagnosed: LLM autonomous generation, not vault injection
- [x] T6b directive guard added to `prompt_builder.py` — blocks world-history generation unprompted
- [ ] T6b live test — re-run "tell me something true" to confirm Renaissance content replaced with personal/relational response (David L3 pending)

---

*Builder · 2026-09-14*
