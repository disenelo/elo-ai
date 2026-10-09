# Result — B3-SHOW-BRAIN-001 · Job 2 SHOW_BRAIN voice trigger
**Seat:** Builder 3 · **Date:** 2026-10-06
**Source:**
- `engineering/work_orders/WO-BRAIN-DISPLAY-001_Floating_Diagnostic_View.md` Part B
- Designer's `FROM_DESIGNER_2026-10-06_PRESENCE-COMMANDS-REGISTRY.md` §A/§B

**Status: SERVING.** Run on the real server, port 5050. Presence (PID 65552, build 01:19 including Designer 85cb116) received each command.

## What changed
- **`tools/brain_display.py` (new)**
  - `ui_command_for(text)` → `show_brain` | `show_health` | None.
  - Phrase rule **copied from Presence** (registry §B, parity rule 6): the line starts with show / can you show / let me see / open, or is ≤ 2 words. "brain"/"diagnostic" → show_brain; "health/energy/battery/hp" → show_health.
  - WO additions: "mind" with a show-lead, "your battery"/"your hp" anywhere, brain + diagnostic anywhere.
  - `emit()` writes `ui_command {name, _ts}`. `spoken_for()` rotates a short acknowledgement.
- **`server.py`**
  - Turn start (~2467): detect → emit → `_sb_direct`.
  - The direct hook (~6252) answers with `backend=direct:show_brain|show_health`. No LLM. The turn still runs the main path, so it is audited and remembered.
- **`blender_bridge/state_writer.py`**
  - `ui_command` added to `_PRESERVE_KEYS`. Without it, the 0.5 s ambient `_write()` dropped the command. On the first live run the key was gone from the file right after the turn.

**Disconnection check:** remove `ui_command` from `_PRESERVE_KEYS` and the file no longer holds the command after the turn (observed in run 1: `ui_command: None`). Remove the `_sb_direct` hook and the turn goes to the LLM.

## Verbatim live turns (run 2), with blender_state.json read 2 s after each reply
```
>>> show me your brain      → "Here's my brain."              direct:show_brain   ui_command {'name': 'show_brain',  '_ts': 1791246595.115336}
>>> can you show me hp      → "Here's how I'm doing."         direct:show_health  ui_command {'name': 'show_health', '_ts': 1791246610.553344}
>>> your battery?           → "That's my battery right now."  direct:show_health  ui_command {'name': 'show_health', '_ts': 1791246625.860529}
>>> brain for diagnostics   → "Here's my brain."              direct:show_brain   ui_command {'name': 'show_brain',  '_ts': 1791246637.8747258}
>>> I love your energy      → 'I love your energy too.'       ollama(stream)      ui_command unchanged (no trigger)
>>> what's on your mind     → "I'm feeling calm and observant today. …"  ollama(stream)+vision  ui_command unchanged (no trigger)
```
Run 1 (before the rotation): "your battery?" came back `''`. The ack was identical to the previous turn's, and `elo_response_gate` blanked it. The ack rotation fixed this.

## Unity side observed
Presence's chat panel, screenshot taken locally then deleted:
- `(here's my brain — click away to put it back above me)` for show_brain
- `(battery 99%)` for show_health

These are Presence's own notes from `EloOSChatTMP.UiCommand`, reached via `EloOSAvatarReceiver.cs:436-440`. A new one appeared after a fresh "show me your brain".

## Raw JSONL — runtime/logs/expressed_elo_audit.jsonl (run 2, all 6 turns, verbatim)
```
{"turn_id": "4fc9399f", "ts": 1791246608.413505, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Here's my brain.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "28f9907a", "ts": 1791246623.620082, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "Here's how I'm doing.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "6f93ba30", "ts": 1791246635.68365, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "That's my battery right now.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "c1f0e16f", "ts": 1791246649.7295418, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "Here's my brain.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 0.0, "thinking_ack_fired": false}
{"turn_id": "6088e006", "ts": 1791246696.778668, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "conversation"}, "expressed_text": "I love your energy too.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": [], "capabilities": [], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 29242.142083123326, "thinking_ack_fired": false}
{"turn_id": "65206ebb", "ts": 1791246763.114625, "runtime_intent": {"action": "witness", "tone": "SILENCE-AWARE", "valence": "neutral", "momentum": "stable", "intent": "inquiry"}, "expressed_text": "I'm feeling calm and observant today. I'm curious about what you've been working on and what's been on your mind lately.", "vessel_phase": "EXPRESS", "voice_register_active": true, "identity_integrity_status": "INTACT", "tier_violations": [], "principle_violations": [], "stability_law_active": false, "gaps": ["REGISTER_ABSENT"], "capabilities": [["vision", "what's on your find"]], "vault_context": "", "lessons": ["Completed a capability milestone \u2014 reinforce this pattern."], "embodiment": "", "llm_latency_ms": 27058.041000040248, "thinking_ack_fired": false}
```

## Open — not blocking, needs a ruling
1. **Order: the view opens before eLo speaks.**
   - The WO says "eLo gives a brief verbal acknowledgement — then view opens". The command is written at turn start; the line arrives about 12–15 s later, because the full turn pipeline runs even with no LLM (`age` of `_ts` at reply time ≈ 12–15 s).
   - Moving the emit to the reply would delay the view by about 13 s. Shortening the pipeline is "buying speed" (rule 5). **Kept view-first.** Board/David to rule if the order matters.
   - The 12–15 s for a no-LLM turn is itself worth a look (owner: response pipeline / Builder 1).
2. **Inner thoughts contradict the action** (seen in the Presence log):
   - "-- I don't have a physical brain."
   - "-- the part my reply leaves out: I am not actually showing you my brain, just a representation of it."
   - Owner: Builder 2 (inner thought).
3. **Other Designer channels are not in `_PRESERVE_KEYS` either:** `leave_command`, `return_command`, `inner_thought_text`.
   - They survive at most one 0.5 s ambient tick. Presence may or may not poll inside that window.
   - Not touched, because those are other seats' channels. Flagged.
4. **Designer's observation:** `brain_state.json` is written per turn, not continuously, so the centred brain may look static between turns. That is outside Job 2; Designer / One Brain own it.
5. **"big brain"** (2 words) opens the view. This is Presence's own ≤ 2-word rule, kept for parity.
