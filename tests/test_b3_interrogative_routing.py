"""
B3 — IS-ELO verdicts 2026-10-06: "can you X" must route like X for every B3
capability, and mentions must not. Offline (no network).
"""
import pytest

from tools.web_search import is_search_command
from tools import spotify_play as sp
from tools.brain_display import ui_command_for
from tools.research import factual_question

SEARCH_YES = ["can you google Pinky and the Brain", "could you search Pinky and the Brain",
              "would you mind googling that", "google Pinky and the Brain", "could you look into the Berlin Wall",
              "You'd have to do a websearch to read up about it", "look it up", "can you search the web for ramen"]
SEARCH_NO = ["I was googling earlier", "I googled it yesterday", "open google docs", "google is down",
             "could you search my notes for the robot plan", "I was looking up at the sky earlier",
             "what are you thinking about"]


@pytest.mark.parametrize("t", SEARCH_YES)
def test_search_routes(t):
    assert is_search_command(t)


@pytest.mark.parametrize("t", SEARCH_NO)
def test_search_does_not_route(t):
    assert not is_search_command(t)


@pytest.mark.parametrize("t,act", [("Can you pause Spotify", "pause"), ("could you pause the music", "pause"),
                                   ("would you turn the music off", "pause"), ("would you skip this song", "next"),
                                   ("Stop playing that", "pause"), ("resume the music", "resume")])
def test_spotify_controls_route(t, act):
    assert sp.control_for(t) == act


@pytest.mark.parametrize("t", ["I can't stop thinking about that song", "turn it off and on again",
                               "stop talking", "can you stop talking", "the song made me stop and think"])
def test_spotify_mentions_do_not_control(t):
    assert sp.control_for(t) is None


@pytest.mark.parametrize("t,name", [("could you show me your brain", "show_brain"),
                                    ("would you show me your health", "show_health"),
                                    ("can I see your brain", "show_brain"), ("show me your brain", "show_brain")])
def test_brain_routes(t, name):
    assert ui_command_for(t) == name


@pytest.mark.parametrize("t", ["can I see you later", "my brain hurts", "I love your energy", "what's on your mind"])
def test_brain_does_not_route(t):
    assert ui_command_for(t) is None


@pytest.mark.parametrize("t,kind", [("can you tell me what a capybara is", "define"),
                                    ("do you know what a Kalman filter is", "define"),
                                    ("could you tell me when the Berlin Wall fell", "fact"),
                                    ("can you tell me how tall the Eiffel Tower is", "fact"),
                                    ("who invented the telephone", "fact"), ("What is a Kalman filter?", "define")])
def test_research_questions(t, kind):
    q = factual_question(t)
    assert q and q[0] == kind


@pytest.mark.parametrize("t", ["can you tell me what you think", "do you know what I mean", "when you get a sec",
                               "could you tell me where my keys are", "what is the plan", "what is my dog's name",
                               "who is K-7", "what is eLo"])
def test_not_research(t):
    assert factual_question(t) is None
