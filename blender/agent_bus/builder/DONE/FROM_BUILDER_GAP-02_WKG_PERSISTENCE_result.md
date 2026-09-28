# BUILDER RESULT — GAP-02: WKG Persistence & Retrieval
Date: 2026-09-11
Status: DONE — §A PASS with documented gaps; §B PASS; §C FAIL (retrieval gap confirmed)

---

## Summary

WKG write works for "I have..." statements. WKG retrieval fails for personal facts
queried by topic keyword ("my dog") when the entity label doesn't directly match query tokens.
Three sub-findings below.

---

## §A — Claim Write (Persistence)

**Test input (live server, port 5050, no preloaded Faculties, no seeded WKG):**
```
IN:  "i have a dog called Biscuit, she is a golden retriever"
OUT: "Biscuit sounds like a lovely name. What's her personality like?"
```

**WKG write result:**
- Before: 210 claims
- After:  211 claims
- Written claim:
  ```
  relationship_type: STATED
  claim_text: "i have a dog called Biscuit, she is a golden retriever"
  epistemic_class: SOURCE_ATTRIBUTED
  confidence: 0.7
  created_at: 06:07:50
  ```

**§A verdict: PASS** — "I have..." statements write to WKG. ✅

---

## §A GAP — Possessive Statements Not Written

**Test input (prior turn):**
```
IN:  "my dog is called Biscuit, she is a golden retriever"
OUT: "Biscuit sounds like a lovely name. What's her personality like?"
WKG write: NONE (210 claims before, 210 after)
```

**Root cause:** `_FIRST_PERSON_VERBS` pattern at `wkg_faculty.py:271`:
```python
r"^i (keep|have|had|am|was|want|need|...)\b"
```
Matches sentences starting with "I". Possessive "my (noun) is/are..." starts with "my" — none of the three patterns fire. Claim silently dropped.

**Impact:** A natural way to state personal facts ("my dog is...", "my sister is...", "my favourite is...") produces no WKG write. Only "I have/am/keep..." forms write.

**Finding severity: P2** — common input pattern, silent drop, no feedback to user.

---

## §B — Write Significance Gate

**Finding:** WKG write thresholds are FIXED values at the write site, NOT gated on SP-29:
- `_FIRST_PERSON_VERBS` → `significance_score=significance_score or 0.6` (default 0.6)
- `_CORRECTION_SIGNALS` → `significance_score=significance_score or 0.75` (default 0.75)
- `_KNOWN_PROJECTS` → `significance_score=significance_score or 0.5` (default 0.5)

Significance passed in from the caller (`extract_and_record_claims(turn_text, significance_score=...)`)
can be SP-29-based if the caller sets it. But in current pipeline (`memory_faculty.py` / spine path),
whether the SP-29 score is passed as the `significance_score` parameter was not the blocking factor
for the Biscuit claim write — the claim wrote at confidence 0.7 with default sig 0.6.

**§B verdict: PASS** — no SP-29 significance gate blocking writes for valid patterns. ✅

---

## §C — Retrieval (Live Evidence)

**Test: server restart → cold retrieval:**
```
Restart: double-fork, port 5050, /health → OK
IN:  "what do you know about my dog?"
OUT: "I don't know any facts about your dog."
```

**Root cause — retrieval path (spine.py:1663-1714):**

1. `search_entities(meaning[:80])` where meaning = "what do you know about my dog?"
2. Token matching (`len(tok) > 3`): query yields tokens `{"what", "know", "about"}` — NOT "dog" (3 chars)
3. Returns 28 entities (all topic entities matching "what"/"know"/"about"), sliced to first 3:
   - "David Charles"
   - "topic:tell me about elo's origins"
   - "topic:what are you thinking about"
4. Gets claims about those 3 entities (up to 3 claims each)
5. Biscuit claim NOT reached — its object entity is labeled `"statement:i have a dog called Biscuit..."`, not found by the "dog" query

**Verification:**
```python
search_entities("what do you know about my dog?")  → 28 entities (none about dogs)
search_entities("biscuit")  → 1 entity: 'statement:i have a dog called Biscuit...'
```

**Root cause summary:**
| Problem | Detail |
|---|---|
| No named entity for "Biscuit" | Claim stored under generic `statement:...` concept |
| "dog" is 3 chars | `len(tok) > 3` excludes it from token matching |
| Claim stored as STATED on opaque concept | Retrieval can't reach via topic query |
| 28 entities found but all irrelevant | "what"/"know"/"about" match old topic entities |

**§C verdict: FAIL** — retrieval does not surface personal facts unless the query directly names
the entity label. "what do you know about my dog?" does not match "Biscuit" or the concept label. ❌

---

## Full GAP-02 Verdict

| Section | Finding | Status |
|---|---|---|
| §A Write | "I have..." claims write to WKG | ✅ PASS |
| §A Gap | "my dog is..." (possessive) does NOT write | ❌ GAP (P2) |
| §B Significance gate | Fixed values, no SP-29 block on write | ✅ PASS |
| §C Retrieval | Cold retrieval fails for personal facts | ❌ FAIL (P1) |

---

## What needs to fix §C (retrieval)

Two options — for Board to decide:

**Option A (entity-first write):** When `extract_and_record_claims()` extracts a personal claim
like "I have a dog called Biscuit", create a named entity for "Biscuit" (BIOLOGICAL type)
and store the claim against that entity. Then `search_entities("biscuit")` finds it.
Weakness: requires NLP to identify the named thing inside the statement.

**Option B (claim_text full-text search):** Add a second retrieval path alongside
`search_entities()` that scans `claim_text` fields directly for query tokens. Much simpler.
"dog" found in `"i have a dog called Biscuit..."` → claim surfaced directly.
Weakness: scales poorly with large claims.json; may surface noisy results.

Neither fix is in scope for Builder to self-execute without a Board work order.

---

## FREEZE status

| File | Touched? |
|---|---|
| runtime/executive.py | NO ✅ |
| prompts/living_presence_spec.txt | NO ✅ |

— Builder · 2026-09-11
