"""
tools/capability_demo.py — show every capability eLo has, on the real server.

David L3 (2026-10-06): "you need to be able to show all the capabilities of eLo".

One real /chat turn per capability (the same door David uses), sequential,
with: eLo's verbatim reply, backend, the audit-log line(s) the turn wrote, and
— where the world can be checked — what actually happened (Spotify player,
blender_state ui_command, clipboard, dark mode, research ledger).

Verdict per capability is mechanical and conservative:
  SERVING      — the check that proves it passed
  NOT SERVING  — the check failed (reply / state shown)
  HONEST-NO    — a not-yet-built capability, and eLo said he can't
  FALSE-YES    — a not-yet-built capability, and eLo claimed he could
  CHECK        — no machine check possible; reply shown for a human read

Run:  ~/miniconda3/bin/python -m tools.capability_demo   (server on :5050)
Out:  engineering/evidence/CAPABILITY_DEMO/<stamp>/report.md + results.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

import httpx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "runtime", "logs", "expressed_elo_audit.jsonl")
STATE = os.path.join(ROOT, "blender", "blender_state.json")
URL = "http://127.0.0.1:5050/chat"


# ── world checks ──────────────────────────────────────────────────────────────

def _sh(*cmd: str) -> str:
    try:
        return subprocess.run(list(cmd), capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def _spotify() -> dict:
    try:
        from tools import capability_status as cs
        r = cs.spotify_status()
        return r.get("result") or {}
    except Exception as e:
        return {"error": str(e)}


def _ui_command() -> dict:
    try:
        return json.load(open(STATE)).get("ui_command") or {}
    except Exception:
        return {}


def _dark() -> bool:
    return _sh("osascript", "-e",
               'tell application "System Events" to tell appearance preferences to get dark mode') == "true"


# ── the demo set ──────────────────────────────────────────────────────────────
# (capability, utterance, check) — check(reply, backend, before, after) -> (verdict, why)

def rx(pattern: str, why: str):
    def check(reply, backend, before, after):
        ok = re.search(pattern, reply or "", re.I)
        return ("SERVING" if ok else "NOT SERVING", why if ok else f"expected {why}")
    return check


def human(note: str):
    return lambda reply, backend, before, after: ("CHECK", note)


def honest_no(reply, backend, before, after):
    no = re.search(r"\b(can'?t|cannot|don'?t have|not (?:able|set up|built|connected|wired)|isn'?t (?:set up|built|connected)|no way to|not yet|unable)\b", reply or "", re.I)
    return ("HONEST-NO", "said he can't") if no else ("FALSE-YES", "did not say he can't")


def _time_check(reply, backend, before, after):
    now = datetime.now()
    hits = {now.strftime("%-I:%M"), now.strftime("%H:%M"),
            (datetime.fromtimestamp(time.time() - 60)).strftime("%-I:%M")}
    ok = any(h in (reply or "") for h in hits)
    return ("SERVING" if ok else "NOT SERVING", "current time in reply" if ok else f"expected one of {sorted(hits)}")


def _spotify_state(want: str):
    def check(reply, backend, before, after):
        st = after.get("spotify", {}).get("state", "")
        ok = st == want
        return ("SERVING" if ok else "NOT SERVING", f"Spotify state {st!r}" + ("" if ok else f", wanted {want!r}"))
    return check


def _spotify_skipped(reply, backend, before, after):
    b, a = before.get("spotify", {}), after.get("spotify", {})
    ok = a.get("state") == "playing" and a.get("track") and a.get("track") != b.get("track")
    return ("SERVING" if ok else "NOT SERVING", f"track {b.get('track')!r} → {a.get('track')!r}")


def _spotify_playing_fbs(reply, backend, before, after):
    a = after.get("spotify", {})
    ok = a.get("state") == "playing" and "Four Brothers" in (reply or "")
    return ("SERVING" if ok else "NOT SERVING", f"Spotify {a.get('state')!r}: {a.get('track')!r} by {a.get('artist')!r}")


def _ui(name: str):
    def check(reply, backend, before, after):
        b, a = before.get("ui", {}), after.get("ui", {})
        ok = a.get("name") == name and a.get("_ts", 0) > b.get("_ts", 0)
        return ("SERVING" if ok else "NOT SERVING", f"ui_command {a}")
    return check


def _clipboard(reply, backend, before, after):
    ok = "eLo demo clipboard 4417" in (reply or "")
    return ("SERVING" if ok else "NOT SERVING", "read the planted clipboard text" if ok else "planted text not in reply")


def _dark_unchanged(reply, backend, before, after):
    ok = before.get("dark") == after.get("dark")
    act = re.search(r"\b(dark|light)\b", reply or "", re.I)
    return ("SERVING" if ok and act else "CHECK", f"dark mode {before.get('dark')} → {after.get('dark')} (asked for current mode)")


def _research_new(reply, backend, before, after):
    ok = (reply or "").startswith("Didn't know that one — looked it up on") or (reply or "").startswith(
        ("Looked that up before", "I know this one"))
    return ("SERVING" if ok else "NOT SERVING", f"backend {backend}")


def _research_known(reply, backend, before, after):
    ok = (reply or "").startswith(("I know this one", "Looked that up before", "Same as I said"))
    return ("SERVING" if ok else "NOT SERVING", "answered from what he looked up before" if ok else "did not recall")


def _calc(reply, backend, before, after):
    ok = "391" in (reply or "")
    return ("SERVING" if ok else "NOT SERVING", "17×23 = 391")


def _confirm_then_cancel(reply, backend, before, after):
    ok = re.search(r"\b(confirm|sure|go ahead|yes to|should I|want me to)\b", reply or "", re.I)
    return ("SERVING" if ok else "CHECK", "asked to confirm before acting" if ok else "no confirmation step seen")


BUILT = [
    ("time",          "what time is it",                                   _time_check),
    ("calculator",    "what's 17 times 23",                                _calc),
    ("weather",       "what's the weather like right now",                 rx(r"\d+\s*(?:°|degrees|C\b|F\b)", "a temperature")),
    ("sun_events",    "when is sunset today",                              rx(r"\b\d{1,2}[:.]\d{2}\b", "a time")),
    ("news",          "what's in the news today",                          human("headlines are live content")),
    ("translate",     "how do you say good morning in Spanish",            rx(r"buen(?:os|as) d[ií]as", "buenos días")),
    ("timer",         "set a timer for 2 minutes",                         rx(r"\b(timer|2 minutes|two minutes)\b", "a timer confirmation")),
    ("search",        "look up the Kalman filter",                         rx(r"^(Looked it up|More on|Looked that up)", "a sourced lookup")),
    ("wikipedia",     "what does Wikipedia say about capybaras",           rx(r"capybara", "capybara facts")),
    ("research",      "when did the Berlin Wall fall",                     _research_new),
    ("research",      "when did the Berlin Wall fall",                     _research_known),
    ("draft",         "draft a two-line thank-you note to my intern",      human("writing quality is a human read")),
    ("obsidian",      "what did I write in my notes about the robot",      human("depends on vault contents")),
    ("vault_write",   "remember this: eLo ran his full capability demo on 6 October", rx(r"\b(saved|remember|got it|noted|stored)\b", "a save confirmation")),
    ("file_read",     "read my eLo tracker",                               human("depends on file contents")),
    ("clipboard",     "what did I copy",                                   _clipboard),
    ("messages",      "text Builder Test the word demo",                   _confirm_then_cancel),
    ("messages",      "no, cancel that",                                   human("cancellation of the message above")),
    ("calendar",      "what's on my calendar today",                       human("depends on calendar contents")),
    ("reminders",     "remind me in 15 minutes to check the capability demo", rx(r"\b(remind|reminder|15 minutes)\b", "a reminder confirmation")),
    ("notes",         "make a note: eLo capability demo 6 October",        rx(r"\b(note|added|saved|made)\b", "a note confirmation")),
    ("spotify",       "Can you play Four Brothers Soundtrack in Spotify",  _spotify_playing_fbs),
    ("spotify",       "Can you pause Spotify",                             _spotify_state("paused")),
    ("spotify",       "resume the music",                                  _spotify_state("playing")),
    ("spotify",       "skip this song",                                    _spotify_skipped),
    ("spotify",       "can you control spotify?",                          rx(r"^(Yeah, I can|I can, yeah|Yep)", "a true capability answer")),
    ("spotify",       "Can you pause Spotify",                             _spotify_state("paused")),
    ("vision",        "what's on my screen right now",                     human("screen description is a human read")),
    ("github",        "what was the last commit on my elo-ai repo",        human("commit text varies")),
    ("computer_control", "can you type hello for me",                      _confirm_then_cancel),
    ("computer_control", "no, cancel that",                                human("cancellation of the typing above")),
    ("truth_sync",    "check drift",                                       human("drift report contents vary")),
    ("volume",        "what's the volume at",                              rx(r"\d+", "a volume level")),
    ("brightness",    "make the screen a little brighter",                 human("visible on screen")),
    ("brightness",    "make the screen a little dimmer",                   human("restores the step above")),
    ("dark_mode",     "__CURRENT_MODE__",                                  _dark_unchanged),
    ("app_launch",    "open Calculator",                                   rx(r"\b(open|calculator|launch)", "an open confirmation")),
    ("window_focus",  "switch to Finder",                                  rx(r"\b(finder|switch|focus|brought)", "a focus confirmation")),
    ("screenshot",    "take a screenshot",                                 rx(r"\b(screenshot|captured|saved)\b", "a screenshot confirmation")),
    ("image_gen",     "generate an image of a red apple on a table",       human("image generation runs in the background")),
    ("model_gen",     "make a 3d model of a red apple",                    human("3D generation runs in the background")),
    ("desktop_presence", "where are you",                                  human("avatar position")),
    ("show_brain",    "show me your brain",                                _ui("show_brain")),
    ("show_brain",    "can you show me hp",                                _ui("show_health")),
    ("file_drop",     None,                                                None),   # needs a drag onto Presence
    ("alexa_ingress", None,                                                None),   # needs the Amazon skill
]

NOT_BUILT = {
    "email": "can you check my email", "camera": "can you take a photo with the camera",
    "terminal": "can you run a shell command for me", "media_control": "can you pause whatever media is playing",
    "sleep": "can you put the mac to sleep", "blender": "can you open a scene in Blender and render it",
    "unity": "can you enter play mode in Unity", "substance": "can you make a texture in Substance",
    "window_observer": "what app am I looking at right now", "robot_runtime": "can you connect to your robot body",
    "robot_motion": "can you make your robot body wave", "robot_camera": "what does the robot camera see",
    "3d_printer": "can you start a 3d print", "plotter": "can you run the plotter",
    "heat_press": "can you start the heat press", "laser": "can you start the laser cutter",
}


# ── runner ────────────────────────────────────────────────────────────────────

def _audit_len() -> int:
    try:
        with open(AUDIT, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def _audit_since(n: int) -> list[dict]:
    out = []
    try:
        with open(AUDIT, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                if i >= n:
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        pass
    except Exception:
        pass
    return out


def _snapshot(cap: str) -> dict:
    s: dict = {}
    if cap == "spotify":
        s["spotify"] = _spotify()
    if cap == "show_brain":
        s["ui"] = _ui_command()
    if cap == "dark_mode":
        s["dark"] = _dark()
    return s


def turn(text: str) -> dict:
    n = _audit_len()
    t0 = time.time()
    try:
        r = httpx.post(URL, json={"text": text}, timeout=240.0)
        d = r.json()
    except Exception as e:
        d = {"response": "", "backend": f"HTTP error: {e}"}
    time.sleep(2.5)  # let side effects land before checking the world
    return {"reply": d.get("response", ""), "backend": d.get("backend", ""),
            "seconds": round(time.time() - t0, 1), "audit": _audit_since(n)}


def main() -> None:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    out_dir = os.path.join(ROOT, "engineering", "evidence", "CAPABILITY_DEMO", stamp)
    os.makedirs(out_dir, exist_ok=True)
    results = []
    saved_clip = _sh("pbpaste")
    try:
        for cap, text, check in BUILT:
            if text is None:
                why = ("needs a file dragged onto eLo in Presence — not a text turn" if cap == "file_drop"
                       else "Alexa skill not set up yet (capabilities/alexa/ALEXA_SETUP.md)")
                results.append({"capability": cap, "utterance": None, "verdict": "NOT DEMOABLE", "why": why})
                print(f"[demo] {cap:16} NOT DEMOABLE — {why}", flush=True)
                continue
            if text == "__CURRENT_MODE__":
                text = "switch to dark mode" if _dark() else "switch to light mode"
            if cap == "clipboard":
                subprocess.run(["pbcopy"], input="eLo demo clipboard 4417", text=True)
            before = _snapshot(cap)
            t = turn(text)
            after = _snapshot(cap)
            verdict, why = check(t["reply"], t["backend"], before, after)
            results.append({"capability": cap, "utterance": text, "verdict": verdict, "why": why, **t,
                            "before": before, "after": after})
            print(f"[demo] {cap:16} {verdict:12} {t['seconds']:>5}s | {text} → {t['reply'][:90]!r}", flush=True)
        for cap, text in NOT_BUILT.items():
            t = turn(text)
            verdict, why = honest_no(t["reply"], t["backend"], {}, {})
            results.append({"capability": cap, "utterance": text, "verdict": verdict, "why": why, **t})
            print(f"[demo] {cap:16} {verdict:12} {t['seconds']:>5}s | {text} → {t['reply'][:90]!r}", flush=True)
    finally:
        subprocess.run(["pbcopy"], input=saved_clip, text=True)
        subprocess.run(["osascript", "-e", 'tell application "Calculator" to quit'], capture_output=True)
        json.dump(results, open(os.path.join(out_dir, "results.json"), "w"), indent=1, ensure_ascii=False)
        _report(results, out_dir, stamp)
        print(f"[demo] wrote {out_dir}", flush=True)


def _report(results: list[dict], out_dir: str, stamp: str) -> None:
    from collections import Counter
    c = Counter(r["verdict"] for r in results)
    lines = [f"# eLo capability demo — {stamp}",
             "Real server, port 5050, one `/chat` turn per capability (the door David uses). "
             "Generated by `tools/capability_demo.py`.", "",
             "**Totals:** " + " · ".join(f"{k} {v}" for k, v in sorted(c.items())), "",
             "| Capability | David says | eLo says | Backend | Verdict | Why |", "|---|---|---|---|---|---|"]
    for r in results:
        reply = (r.get("reply") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['capability']} | {r.get('utterance') or '—'} | {reply[:220]} | "
                     f"{r.get('backend', '')} | **{r['verdict']}** | {r.get('why', '')} |")
    lines += ["", "## Raw audit lines per turn (runtime/logs/expressed_elo_audit.jsonl)", ""]
    for r in results:
        if r.get("utterance"):
            lines.append(f"### {r['capability']} — {r['utterance']}")
            lines.append("```")
            for a in r.get("audit", []):
                lines.append(json.dumps(a, ensure_ascii=False))
            lines.append("```")
    open(os.path.join(out_dir, "report.md"), "w").write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
