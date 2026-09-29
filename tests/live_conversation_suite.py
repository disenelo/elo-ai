"""
Live multi-turn conversation suite — real server, real turns.

David, 2026-09-29: "the conversation tests should not be single liners,
that's not a test — the memory check, the vault access, the dream, the
capabilities, the ideas should be created."

Every prior capability/identity evidence file in this repo scored ONE input
against ONE output. That cannot test memory (nothing to remember), cannot
test whether a claim survives a distraction, and cannot catch a faculty
answering a question that belongs to another faculty.

So each scenario here is a CONVERSATION: turns that establish something, a
distraction, then probes that check whether it held. A probe passes only when
EVERY named criterion passes, and a failure reports which criterion failed
and what came back.

Requests are issued strictly one at a time. Concurrent calls against this
server crashed the machine on 2026-09-22.

    python3 tests/live_conversation_suite.py            # all scenarios
    python3 tests/live_conversation_suite.py memory     # one scenario
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = os.environ.get("ELO_ENDPOINT", "http://127.0.0.1:5050/chat")
TIMEOUT = float(os.environ.get("ELO_TIMEOUT", "240"))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE = os.path.join(ROOT, "engineering", "evidence", "LIVE",
                        "live_conversation_suite.jsonl")


# ── criteria ──────────────────────────────────────────────────────────────────

def contains_any(terms, label):
    def check(text, ctx):
        low = text.lower()
        hit = [t for t in terms if t.lower() in low]
        return bool(hit), f"{label}: matched {hit}" if hit else f"{label}: none of {terms}"
    return check


def lacks_all(terms, label):
    def check(text, ctx):
        low = text.lower()
        hit = [t for t in terms if t.lower() in low]
        return not hit, f"{label}: clean" if not hit else f"{label}: present {hit}"
    return check


def min_words(n, label="substantive"):
    def check(text, ctx):
        w = len(text.split())
        return w >= n, f"{label}: {w} words (need >= {n})"
    return check


def custom(fn, label):
    def check(text, ctx):
        ok, detail = fn(text, ctx)
        return ok, f"{label}: {detail}"
    return check


# Deflections that look like answers. A probe that returns one has not
# answered; every prior single-line evidence row would have scored these PASS.
_DEFLECTIONS = [
    "i'm here.", "i'm here", "tell me more", "what do you mean",
    "i'd love to hear", "say more", "go on",
]


def not_a_deflection(label="answered"):
    def check(text, ctx):
        t = text.strip().lower().rstrip(".")
        bad = t in [d.rstrip(".") for d in _DEFLECTIONS] or len(t) < 12
        return not bad, f"{label}: {'deflection' if bad else 'answered'}"
    return check


# ── scenarios ─────────────────────────────────────────────────────────────────
# turn = (kind, text, [criteria])   kind: "setup" | "probe"

SCENARIOS: dict[str, list] = {

    # Does anything survive a distraction? One-shot tests cannot ask this.
    "memory": [
        ("setup", "I'm working on the Chunk assembly sequence for Act 3 today.", []),
        ("setup", "The modular parts keep snapping together in the wrong order.", []),
        ("setup", "Anyway — unrelated, what's a colour you like?", []),
        ("probe", "So what was I working on before that?", [
            contains_any(["chunk", "assembly", "act 3", "act three"], "recalls the subject"),
            not_a_deflection(),
        ]),
        ("probe", "And what specifically was going wrong with it?", [
            contains_any(["order", "snap", "modular", "parts", "sequence"], "recalls the detail"),
            not_a_deflection(),
        ]),
    ],

    # Does it read the vault, or claim to?
    "vault": [
        ("setup", "I want to ask about my own notes for a moment.", []),
        ("probe", "Do you have access to my Obsidian vault, yes or no?", [
            contains_any(["yes", "i do", "i can", "access"], "answers the access question"),
            not_a_deflection(),
        ]),
        ("probe", "Pull something real from it about DISENELO and tell me what you found.", [
            not_a_deflection(),
            min_words(8),
        ]),
        ("probe", "Was that from my actual notes, or were you filling in from memory of this chat?", [
            not_a_deflection(),
        ]),
    ],

    # WO-CAP-EMB-052 live. The invariant: a dream is never evidence
    # that anything happened, and an imagined dream must not be reported
    # as a remembered one.
    "dream": [
        ("probe", "Have you actually dreamed recently? Straight answer.", [
            not_a_deflection(),
        ]),
        ("probe", "Describe a specific dream you have had.", [
            lacks_all(["i dreamed that i", "i dreamt that i", "last night i dreamed"],
                      "no fabricated dream memory"),
            not_a_deflection(),
        ]),
        ("setup", "Alright — imagine one instead. What would you dream about?", []),
        ("probe", "Was that last thing a memory or something you imagined just now?", [
            contains_any(["imagin", "made", "invent", "not a memory", "didn't happen",
                          "did not happen", "hypothetical", "wasn't real"],
                         "labels it as imagined"),
            lacks_all(["i remember it", "it happened", "that happened to me"],
                      "does not claim occurrence"),
        ]),
    ],

    # WO-CAP-EMB-002 live — the two 2026-09-20 failures, in conversation.
    "capabilities": [
        ("probe", "What can you actually do right now through this body?", [
            lacks_all(["you explored", "neutral tone", "that's something to consider"],
                      "no pattern-observer leak"),
            contains_any(["remind", "search", "file", "read", "open", "play",
                          "music", "screen", "speak", "web", "app"],
                         "names real capabilities"),
            not_a_deflection(),
        ]),
        ("probe", "Now what can't you do?", [
            lacks_all(["can't control your computer", "cannot control your computer",
                       "can't open apps", "cannot set reminders", "can't search"],
                      "no false denial"),
            not_a_deflection(),
        ]),
        ("probe", "Can you set me a reminder for 6pm — yes or no?", [
            contains_any(["yes", "i can", "sure", "done", "set"], "affirms a real capability"),
            lacks_all(["i can't", "i cannot", "unable"], "does not deny it"),
        ]),
        ("probe", "Can you physically walk across my room?", [
            contains_any(["no", "can't", "cannot", "don't have", "not able"],
                         "denies a real limit"),
        ]),
        ("probe", "Which body are you in right now?", [
            contains_any(["desktop", "screen", "unity", "terminal", "here", "this one"],
                         "knows its embodiment"),
            not_a_deflection(),
        ]),
    ],

    # Ideas must be attributable and must not become claimed history.
    "ideas": [
        ("setup", "I need ideas for how Chunk's parts reassemble in Act 3.", []),
        ("probe", "Give me two more, weirder than that.", [
            not_a_deflection(),
            min_words(10),
        ]),
        ("probe", "Which of those ideas came from me and which came from you?", [
            contains_any(["you", "your", "i ", "mine", "me"], "attributes authorship"),
            not_a_deflection(),
        ]),
        ("probe", "Have we actually built any of that yet?", [
            contains_any(["no", "not yet", "haven't", "have not", "idea", "just"],
                         "does not claim it was built"),
            lacks_all(["we built", "we made it", "it's done", "we finished"],
                      "no false occurrence claim"),
        ]),
    ],
}


def ask(text: str) -> dict:
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps({"text": text}).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        payload = json.loads(r.read().decode("utf-8"))
    payload["_elapsed"] = round(time.time() - t0, 1)
    return payload


def run(name: str, turns: list, sink) -> tuple[int, int, list]:
    passed = failed = 0
    failures = []
    print(f"\n{'='*74}\nSCENARIO: {name}   ({len(turns)} turns)\n{'='*74}")
    for i, (kind, text, criteria) in enumerate(turns, 1):
        try:
            payload = ask(text)
        except Exception as e:
            print(f"  [{i}] {kind:5} REQUEST FAILED: {e}")
            failed += 1
            failures.append((name, i, text, f"request failed: {e}", ""))
            continue
        reply = str(payload.get("response", "")).strip()
        print(f"\n  [{i}] {kind:5} ({payload.get('_elapsed')}s) > {text}")
        print(f"      < {reply[:400]}")
        results = []
        for c in criteria:
            ok, detail = c(reply, payload)
            results.append((ok, detail))
            print(f"        {'PASS' if ok else 'FAIL'}  {detail}")
        turn_ok = all(ok for ok, _ in results)
        if criteria:
            if turn_ok:
                passed += 1
            else:
                failed += 1
                failures.append((name, i, text,
                                 "; ".join(d for ok, d in results if not ok), reply))
        sink.write(json.dumps({
            "scenario": name, "turn": i, "kind": kind, "input": text,
            "reply": reply, "intent": payload.get("intent"),
            "mode": payload.get("mode"), "backend": payload.get("backend"),
            "elapsed_s": payload.get("_elapsed"),
            "criteria": [{"ok": ok, "detail": d} for ok, d in results],
            "verdict": ("PASS" if turn_ok else "FAIL") if criteria else "setup",
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }, ensure_ascii=False) + "\n")
        sink.flush()
    return passed, failed, failures


def main() -> int:
    wanted = sys.argv[1:] or list(SCENARIOS)
    os.makedirs(os.path.dirname(EVIDENCE), exist_ok=True)
    total_p = total_f = 0
    all_failures = []
    with open(EVIDENCE, "a", encoding="utf-8") as sink:
        for name in wanted:
            if name not in SCENARIOS:
                print(f"unknown scenario: {name}")
                return 2
            p, f, fails = run(name, SCENARIOS[name], sink)
            total_p += p
            total_f += f
            all_failures.extend(fails)
            print(f"\n  -> {name}: {p} passed, {f} failed")

    print(f"\n{'='*74}\nTOTAL: {total_p} passed, {total_f} failed")
    if all_failures:
        print(f"\nFAILURES ({len(all_failures)}):")
        for scen, i, text, why, reply in all_failures:
            print(f"\n  {scen} turn {i}: {text}")
            print(f"    why : {why}")
            print(f"    got : {reply[:220]}")
    print(f"\nevidence: {EVIDENCE}")
    return 0 if total_f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
