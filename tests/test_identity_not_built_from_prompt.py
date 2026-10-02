"""
eLo's sense of himself must be built from what David said, not from his own prompt.

`raw` in server.py is a MUTABLE variable that accumulates prompt injections.
It is overwritten at six sites -- WORLD_KNOWLEDGE, WEB_SEARCH, TODO_VAULT,
SCREEN_CONTENT, APP_LIST, PROJECT_LINKS -- each prepending a block for the
model. Every consumer after those sites reads whichever block fired.

Found live in self/elo_self_state.json, 2026-09-29. eLo's lifetime_threads,
the thing behind "what do you keep coming back to?":

    ['world', 1009]   ['[world_knowledge', 982]
    ["elo's", 982]    ['(verified', 982]
    ['about', 103]    ['stuck', 38]      ['building', 21]

The top four are fragments of his own prompt syntax, counted ~1000 times.
The real threads sat 50:1 underneath. Those same threads seed his dreams
(dream_faculty.py:517), so it reached those too.

_original_raw (server.py:2240) is captured before any enrichment. The F-5
remediation established it on 2026-08-21 for state_manager; the consumers
below were left on `raw` and are fixed now.
"""
from __future__ import annotations

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SERVER = os.path.join(_ROOT, "server.py")


def _src() -> str:
    return open(_SERVER, encoding="utf-8").read()


def _line_of(needle: str) -> int:
    return _src()[: _src().index(needle)].count("\n") + 1


def test_original_raw_is_captured_before_every_injection():
    """
    Whatever the injection sites are, the clean capture must precede all of
    them, or _original_raw is contaminated too.
    """
    s = _src()
    capture = s.index("_original_raw = raw")
    injections = [m.start() for m in re.finditer(r'\n\s+raw = f"\[', s)]
    assert injections, "no injection sites found — has the pipeline changed?"
    assert all(capture < i for i in injections), (
        "_original_raw is captured after an injection site"
    )


def test_lifetime_threads_are_built_from_the_clean_input():
    """
    The thread accumulator tokenises the user's words. On `raw` it tokenises
    the prompt instead.
    """
    s = _src()
    i = s.index("_so_topics = list(dict.fromkeys(")
    block = s[i - 900:i]
    assert "(_original_raw or raw or \"\").split()" in block, (
        "lifetime threads are still tokenised from the enriched `raw`"
    )


def test_turn_data_user_input_is_the_clean_input():
    s = _src()
    i = s.index('"user_input":')
    assert "_original_raw" in s[i:i + 60], (
        "apply_turn receives the enriched text as user_input"
    )


def test_episodic_memory_uses_the_clean_input():
    """The sibling fix — both must hold together."""
    s = _src()
    assert "_mem_said        = _original_raw or raw" in s
    assert "_write_interaction(_mem_said" in s


def test_state_manager_still_uses_the_clean_input():
    """The August F-5 fix must not regress while fixing its siblings."""
    assert "_state, _original_raw, response," in _src()


def test_the_injection_sites_still_exist():
    """
    The fix must not have removed the enrichment. The model still needs
    WORLD_KNOWLEDGE and the rest; only eLo's self-knowledge changed source.
    """
    s = _src()
    for block in ("[WORLD_KNOWLEDGE", "[WEB_SEARCH:", "[SCREEN_CONTENT]",
                  "[APP_LIST]", "[PROJECT_LINKS]", "[TODO_VAULT]"):
        assert block in s, f"{block} enrichment was removed, not re-sourced"


def test_live_state_contamination_is_visible_not_hidden():
    """
    Documents the damage already in the store. This is not a pass/fail on the
    fix -- it records that historical threads are polluted, so a later cleanup
    has a reference point. It asserts only that the file is readable.
    """
    import json
    path = os.path.join(_ROOT, "self", "elo_self_state.json")
    if not os.path.isfile(path):
        return
    threads = json.load(open(path, encoding="utf-8")).get("lifetime_threads", [])
    polluted = [t for t in threads
                if isinstance(t, (list, tuple)) and t
                and str(t[0]).startswith(("[", "("))]
    if polluted:
        print(f"\nNOTE: {len(polluted)} lifetime threads are prompt fragments "
              f"from before the fix: {[t[0] for t in polluted]}")


# ── injection sites must echo the clean input, never the enriched one ────────

def test_every_injection_echoes_the_original_not_the_enriched_raw():
    """
    Each enrichment block ends "User asked: {...}". Thirteen used
    _original_raw; six used `raw`, which by then may already BE another
    block. Two firing on one turn nested:

        [WEB_SEARCH: chunk]
        results...

        User asked: [WORLD_KNOWLEDGE]
        Chunk: modular companion.

        User asked: what do you know about Chunk

    The model is handed a question wrapped inside a question, and every
    downstream consumer of `raw` inherits the whole stack.
    """
    s = _src()
    stray = re.findall(r"User asked: \{raw\}", s)
    assert not stray, (
        f"{len(stray)} injection site(s) echo the enriched `raw` instead of "
        "_original_raw — enrichments will nest"
    )


def test_all_injection_sites_accounted_for():
    """If a new enrichment is added, it must use the clean input too."""
    s = _src()
    tails = re.findall(r"User asked: \{([_a-z]+)\}", s)
    assert tails, "no injection tails found — has the pipeline changed shape?"
    assert set(tails) == {"_original_raw"}, f"unexpected tail sources: {set(tails)}"
