"""
B3 — Spotify music demo (WO-B3-0013, END-OF-OCT demo milestone).

Locks down the three Track C bugs called out in START_HERE:

  1. Pause routing — natural phrasings must reach spotify_play.control("pause"),
     not fall through to the LLM.
  2. Capability denial while playing — "can you control Spotify?" must return
     an affirmative line from capability_answer(), not silence.
  3. "Got it" with no action — "play me some music" / "just play something" /
     "put on music" must match _PLAY_MUSIC_RE so handle() takes the turn,
     otherwise the LLM silent-acks ("Got it") without hitting Spotify.

Plus the demo-card acceptance phrasings: "play something chill",
"put on jazz", "play some reggae" must all be classified as a Spotify request
by at least one of the detection paths.

Offline. No network, no AppleScript. Pure classifier tests.
"""
import pytest

from tools import spotify_play as sp
from tools.spotify_agent import is_search_play_intent, is_playlist_intent


# ── BUG 1: pause routing ──────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _never_speak(monkeypatch):
    """Tests must never make eLo talk on David's Mac (pre_ack / voice_engine)."""
    import runtime.pre_ack as _pa, voice.voice_engine as _ve
    if not getattr(_pa.emit, "_b3_test_stub", False):
        monkeypatch.setattr(_pa, "emit", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "speak", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "speak_inner", lambda *a, **k: None)
    monkeypatch.setattr(_ve, "is_speaking", lambda: False)

PAUSE_YES = [
    "pause spotify",
    "pause the music",
    "stop the music",
    "turn the music off",
    "turn off the music",
    "shut off the music",
    "mute spotify",
    "kill the music",
    "can you pause spotify",
    "could you stop the music",
    "would you turn the music off",
    "stop playing that",
    "pause",
    "stop",
    "pause it",
    "stop it",
]


@pytest.mark.parametrize("t", PAUSE_YES)
def test_pause_phrasings_route_to_pause(t):
    assert sp.control_for(t) == "pause", f"{t!r} did not route to pause"


# ── BUG 2: capability denial while playing ────────────────────────────────────
ABILITY_YES = [
    "can you control spotify?",
    "could you control spotify",
    "are you able to control spotify",
    "you can control spotify",
    "you're able to control spotify",
    "do you know how to control spotify",
    "can you use spotify",
    "you can control spotify directly cause you are playing something right now",
]


@pytest.mark.parametrize("t", ABILITY_YES)
def test_ability_questions_get_affirmative_answer(t):
    line = sp.capability_answer(t)
    assert line, f"{t!r} returned no capability answer — eLo would deny"
    low = line.lower()
    assert any(w in low for w in ("yeah", "yep", "i can")), (
        f"{t!r} answer was not affirmative: {line!r}"
    )


def test_ability_answers_rotate_so_response_gate_does_not_blank():
    """elo_response_gate blanks identical consecutive replies — the ability
    answers rotate on purpose so a second "can you control spotify?" still
    reaches David."""
    a = sp.capability_answer("can you control spotify?")
    b = sp.capability_answer("can you control spotify?")
    assert a and b and a != b, (a, b)


# ── BUG 3: "Got it" with no action — generic play requests must fire ─────────
PLAY_MUSIC_YES = [
    "play music",
    "play something",
    "play anything",
    "put on music",
    "put on something",
    "play me some music",
    "play me something",
    "play me a tune",
    "just play something",
    "can you just play something",
    "please play music",
    "could you play me some music",
    "would you play some music",
]


@pytest.mark.parametrize("t", PLAY_MUSIC_YES)
def test_generic_play_music_fires_the_handler(t):
    """_PLAY_MUSIC_RE is what _handle_line checks first — a miss here means
    handle() returns None, the server passes to the LLM, and David hears
    "Got it" with nothing playing."""
    assert sp._PLAY_MUSIC_RE.match(t.strip()), (
        f"{t!r} missed _PLAY_MUSIC_RE — this is the silent-ack bug"
    )


PLAY_MUSIC_NO = [
    "play jazz",
    "play Fela Kuti",
    "play Nights by Frank Ocean",
    "what music is this",
    "pause the music",
    "I love music",
    "the music made me cry",
]


@pytest.mark.parametrize("t", PLAY_MUSIC_NO)
def test_named_or_mentions_do_not_match_generic_play(t):
    """Named plays route through parse()/is_search_play_intent; mentions must
    not fire the handler at all."""
    assert not sp._PLAY_MUSIC_RE.match(t.strip()), (
        f"{t!r} wrongly matched the generic-play regex"
    )


# ── Demo-card acceptance: "chill" / "jazz" / "reggae" must be a Spotify req ──
# Each row must be classified by at least one detection path so the server
# does something — not a silent LLM ack.
DEMO_ROWS = [
    "play something chill",
    "put on jazz",
    "play some reggae",
    "play some chill music",
    "play me something chill",
]


@pytest.mark.parametrize("t", DEMO_ROWS)
def test_demo_row_is_a_spotify_request(t):
    fired_generic = bool(sp._PLAY_MUSIC_RE.match(t.strip()))
    fired_search_play = is_search_play_intent(t)
    fired_playlist = is_playlist_intent(t)
    fired_parse = sp.parse(t) is not None
    assert fired_generic or fired_search_play or fired_playlist or fired_parse, (
        f"{t!r} would silent-ack — no Spotify classifier claimed it"
    )
