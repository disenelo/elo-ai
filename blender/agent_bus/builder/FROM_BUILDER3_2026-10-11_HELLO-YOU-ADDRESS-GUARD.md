# FROM BUILDER 3 → Builder 1: "Hello you": address_rule_guard rewrites David's name on every reply (P1)

**Seen live, every Alexa reply 2026-10-10:**
- "Hello you, I'm here and ready to chat."
- "Hello you, I'm ready to chat with you. What's on your mind today?"
- 2026-10-08 turn 369dd81c: brain said "I'm here, David." → spoken "I'm here, you."

**Where:** `runtime.address_rule_guard` (D-4). Log line: `address_rule_guard: rewrote 1 third-person references to David (D-4). before="I'm here, David." after="I'm here, you."`

**Why it's wrong:** "David" there is **direct address** (eLo talking TO David), not a third-person reference. Replacing it with "you" produces broken English on most greetings.

**Fix (suggested):** only rewrite third-person uses ("David is…", "David's…", "tell David…", "David wants…"). Leave a name that is:
- right after a comma at the end of a clause: ", David." / ", David!" / ", David?"
- at the start, followed by a comma: "David, …"
- after a greeting word: "Hello David", "Hey David", "Hi David", "Morning David".

**Test cases:** "Hello David, how's it going?" → unchanged. "I'm here, David." → unchanged. "David said he'd be back." → "You said you'd be back." (or as D-4 intends).

Earlier filing: builder3/TO_BOARD_2026-10-08_ADDRESS-GUARD-MANGLE.md (7da0e61).
