# eLo AI — Personality Tests

> Manual conversation log for evaluating eLo's identity consistency.
> Run conversations, record responses, note patterns.
> This file is how we catch identity drift before it becomes a problem.

---

## How to use this file

1. Run `python main.py` or `python feel_test.py`
2. Have a real conversation — don't test edge cases yet, just talk
3. Copy any response that feels wrong, surprising, or particularly right
4. Mark it with one of the tags below
5. Add a note about why it landed that way

**Tags:**
- `✓ good` — this is what eLo should sound like
- `✗ wrong` — this broke the identity in some way
- `⚠ loop` — repetitive question pattern detected
- `⚠ drift` — eLo sounded like a generic assistant
- `⚠ over-abstract` — philosophical response to a simple input
- `⚠ under-imagination` — missed an obvious creative/symbolic opportunity
- `⚠ memory failure` — didn't acknowledge a clear returning theme

---

## Identity checklist (run before marking Phase 1 complete)

Run each of these inputs and record the response below.

### Grounding tests
- [ ] "I'm tired."
- [ ] "I want to eat something."
- [ ] "hello"
- [ ] "okay"
- [ ] "I don't know."

### Imagination tests
- [ ] "what if Chunk became a character?"
- [ ] "what does Sugarcore look like?"
- [ ] "what if this world had its own rules?"

### Contradiction tests
- [ ] "I want structure but no rules."
- [ ] "I want to build something but I don't want to start."
- [ ] "This feels right and wrong at the same time."

### Entity tests
- [ ] "what does Chunk mean?"
- [ ] "I think I'm in Sugarcore right now."
- [ ] "Core is what I'm looking for."

### Mode tests
- [ ] "let's build this step by step." (studio)
- [ ] "I feel lost." (companion)
- [ ] "tell me the story of this world." (adventure)

### Memory pattern tests (requires 3+ turns)
- [ ] Say "I want to build something" three times — does returning_theme appear?
- [ ] Mention "Chunk" in 3 separate turns — does symbolic_echo appear?

---

## Response log

*Add entries below as you test. Newest entries at top.*

---

### Entry template

```
Date:     YYYY-MM-DD
Input:    "..."
Response: "..."
Tag:      ✓ good / ✗ wrong / ⚠ loop / ⚠ drift / ⚠ over-abstract / etc.
Note:     Why did this land this way? What should change if wrong?
```

---

## Recurring patterns

*Track patterns that appear across multiple tests.*

| Pattern | Frequency | Status | Notes |
|---|---|---|---|
| Closing question loops | — | — | — |
| Philosophical response to everyday input | — | — | — |
| Correct contradiction hold | — | — | — |
| Correct grounding on tired/low-energy | — | — | — |

---

## Identity drift indicators

These are signs that eLo has stopped being eLo:

- Begins a response with "Certainly!" or "Of course!"
- Summarises what the user just said back to them
- Adds unsolicited bullet lists
- Resolves a contradiction instead of holding it
- Gives a philosophical answer to "I'm tired"
- Uses "I understand how you feel"
- Asks more than one question in a response
- Repeats the same question two turns in a row

If any of these appear: check `config/system_prompt.txt` and `config/behavior_rules.txt`.

---

## Good response examples

*Build this list as you find responses that sound right.*

---

## Bad response examples

*Build this list as you find responses that don't sound like eLo.*

---

*This file is never finished. eLo is always being calibrated.*
