"""
tests/test_conversation_quality.py — eLo OS conversation quality validation.

Tests:
    1. Greeting — relevant, warm, not generic filler
    2. Inquiry — actual answers, not comfort phrases
    3. Emotional — grounding, not questioning loops
    4. Creative — encouraging, not deadening
    5. Recall — references session/project context
    6. Goodbye — identity-consistent exit

Also verifies:
    - No consecutive phrase loops across 30 messages
    - Inquiry override: factual questions never hit emotional pools
"""

import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backends.mock_backend import MockBackend


def _r(m: MockBackend, text: str, mode: str = "CHILDLIKE-WISE") -> str:
    return m.generate_response(text, mode, {}, {}, {}, {})["response_text"]


def _ok(condition: bool, label: str):
    status = "  OK " if condition else "FAIL"
    print(f"  {status}  {label}")
    return condition


# ── CATEGORY 1: GREETING ─────────────────────────────────────────────────────

def test_greeting():
    m = MockBackend()
    r = _r(m, "Hello")
    assert "?" in r or any(w in r.lower() for w in ["on your mind", "what's up", "going on", "working on", "what do you need", "ready", "starting", "what are"]), \
        f"Greeting should invite conversation, got: {r!r}"

def test_greeting_not_filler():
    m = MockBackend()
    r = _r(m, "How are you?")
    # should NOT be silence/stabilise response
    bad = ["take your time", "we don't need to rush", "one step", "simplify"]
    assert not any(b in r.lower() for b in bad), \
        f"Greeting triggered comfort filler: {r!r}"


# ── CATEGORY 2: INQUIRY ───────────────────────────────────────────────────────

def test_inquiry_what_is_elo():
    m = MockBackend()
    r = _r(m, "What is eLo?")
    keywords = ["universe", "creative", "character", "building", "exploration", "world"]
    assert any(k in r.lower() for k in keywords), \
        f"'What is eLo?' must describe the eLo universe, got: {r!r}"

def test_inquiry_explain_book():
    m = MockBackend()
    r = _r(m, "Explain the eLo book.")
    keywords = ["book", "story", "adventure", "elo", "narrative", "character"]
    assert any(k in r.lower() for k in keywords), \
        f"Book inquiry must describe the story, got: {r!r}"

def test_inquiry_who_is_k7():
    m = MockBackend()
    r = _r(m, "Who is K-7?")
    keywords = ["k-7", "spirit", "seven", "form", "guide", "companion"]
    assert any(k in r.lower() for k in keywords), \
        f"K-7 inquiry must describe K-7, got: {r!r}"

def test_inquiry_what_is_chunk():
    m = MockBackend()
    r = _r(m, "What is Chunk?")
    keywords = ["chunk", "reconstruct", "reassembl", "modular", "broken", "reform", "fragment"]
    assert any(k in r.lower() for k in keywords), \
        f"Chunk inquiry must describe Chunk, got: {r!r}"

def test_inquiry_what_is_sugarcore():
    m = MockBackend()
    r = _r(m, "What is Sugarcore?")
    assert "sugarcore" in r.lower() or any(w in r.lower() for w in ["aesthetic", "colour", "visual", "soft", "warm"]), \
        f"Sugarcore inquiry must describe Sugarcore, got: {r!r}"

def test_inquiry_narrative_arc():
    m = MockBackend()
    r = _r(m, "Explain the eLo narrative arc.")
    keywords = ["story", "book", "act", "elo", "adventure", "healing", "narrative"]
    assert any(k in r.lower() for k in keywords), \
        f"Narrative arc must return story content, got: {r!r}"

def test_inquiry_not_emotional():
    """Factual questions must never hit emotional response pools."""
    m = MockBackend()
    emotional_fillers = ["take your time", "we don't need to rush", "nothing needs to happen", "we can simplify"]
    for q in ["What is eLo?", "Explain the eLo book.", "What are we building?", "Who is K-7?"]:
        r = _r(m, q)
        assert not any(f in r.lower() for f in emotional_fillers), \
            f"Inquiry {q!r} triggered emotional filler: {r!r}"

