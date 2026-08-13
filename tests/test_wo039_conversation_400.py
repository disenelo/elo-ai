"""
tests/test_wo039_conversation_400.py — WO-039 stress test (David 2026-08-06)
Feed 400 varied conversation messages through the REAL routing functions
(typo_engine.repair + intent_engine.detect) and flag any garble:
  - a conversational (non-command) line that gets a command word injected by repair, OR
  - a conversational line misclassified as a 'system'/command intent.
Also confirm real commands STILL route to system. Prints a garble rate over 400.
Run: python3 tests/test_wo039_conversation_400.py
"""
import sys, os
sys.path.insert(0, ".")
from runtime.router.typo_engine import repair
from runtime.router.intent_engine import detect

_CMD_WORDS = ("quit", "close", "kill", "exit", "terminate")

def _repaired_text(text):
    r = repair(text)
    if isinstance(r, str): return r
    if isinstance(r, dict):
        for k in ("text", "repaired", "out", "cleaned", "result"):
            if k in r and isinstance(r[k], str): return r[k]
        return str(r.get("text", text))
    return text

# ── Corpus: conversational + TRAP lines (must NOT route to a command) ──────────
conversational = [
 "hey how are you doing today", "good afternoon well almost evening",
 "i slept through most of the day again", "trying to sleep on the floor for my back",
 "we made a lot of progress with you today", "how's the board looking",
 "everything i built is related to the vision", "i built a shirt and printed a pendant yesterday",
 "let's not quit now we're so close", "i was thinking about closing the fashion line for winter",
 "that idea is a real killer feature honestly", "the window of opportunity is closing fast",
 "i want a seat at the table for this decision", "it's hard to sit still when i'm this excited",
 "what is this question even about", "i love how you moved around the screen just then",
 "the weather looks nice for a little walk", "do you remember what we talked about last week",
 "i'm feeling good about where this is going", "you are really coming to life now",
 "something is building and it feels like it's taking shape", "i need a good conversation right now",
 "i've been building this for six or seven months", "we're close to killing the last few bugs",
 "the build looks cleaner after the refactor", "i closed the deal on the studio space",
 "she built her whole brand from scratch", "don't kill the momentum we have going",
 "i quit my old job to do this full time", "the closing scene of that film stuck with me",
 "i built a little shelf for the plants", "we should exit that market segment eventually",
 "the killer app here is the companion itself", "i'm closing my laptop for the night soon",
 "that was a close call with the deadline", "i built up a lot of savings for this",
 "i want to build eLo's body next", "the window on the left has my notes",
 "quitting caffeine has helped my sleep", "i sit by the window most mornings",
 "we built the whole board from the canon", "how do you feel perched up there",
 "i like when you sit on the window it's a nice touch", "the top of the window catches the light",
 "i killed some time reading earlier", "closing thoughts before we wrap up",
 "the exit row has more legroom", "i built a playlist for focus",
 "you were exploring more than waving i think", "where are you on the screen right now",
 "tell me about the company today", "what's on your mind up there",
 "i took a walk to clear my head", "i'm often alone so the walks help",
 "this feels like a real conversation now", "let's keep pressing forward together",
 "the vision is finally coming together", "i want you aware of the company like the architect is",
 "one day you'll sit on your own", "we'll push this through you soon",
]
# TRAP fragments — single/short strings near command words, must NOT fire a command
traps = [
 "built", "building", "rebuilt", "guilt", "quilt", "billed", "called", "killed it",
 "close friends", "closer look", "window seat", "seated", "the sit-down meeting",
 "exit strategy", "killer instinct", "closing time", "built different",
]
# REAL commands — SHOULD route to system/command intent
commands = [
 "quit finder", "close the window", "kill the process", "exit the app",
 "quit spotify", "close chrome", "terminate the script", "quit the browser",
]

# Build a 400-line log: mostly conversational+traps, ~8% real commands.
log = []
i = 0
while len(log) < 400:
    if i % 12 == 11:
        log.append(("cmd", commands[i % len(commands)]))
    elif i % 5 == 4:
        log.append(("conv", traps[i % len(traps)]))
    else:
        log.append(("conv", conversational[i % len(conversational)]))
    i += 1

garbles = []      # conversational lines that misrouted
cmd_missed = []   # real commands that did NOT route
for kind, msg in log:
    try:
        intent = (detect(msg) or {}).get("intent")
    except Exception as e:
        intent = f"ERR:{e}"
    rep = _repaired_text(msg)
    injected = [w for w in _CMD_WORDS if w in rep.lower() and w not in msg.lower()]
    if kind == "conv":
        if intent == "system":
            garbles.append((msg, f"misclassified intent=system"))
        elif injected:
            garbles.append((msg, f"repair injected {injected}"))
    else:  # cmd
        if intent != "system":
            cmd_missed.append((msg, f"intent={intent} (expected system)"))

conv_n = sum(1 for k, _ in log if k == "conv")
cmd_n  = sum(1 for k, _ in log if k == "cmd")
print(f"WO-039 400-message stress test")
print(f"  total messages: {len(log)}  (conversational: {conv_n}, commands: {cmd_n})")
print(f"  GARBLE events (conversational misrouted): {len(garbles)}")
for m, r in garbles[:15]: print(f"    ❌ {m!r} — {r}")
print(f"  commands that failed to route: {len(cmd_missed)}")
for m, r in cmd_missed[:15]: print(f"    ⚠ {m!r} — {r}")
rate = 100.0 * (1 - len(garbles) / max(conv_n, 1))
print(f"  clean conversational rate: {rate:.1f}%")
print("RESULT:", "PASS ✅ (0 garbles, commands route)" if (not garbles and not cmd_missed)
      else f"REVIEW — {len(garbles)} garbles / {len(cmd_missed)} missed commands")
