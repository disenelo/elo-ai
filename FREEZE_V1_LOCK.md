# FREEZE_V1_LOCK.md — eLo OS Recovery v1

**Declared**: 2026-06-29
**Authority**: Recovery Execution Plan — RETURN TO SIGNAL
**Status**: ACTIVE

---

## What is frozen

The following are immutable until explicitly unlocked. No session may alter these without recording the unlock reason and the new state in §Unlock Log below.

### 1. Identity
**File**: `prompts/living_presence_spec.txt`
**Frozen sections**: CHARACTER DNA, IDENTITY, PLANETARY LAYER
**Core**: eLo is calm, curious, playful, direct, emotionally present. Accidental comedian — not because he tells jokes, but because he means everything completely. Adventurer energy. Light mischief at the edges.
**What cannot change**: these traits, this register, this relationship to the user.

### 2. Voice
**File**: `prompts/living_presence_spec.txt`
**Frozen sections**: VOICE STATES (5 tones: SILENCE-AWARE, WITTY, DIRECT, JOYFUL, CHILDLIKE-WISE)
**Core**: exactly 5 tones. WITTY = observational/impish register, not sarcasm. CHILDLIKE-WISE = default grounded presence.
**What cannot change**: the 5-tone model, the register descriptions.

### 3. Attention
**File**: `core/attention.py`
**Core**: intent / valence / momentum three-dimensional model. Embedding boost. HIGH / MEDIUM / LOW priority memory tiers.
**What cannot change**: the three-dimensional model, the tier structure.

### 4. Memory Rules
**File**: `prompts/living_presence_spec.txt` — MEMORY PRINCIPLE
**Core**: Memory is meaning, not transcripts. Remember recurring projects, values, emotions, goals. Forget conversational clutter.
**What cannot change**: this principle. Strategic forgetting is a future phase decision — do not add it now.

### 5. Conversation Rules
**File**: `prompts/living_presence_spec.txt` — CONVERSATION ACTION RULE
**Core**: 9 CAL actions (ANSWER, BUILD, CONNECT, CELEBRATE, REFLECT, GROUND, CHALLENGE, WITNESS, SILENCE). POSITIVE MOMENTUM RULE. OBSERVATION RULE. CONTRIBUTION RULE (added Phase 04).
**What cannot change**: the 9 actions, the positive momentum rule.

---

## What is forbidden during freeze

- New tools or agents
- New CAL actions
- New memory systems
- New ambient behaviors
- New Unity contracts
- New FORBIDDEN entries in prompt_builder.py (unless replacing one being removed)
- New world graph entities or viewpoints

---

## Recovery phases

| Phase | Description | Duration | Status |
|-------|-------------|----------|--------|
| 01 | FREEZE — this document | 1 session | ✅ 2026-06-29 |
| 02 | Remove response defensiveness | 1–2 sessions | ✅ 2026-06-29 |
| 03 | Reduce context injection | 2 sessions | ✅ 2026-06-29 |
| 04 | Restore contribution | 2 sessions | ✅ 2026-06-29 |
| 05 | Rebuild positive states | 1 session | ✅ 2026-06-29 |
| 06 | Presence before movement | 2 sessions | 🔴 pending |
| 07 | Relationship (limited) | 2 sessions | 🔴 pending |
| 08 | Silence restore | 1 session | 🔴 pending |
| 09 | 100 session test | ongoing | 🔴 pending |
| 10 | Avatar gate | gated | 🔴 pending |

---

## Avatar gate — DO NOT PASS UNTIL

Identity: 9/10
Conversation: 9/10
Contribution: 8/10
Presence: 8/10

Only then: Unity expansion, Desktop expansion, Robot.

---

## Unlock protocol

To unlock a frozen element:
1. Name the specific element being changed.
2. State why the freeze was wrong or why the change serves recovery.
3. Record the unlock below under §Unlock Log.
4. Make the change.

---

## Unlock Log

| Date | Element changed | File | Why | Authority |
|------|----------------|------|-----|-----------|
| 2026-08-21 | Added `"You mentioned…"` to the existing anti-mirroring example list | `prompts/living_presence_spec.txt` lines 243-248 | Genuine phrase gap — `"I notice"` and `"it feels like you're"` were listed; `"You mentioned"` was absent. This is NOT one of the 9 CAL actions or the positive momentum rule (§5 frozen). Extends an existing rule, no new list or new action. | AUTHORISED card 0062, task 2 |

---

## Success condition

The user says: "It feels like eLo again."
Not: "It answers correctly."
