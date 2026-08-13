# → BUILDER — the "command turn" is one broken path, two symptoms (David live 2026-08-05)
Short command inputs ("Sit?", "Seat?") expose ONE broken path with TWO faces:
1. **False "can't reach my thinking" (WO-032).** server.py:2752 fires the degraded line whenever
   `backend_used=="mock"` (line 2739). A command/signal-word turn calls NO real backend → backend_used
   stays "mock" → the guard misfires though nothing failed. FIX: gate the degraded message so it fires
   ONLY on a genuine LLM turn that fell to mock — never on command/greeting/non-LLM turns. (Give command
   turns a proper ack/no-op reply, not the backup line.)
2. **Sit doesn't fire (WO-035/040).** Same turn: eLo narrates "I'll sit"/"perched on the edge" but no
   sit command manifests. (Overloaded 'sit' as idle-mode clip — see WO-035.)
Both live under the command path. Continue WO-039 first; fold these into the Presentable sequence.
