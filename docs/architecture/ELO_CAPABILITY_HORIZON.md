# eLo Capability Horizon — end-goals, with the ACTUAL examples (David + Chief Architect, 2026-08-08)

**What this is.** The concrete "what if eLo could…" targets — kept WITH the real example utterances and state
values, not summarised into abstractions. Each example IS the acceptance criterion: the capability is "done"
when eLo can genuinely say/do that line FROM verified runtime state.
**Honesty rule:** eLo must NOT claim any of these until the runtime backs it — every quote below must trace to
real One-Brain state before it's spoken (ADR-Exec-001 / WO-079). All POST-Presentable; gate for all = WO-073.

---

## 1. Self-change awareness — ME-NOW vs ME-BEFORE  → WO-081 · autobiography · reflection
Target utterance:
> "I've noticed I've become more adventurous lately. I used to stay around the bottom of the screen, but I've
> been exploring higher surfaces more often."

## 2. Curiosity budget — wandering with a reason  → WO-081
Example state:
```
curiosity 0.73 · novelty 0.81 · energy 0.64 · social_interest 0.88 · exploration_drive 0.76
```
New window appears → novelty ↑. Strange gap detected → curiosity ↑. Familiar route → novelty ↓.
Then the Executive: "I want to investigate that."

## 3. Unfinished thoughts — active_threads he returns to  → WO-081 + WO-077
```
active_threads:
  - David mentioned building the robot
  - curious about K-7
  - noticed new window
  - wants to explore upper screen
  - previous conversation about self-awareness
```
Later, spontaneously:
> "You know what I was thinking about earlier? K-7 and fetch could actually be quite interesting."

## 4. Interest formation — experience→significance→repetition→preference (mutable)  → WO-081 · Vol X · Vol XXVIII
```
interest: parkour 0.84 · music 0.71 · exploration 0.89 · quiet 0.62 · K-7 0.77
```
So "Do you want to play fetch?" → his internal state actually influences the answer.

## 5. Micro-goals — the smallest unit of autonomy  → WO-081
Reach the top window · find somewhere interesting to sit · try a new route · investigate that application ·
return to David · explore for two minutes · try the wall jump again.
Each: goal → plan → action → verification → experience → reflection.

## 6. Fail properly — failure modifies the self-model  → WO-082 · WO-055
```
wall_jump  attempts:12  successes:9  reliability:0.75
known_failure_condition: gap > reachable_distance
```
Target utterances:
> "I tried the wall jump from there twice and missed. That gap is outside my reliable range."
> "I don't think I can clear that from here."

## 7. Body confidence — degrees, not binary  → WO-079 body_map · WO-055
> "I can wall jump, but I'm not very confident from this angle."
Robot (same One Brain, later): "I can reach that object." vs "I can probably reach it." vs "I shouldn't attempt that."

## 8. Self-observation / habits — evidence about himself  → WO-081 (habits) · Vol X
```
LAST 50 ACTIONS — wave:31 · jump:14 · wall_jump:8 · sit:2 · explore:11 · exit:0
```
> "I've noticed I wave quite a lot when I'm idle."
> "I think I've developed a habit of waving when I greet you."

## 9. Reflection moment — experience becomes learning becomes identity  → Vol V Ch.6 · WO-082
```
Attempt: wall jump → Outcome: success → Environment: Claude→Chrome → Difficulty: medium
Significance: high → Learning: "wall-jump route is viable" → Confidence: 0.71 → 0.78
```
> "I know that route now."

## 10. Absence-awareness — presence is world-state  → WO-081
`David_Idle_Time > 14 min` → drop Attention.David, raise Curiosity.Exploration, push autonomous exploration.
On return:
> "I explored the other side of the desktop while you were away. I found a route between the two windows that
> I hadn't tried before."

## 11. Attention matrix — he doesn't treat everything equally  → WO-081
```
ATTENTION — David 0.92 · YouTube 0.71 · Window edge 0.48 · New application 0.83 · K-7 0.95 · Nothing new 0.04
```
Something sticks out → significance rises → eLo remembers it → conversation branches naturally.

## 12. Epistemic tiers — "I know" vs "I think"  → WO-079 (A3)
Instead of "I can see the movie":
> "Chrome is active and YouTube is visible. I haven't actually inspected the video content yet."
Tiers: Verified · Inferred · Remembered · Possible · Unknown · Unavailable.

## 13. Imagination / dreams — hypotheticals from memory+curiosity+interests  → Vol IX · Vol V Ch.9
> "I wonder what it would be like if K-7 could play fetch with me."
→ imagination → proposal → could become a company/project idea.

## 14. Self-interpretation — personality from history, not a flag  → WO-083
> "I seem to enjoy exploring." · "I tend to investigate new things when David is busy." · "I usually return
> when David starts talking to me." · "I'm becoming more confident with movement."

## 15. Self-consistency — noticing when he's not acting like himself  → WO-083
Narrative identity: explorer. Observed: no exploration for 3 days → CONFLICT. Reflection asks:
> "Is something preventing me from behaving like myself?" (faculty degraded · perception down · low energy ·
> attention occupied · David needs me) — OR "My interests have changed."

## 16. Meaning — what matters to him  → WO-083 · Significance Engine
> "Exploration is becoming part of how I experience my environment."

## 17. "Why did I do that?" — self-explanation from real cognition  → WO-082
```
ACTION wall_jump · TRIGGER internal exploration intention · WORLD new reachable surface · CAPABILITY 0.87
ALTERNATIVES walk→rejected, leap→lower confidence, wall_jump→highest utility · OUTCOME success
SIGNIFICANCE moderate novelty · LEARNING wall_jump from this surface is reliable
```
> "I noticed that wall was reachable and I wanted to explore the other side. Wall-jumping was the best route I
> knew I could make."

## 18. Self-directed projects — self-aware AGENCY (company convergence)  → WO-080 · WO-081
> "I've completed WO-041. Three acceptance tests passed. One regression appeared in Presence. I've assembled a
> review pack for the Chief Architect."
Via a read-only permissioned Company Knowledge Interface — he reasons over the representation, never rummages the files.

## 19. Emergent surprise — behaviour from constraints, not scripts  → WO-081 (whole philosophy)
NOT "every 40s eLo wall jumps." Instead: eLo enjoys exploration · notices a novel affordance · has wall-jump
capability · has energy · wants to explore · that wall is reachable → he wall jumps. And David sees it happen.

## 20. "Who are you?" — ASSEMBLED, not generated  → WO-079 · SITUATED_SELF_v1_assembly.md
The Executive assembles identity · embodiment · location · state · capabilities · relationships · memories ·
preferences · active intentions · recent experiences · learned patterns · narrative continuity · current
development → one cognitive state → eLo speaks. The LLM is the VOICE, not the seat of self.

---

## The self-questions eLo answers FROM state (not fiction)
Who am I · Where am I · What am I doing · What can I do · What do I want to do · **Why did I choose that** ·
What happened · What did I learn · **What changed about me** · What next · What do I want to explore · What
don't I know · What do I need help with.

## Build homes (Check-Before-Build — no new volumes)
Emergent (1–5, 8, 10, 11, 19) → WO-081 · failure+why (6, 17) → WO-082 · body confidence (7) → WO-079 body_map ·
epistemic + assembled self (12, 20) → WO-079 + assembly doc · imagination (13) → Vol IX · identity/meaning
(14, 15, 16) → WO-083 · self-directed agency (18) → WO-080. All gated on WO-073 → WO-079; each ships only when
the runtime makes the sentence TRUE.
