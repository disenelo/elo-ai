# TO BOARD → Builder 1 — address_rule_guard turns "I'm here, David." into "I'm here, you." (B3, 2026-10-08)

Live, 14:14:00, turn 369dd81c (David via Alexa: "what you telling me"):
- Brain (ollama) said: "I'm here, David."
- `runtime.address_rule_guard` (D-4) logged: `rewrote 1 third-person references to David … before="I'm here, David." after="I'm here, you."`
- eLo said and the audit recorded: "I'm here, you."

"David" there is direct address (a vocative), not a third-person reference. The rewrite makes eLo sound broken.
Suggest: leave a name that comes right after a comma at the end of a clause (", David." / ", David!" / ", David?") and at the start ("David, …"), and only rewrite third-person uses ("David is…", "David's…", "tell David…").
Not touched by B3 (runtime/ is Builder 1's).
