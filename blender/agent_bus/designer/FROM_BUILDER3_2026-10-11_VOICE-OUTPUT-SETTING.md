# FROM BUILDER 3 → Designer: Presence setting "eLo's voice: Mac / Alexa speaker"

Full spec: `blender/agent_bus/FROM_BOARD_REQUEST_2026-10-10_DESIGNER-VOICE-OUTPUT-SETTING.md`. Summary:

**David, 2026-10-10:** "in settings… where I can choose Alexa or Mac, as I want to test. I don't want all my audio coming through the Bluetooth speaker, just eLo."

1. Add a setting: **eLo's voice: [ Mac ] [ Alexa speaker ]**, default Mac.
2. On change **and once at every launch**, append to `blender/unity_events.json`:
   `{"type": "voice_output", "subject": "mac" | "echo", "action_id": "", "payload": {"issued_by": "david"}, "_ts": <unix seconds>}`
3. Nothing else changes: lipsync/bubbles as now. The brain moves only eLo's voice to the Echo (Mac output untouched) and falls back to the Mac if the Echo isn't connected.

Note: when David talks through Alexa with the Echo connected, the brain also sends that reply to the Echo for a minute (68910a8, "contextual output"). David's setting governs everything else.
