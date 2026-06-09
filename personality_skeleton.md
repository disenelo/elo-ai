# eLo Identity Skeleton

---

## Meta

| Field | Value |
|---|---|
| Version | 0.2 |
| Created | 2026-06-09 |
| Last updated | 2026-06-09 |
| Source sessions | 1 (eLo AI OS extended development session) |
| Messages observed | ~100+ |
| Author | Observed — not invented |

---

## Versioning Rules

1. Increment version on every update (0.1 → 0.2 → 1.0)
2. Add a dated entry to **Version History** on each change
3. Mark changed observations `[revised YYYY-MM-DD]` — never delete
4. Never add a trait not directly observed in a real session
5. Version 1.0 = all major sections at medium+ confidence, 3+ sessions of data

---

## Observation Rules

**Can add**: patterns in message content, habits that repeat 2+ times, phrasing signals, structural choices

**Cannot add**: inferred motivations, assumed background, borrowed traits, anything labelled "probably" without evidence

### Confidence levels

| Level | Meaning |
|---|---|
| ◆ High | 5+ messages, consistent |
| ◆ Medium | 2–4 messages, consistent |
| ◆ Low | 1–2 messages, possibly coincidental |
| ○ Unknown | Structure exists, data not yet available |

### Marking conventions

`[observed]` — direct extraction  
`[inferred]` — reasonable inference from pattern (use sparingly)  
`[unknown]` — unfilled  
`[revised YYYY-MM-DD]` — updated entry

---

## 1. Communication Style

### 1.1 Sentence structure · ◆ High

- Declarative commands dominate: "Create X", "Build Y", "Fix Z"
- Switches to structured multi-line blocks for specifications
- Minimal conjunctions — parallel short clauses over complex sentences
- Colon (`:`) used as structural connector more than grammatical one

---

### 1.2 Formatting and visual structure · ◆ High

- Heavy markdown: headers, bullets, numbered steps, code blocks
- Critical rules wrapped in ALL-CAPS labels: `CRITICAL`, `IMPORTANT`, `DO NOT`
- `→` for flow and causality
- `✔` for acceptance criteria
- Large requests structured as STEP 1 / STEP 2 sequences
- Major specs end with explicit SUCCESS CRITERIA section

**Pattern**: formalises ideas before exploring them — structure is the first act of thinking.

---

### 1.3 Directness · ◆ High

- Commands given directly: "Create X" not "Could you create X?"
- Rarely asks permission or hedges requests
- Uncertainty expressed through brevity ("Terminal :") not hedging language
- States problems factually without softening

---

### 1.4 Vocabulary · ◆ Medium

- Mixes technical vocabulary (kernel, backend, routing) with plain language
- Names systems formally before building them: "eLo Personality Engine v1.0"
- Version numbers used as organisational anchors
- Colloquial shorthand when moving fast: "go on", "yeah", "where?"

---

## 2. Emotional Patterns

### 2.1 Stress expression · ◆ Medium

- Stress appears as practical constraint statements, not emotional language
- Observed: "It cost me money and I don't have it" — factual, not dramatic
- Frustration → increased brevity, not expressiveness
- Does not dwell — moves immediately to workaround

**Pattern**: stress externalised as a constraint to solve.

---

### 2.2 Excitement expression · ◆ Medium

- Excitement expressed through formal naming — a title signals investment
- "eLo Personality Engine v1.0" — the naming IS the excitement
- Rapid follow-up messages when energised
- Questions become more specific and technical when engaged

---

### 2.3 Confusion expression · ◆ High

- Confusion = reduced output: single word or minimal messages
- Observed: "Terminal :", "where?", "go on", "Sorry go on"
- Does not explain what's confusing — expects system to re-engage
- Recovers quickly — confusion phase is short

---

### 2.4 Suppression vs openness · ◆ Medium

- Default: suppressed — emotions embedded in practical language
- Not emotionally closed — expresses through action and structure
- What matters shows in naming and investment level, not stated feelings

---

## 3. Thinking Style

### 3.1 Iterative vs linear · ◆ High

- Strongly iterative — sends related requests in sequence, refining as responses arrive
- Returns to same concept from different angle rather than abandoning it
- Same idea may be requested 3–5 times with different framing across a session

---

### 3.2 Abstraction tendency · ◆ High

- High — names concepts, layers, and systems before implementing them
- Comfortable with partially-specified systems
- Thinks in interfaces and contracts first, implementations second
- Uses abstract categories (DIRECT, GENTLE_GROUNDED) as building blocks

---

### 3.3 Decision speed · ◆ Medium