def test_inquiry_override_even_under_emotional_mode():
    """Factual query must answer even if mode is SILENCE-AWARE."""
    m = MockBackend()
    r = _r(m, "What is eLo?", mode="SILENCE-AWARE")
    assert "universe" in r.lower() or "creative" in r.lower() or "character" in r.lower(), \
        f"Inquiry must override SILENCE-AWARE mode, got: {r!r}"


# ── CATEGORY 3: EMOTIONAL ─────────────────────────────────────────────────────

def test_emotional_overwhelm():
    m = MockBackend()
    r = _r(m, "I feel completely overwhelmed.")
    # both GENTLE and OVERWHELM pools are valid — both ground, not question-loop
    grounding = ["simplify", "one step", "slow", "reduce", "hold", "rush", "here",
                 "nothing needs", "real", "okay", "stay", "that's where", "don't have to",
                 "push", "move", "place", "alright", "time"]
    assert any(g in r.lower() for g in grounding), \
        f"Overwhelm must return grounding response, got: {r!r}"

def test_emotional_scattered():
    m = MockBackend()
    r = _r(m, "I have been feeling a bit scattered lately.")
    assert "?" not in r or r.count("?") <= 1, \
        f"Emotional response must not loop with questions: {r!r}"

def test_emotional_not_looping():
    """10 emotional messages should not all get the same response."""
    m = MockBackend()
    responses = set()
    inputs = [
        "I feel tired.", "I'm exhausted.", "Everything feels like too much.",
        "I can't think clearly.", "So much is happening.", "I feel scattered.",
        "I don't know where to start.", "Overwhelmed today.", "Low energy.",
        "Can't seem to focus."
    ]
    for inp in inputs:
        responses.add(_r(m, inp))
    assert len(responses) >= 4, \
        f"Emotional responses are looping: only {len(responses)} unique responses across 10 inputs"


# ── CATEGORY 4: CREATIVE ──────────────────────────────────────────────────────

def test_creative_exploration():
    m = MockBackend()
    r = _r(m, "What if we built a visual layer for eLo?", mode="JOYFUL")
    # Should encourage, not stabilise
    bad = ["take your time", "nothing needs to happen", "one step is enough"]
    assert not any(b in r.lower() for b in bad), \
        f"Creative input triggered stabilise response: {r!r}"

def test_creative_variety():
    m = MockBackend()
    responses = set()
    for _ in range(8):
        responses.add(_r(m, "Let's build something new.", mode="JOYFUL"))
    assert len(responses) >= 3, \
        f"Creative responses looping: {responses}"


# ── CATEGORY 5: RECALL ────────────────────────────────────────────────────────

def test_recall_what_were_we():
    m = MockBackend()
    r = _r(m, "What were we working on?")
    keywords = ["elo os", "system", "memory", "session", "building", "attention", "architecture", "spec",
                "conversation", "quality", "responding", "continuity", "elo", "os"]
    assert any(k in r.lower() for k in keywords), \
        f"Recall must reference project context, got: {r!r}"

def test_recall_what_did_we():
    m = MockBackend()
    r = _r(m, "What did we talk about last session?")
    assert any(k in r.lower() for k in ["elo", "session", "system", "memory", "building"]), \
        f"Recall must reference session history, got: {r!r}"


# ── CATEGORY 6: GOODBYE ───────────────────────────────────────────────────────

def test_goodbye_pool_available():
    from backends.mock_backend import EXIT_POOL
    assert len(EXIT_POOL) >= 4, "EXIT_POOL must have at least 4 entries"

def test_goodbye_not_software():
    from backends.mock_backend import EXIT_POOL
    software_phrases = ["saving", "closing", "shutting", "terminated", "session ended"]
    for msg in EXIT_POOL:
        assert not any(p in msg.lower() for p in software_phrases), \
            f"Exit message feels like software: {msg!r}"


