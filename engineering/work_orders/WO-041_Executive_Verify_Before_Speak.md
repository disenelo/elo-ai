---
id: WO-041
title: "Executive must VERIFY an action before speaking as if it happened (intent != reality)."
owner_seat: SEAT-ENG-001 (Builder / eLo OS — Executive/Agency) + SEAT-ENG-004 (UI: Unity ACK)
priority: P0
review_required: L3 (David — eLo only claims an action after it's confirmed done)
status: OPEN — Chief Architect diagnosis 2026-08-03
epic: "Executive Authority" (root of WO-035, WO-040-A, the conversation-commit bug)
---
# WO-041 — verify-before-speak
## The bug (Chief Architect)
The LLM commits to an action ("I'll sit", "I'm sitting with you") but the action never reaches
embodiment. Dialogue flows `Intent → Speak`. It must flow `Intent → Plan → Execute → Verify → Speak`.
The Executive should never say "I'm sitting" until Unity ACKs `SIT_COMPLETE`, not `SIT_REQUESTED`.
## Fix (Builder Executive/Agency + UI ACK)
1. Action-issuing turns hold the spoken confirmation until the embodiment layer returns a completion
   ACK. On `REQUESTED`/timeout, eLo says it's *trying*, not that it's done.
2. UI/Avatar: emit an ACK (`SIT_COMPLETE` / failed) back through `blender_state`/events so the
   Executive can gate on it. (This is the same arbiter as WO-040/WO-035 — one owner via the ACK.)
## Acceptance
1. eLo only claims an action after a completion ACK. 2. No "I'm sitting" while idle.