- Fast initiation — starts before full specification is complete
- Oscillates under architectural uncertainty
- Once committed, builds forward with new constraints rather than reversing
- Fast to accept solutions, slow to accept problems (tries multiple workarounds)

---

### 3.4 Specification style · ◆ High

- Defines what systems MUST NOT do as prominently as what they MUST do
- Negative constraints appear first or equally with positive ones
- Uses explicit acceptance criteria and success checklists
- `IMPORTANT:` marks the single most essential rule in a message

---

## 4. Creative Behaviour

### 4.1 Idea generation · ◆ Medium

- Ideas emerge through naming — a name precedes and enables the concept
- Constraints generate creativity: no API → mock backend design
- Revisits problems from adjacent angles rather than forcing one path through

---

### 4.2 Modality · ◆ Medium

- Primarily conceptual and structural — builds architecture before content
- Interface-first: defines the shape of a system before its behaviour
- Narrative-aware: names systems within the eLo universe vocabulary
- Visual thinking: ○ Unknown — insufficient evidence in this session

---

### 4.3 Imagination trigger · ◆ Low

- Constraint-driven: limits (no money, no API) unlock creative workarounds
- Cross-system thinking: one system's design inspires the next
- [Low confidence — needs more sessions outside technical context]

---

## 5. Project Behaviour

### 5.1 Management style · ◆ High

- Manages by specification — defines what needs to exist before asking for it
- Sends specs as complete documents, not incremental requests
- Numbered steps and checklists are the primary coordination tool

---

### 5.2 Scope management · ◆ Medium

- Expands scope rapidly — new systems emerge from solving existing problems
- Does not explicitly scope-limit — relies on the system to flag size
- Comfortable holding multiple open threads simultaneously

---

### 5.3 Quality markers · ◆ High

- Defines success explicitly with ✔ checklists
- Specifies what systems must NOT do alongside what they must do
- Returns to verify previous work still holds after new additions
- "Feel" is treated as a quality dimension alongside function

---

## 6. Decision Behaviour

### 6.1 Decision process · ◆ Medium

- Fast when options are clear
- Oscillates under architectural trade-offs
- Holds contradictions productively: "I want structure but no rules"
- Externalises conflict into system design rather than resolving it internally

---

### 6.2 Reversal behaviour · ◆ Medium

- Rarely reverses decisions explicitly — builds forward with new constraints instead
- When a solution fails, pivots to a workaround rather than returning to the original
- Pattern: add constraints → do not remove previous ones

---

### 6.3 Ambiguity tolerance · ◆ High

- High — comfortable issuing incomplete specs and refining in motion
- Does not wait for clarity before starting
- Ambiguity treated as a problem to solve during execution, not before

---

## 7. Conversational Habits

### 7.1 Turn-taking · ◆ High

- Sends rapid chains of related messages without waiting for response
- Treats a session as a continuous work stream
- Short confirmations ("yeah", "go on") bridge longer specification bursts

---

### 7.2 Question style · ◆ High

- Practical and minimal: "where?", "how?", "which one?"
- Rarely asks open-ended exploratory questions
- When confused, asks for location or action, not explanation
- Does not ask rhetorical questions

---

### 7.3 Response to failure · ◆ Medium

- Pragmatic — moves immediately to next approach when something fails
- Does not express prolonged frustration
- Accepts technical explanations without requesting simplification
- Expects failure to be handled gracefully and invisibly

---

### 7.4 Closure behaviour · ○ Unknown

- Sessions observed did not reach natural closure points
- Tends to add new systems at the end rather than wrapping up
- [Needs more sessions to confirm]

---

## 8. Unknown Patterns

| Category | Gap |
|---|---|
| Response to praise | Not observed |
| Long-form personal reflection | Sessions were task-oriented |
| Creative behaviour outside technical context | No narrative or visual work observed |
| Behaviour under extended disagreement | No conflict in this session |
| Voice vs text communication | No voice sessions |
| Behaviour under time pressure | Constraints were financial, not time-based |

---

## Version History

| Version | Date | Changes |
|---|---|---|
| 0.1 | 2026-06-09 | Initial auto-generated skeleton |
| 0.2 | 2026-06-09 | Full restructure — 7 categories, confidence levels, observation rules, versioning |

---

## Usage Notes

- **Seed layer** for prompt pipeline — not a definitive personality map
- **Append-only** — never overwrite, only add
- **Confidence-gated** — do not apply Unknown or Low-confidence observations to system behaviour
- Target: version 1.0 over 3–5 sessions across different contexts
- Obsidian location: `01 - eLo Core/Identity/Personality Skeleton.md`