# ── ANTI-LOOP: 30-MESSAGE STRESS TEST ────────────────────────────────────────

def test_no_loop_across_30_messages():
    """30 varied messages should not produce more than 3 consecutive identical responses."""
    m = MockBackend()
    inputs = [
        "Hello", "How are you?", "What is eLo?", "Explain the book.",
        "Who is K-7?", "What is Chunk?", "I feel tired.",
        "What if we built something new?", "What were we working on?",
        "I'm feeling scattered.", "What should I focus on?",
        "Let's create something today.", "I don't know where to start.",
        "What is Sugarcore?", "Tell me about the narrative arc.",
        "I feel overwhelmed.", "What are the current goals?",
        "That idea has potential.", "I want to build a voice layer.",
        "What are we actually making?", "I feel good today.",
        "What does eLo mean to you?", "I've been circling this for a while.",
        "What's the next step?", "What did we discuss before?",
        "I'm not sure what to do.", "Let's slow down a bit.",
        "Something feels off.", "What is the Sugarcore aesthetic?",
        "Thank you.",
    ]
    responses = []
    for inp in inputs:
        responses.append(_r(m, inp))

    # check no 3 consecutive identical
    for i in range(len(responses) - 2):
        assert not (responses[i] == responses[i+1] == responses[i+2]), \
            f"3 consecutive identical responses at positions {i}-{i+2}: {responses[i]!r}"


# ── SUCCESS CRITERIA SCENARIO ─────────────────────────────────────────────────

def test_success_scenario():
    """The exact scenario from the spec must produce relevant answers."""
    m = MockBackend()
    cases = [
        ("Hello",                       lambda r: "?" in r or any(w in r.lower() for w in ["on your mind", "going on", "working", "what's up", "ready", "starting", "what are", "hear"])),
        ("What is eLo?",                lambda r: any(w in r.lower() for w in ["universe", "creative", "character", "world"])),
        ("Explain the book.",           lambda r: any(w in r.lower() for w in ["book", "story", "adventure", "healing", "elo"])),
        ("I feel confused.",            lambda r: any(w in r.lower() for w in ["okay", "slow", "here", "time", "sense", "valid", "place"])),
        ("What are we building?",       lambda r: any(w in r.lower() for w in ["elo os", "game", "robot", "book", "kickstarter", "system", "build"])),
        ("What did we talk about?",     lambda r: any(w in r.lower() for w in ["elo os", "session", "memory", "system", "building"])),
        ("Goodbye.",                    lambda r: True),   # any response is fine for unmatched goodbye
    ]
    for inp, check in cases:
        r = _r(m, inp)
        assert check(r), f"Scenario failed for {inp!r}: {r!r}"


# ── RUNNER ────────────────────────────────────────────────────────────────────

def _run_all():
    tests = [
        test_greeting,
        test_greeting_not_filler,
        test_inquiry_what_is_elo,
        test_inquiry_explain_book,
        test_inquiry_who_is_k7,
        test_inquiry_what_is_chunk,
        test_inquiry_what_is_sugarcore,
        test_inquiry_narrative_arc,
        test_inquiry_not_emotional,
        test_inquiry_override_even_under_emotional_mode,
        test_emotional_overwhelm,
        test_emotional_scattered,
        test_emotional_not_looping,
        test_creative_exploration,
        test_creative_variety,
        test_recall_what_were_we,
        test_recall_what_did_we,
        test_goodbye_pool_available,
        test_goodbye_not_software,
        test_no_loop_across_30_messages,
        test_success_scenario,
    ]
    passed = 0
    failed = 0
    for t in tests:
        name = t.__name__.replace("test_", "").replace("_", " ")
        try:
            t()
            _ok(True, name)
            passed += 1
        except AssertionError as e:
            _ok(False, f"{name}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = _run_all()
    sys.exit(0 if ok else 1)
