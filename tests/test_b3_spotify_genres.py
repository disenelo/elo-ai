"""B3 card 0013/0014: genre requests reach Spotify; non-music sentences never do. Offline (Spotify stubbed)."""
import pytest
import tools.spotify_play as sp


@pytest.mark.parametrize("q,g", [("put on jazz", "jazz"), ("play some reggae", "reggae"), ("play something chill", "chill"),
                                 ("can you put on some lo-fi please", "lo-fi"), ("play me a bit of house", "house"),
                                 ("stick on drum and bass", "drum and bass"), ("play jazz on spotify", "jazz")])
def test_genres(q, g):
    assert sp.genre_request(q) == g


@pytest.mark.parametrize("q", ["I put on a jacket", "play mode", "put on your thinking cap", "play the game",
                               "what's jazz?", "play some music", "pause the music"])
def test_not_genres(q):
    assert sp.genre_request(q) is None


def test_genre_plays_the_genre_not_resume(monkeypatch):
    played = []
    monkeypatch.setattr(sp, "play", lambda t: played.append(t) or f"Playing {t}.")
    monkeypatch.setattr(sp, "play_music", lambda: pytest.fail("generic resume must not run for a genre"))
    out = sp._handle_line("play something chill")
    assert out[0] == "play" and played == ["chill"] and out[2] == "Playing chill."
