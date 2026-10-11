"""
WO-B3-0012 — Web search + summaries demo (Board acceptance proof).

Card acceptance: 3 different natural language search requests. All must return
a spoken summary in eLo's voice, not raw results.

Covered here (offline, SerpAPI + Wikipedia mocked):
  AT-1  "look up the Berlin Wall"          → is_search_command + topic + sourced summary
  AT-2  "can you google Fela Kuti"         → interrogative form routes, named topic resolved
  AT-3  "read up about Pinky and the Brain" → named topic resolved, Wikipedia-led summary
  AT-4  "what's happening with the NBA"    → is_search_intent path, SearchResult context block
  AT-5  compose_found never emits raw URLs, bullet lists, or promo copy
  AT-6  lookup() returns the B3 standard shape {success, result, error}
"""
from __future__ import annotations

import os
import re
import sys
import unittest.mock as mock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import tools.web_search as _ws
from tools.web_search import (
    SearchResult,
    compose_found,
    format_for_context,
    is_search_command,
    is_search_intent,
    lookup,
    resolve_search_topic,
)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_web_search_state():
    """compose_found tracks what's already been said per topic; isolate tests."""
    _ws._said.clear()
    _ws._recent_inputs.clear()
    _ws.last_source = ""
    _ws.last_kg = {}
    _ws.last_spelling_fix = ""
    _ws.last_answer_box = {}
    _ws.last_picks = []
    _ws.last_wiki_description = ""
    yield
    _ws._said.clear()
    _ws._recent_inputs.clear()


def _mock_pipeline(topic_title: str, kg_desc: str, wiki_extract: str):
    """Patch SerpAPI + Wikipedia with a canonical result for one topic.
    _serp_search sets last_kg (title + description), returns one Wikipedia-hosted
    organic result. wiki_summary returns the lead paragraph."""
    def fake_serp(query, key, max_results, engine="google"):
        _ws.last_kg = {"title": topic_title, "description": kg_desc}
        _ws.last_spelling_fix = ""
        _ws.last_answer_box = {}
        return [SearchResult(
            title=f"{topic_title} - Wikipedia",
            url=f"https://en.wikipedia.org/wiki/{topic_title.replace(' ', '_')}",
            snippet=wiki_extract,
        )]

    def fake_wiki(name):
        return SearchResult(
            title=topic_title,
            url=f"https://en.wikipedia.org/wiki/{topic_title.replace(' ', '_')}",
            snippet=wiki_extract,
        )

    return (
        mock.patch.dict(os.environ, {"SERPAPI_KEY": "test"}),
        mock.patch.object(_ws, "_serp_search", side_effect=fake_serp),
        mock.patch.object(_ws, "wiki_summary", side_effect=fake_wiki),
    )


def _run_lookup(utterance: str, topic_title: str, kg_desc: str, wiki_extract: str):
    """Full pipeline from utterance to spoken line, with mocked network."""
    assert is_search_command(utterance), f"{utterance!r} did not route via is_search_command"
    resolved = resolve_search_topic(utterance)
    assert resolved, f"{utterance!r} resolved to empty topic"
    env_patch, serp_patch, wiki_patch = _mock_pipeline(topic_title, kg_desc, wiki_extract)
    with env_patch, serp_patch, wiki_patch:
        return lookup(resolved)


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_look_up_berlin_wall_returns_sourced_summary():
    r = _run_lookup(
        "look up the Berlin Wall",
        topic_title="Berlin Wall",
        kg_desc="A guarded concrete barrier that divided Berlin from 1961 to 1989.",
        wiki_extract=(
            "The Berlin Wall was a guarded concrete barrier that physically and "
            "ideologically divided Berlin from 13 August 1961 until 9 November 1989. "
            "The wall separated East Berlin from West Berlin."
        ),
    )
    line = r["result"]["line"]
    assert r["success"] is True, f"AT-1 FAIL: lookup unsuccessful ({r.get('error')!r})"
    assert "Berlin Wall" in line, f"AT-1 FAIL: topic missing from line — {line!r}"
    assert line.startswith(("Looked it up on ", "More on ")), (
        f"AT-1 FAIL: eLo's own lead-in missing — {line!r}"
    )
    assert "Wikipedia" in line, f"AT-1 FAIL: source not named — {line!r}"


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_google_fela_kuti_interrogative_routes_and_summarises():
    assert resolve_search_topic("can you google Fela Kuti") == "Fela Kuti"
    r = _run_lookup(
        "can you google Fela Kuti",
        topic_title="Fela Kuti",
        kg_desc="Nigerian multi-instrumentalist and pioneer of Afrobeat.",
        wiki_extract=(
            "Fela Anikulapo Kuti was a Nigerian musician and political activist who "
            "pioneered the Afrobeat genre in the late 1960s. He is widely regarded as "
            "one of Africa's most influential musicians of the twentieth century."
        ),
    )
    line = r["result"]["line"]
    assert r["success"] is True
    assert "Fela" in line, f"AT-2 FAIL: topic missing — {line!r}"
    assert "•" not in line and "-" not in line.split(" — ", 1)[-1][:3], (
        f"AT-2 FAIL: bullet-list markers in the spoken line — {line!r}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_read_up_about_pinky_and_the_brain():
    assert resolve_search_topic("read up about Pinky and the Brain") == "Pinky and the Brain"
    r = _run_lookup(
        "read up about Pinky and the Brain",
        topic_title="Pinky and the Brain",
        kg_desc="American animated television series created by Tom Ruegger.",
        wiki_extract=(
            "Pinky and the Brain is an American animated television series created by "
            "Tom Ruegger, which premiered on Kids' WB on September 9, 1995. It was the "
            "first animated television series to be presented in Dolby Surround."
        ),
    )
    line = r["result"]["line"]
    assert r["success"] is True
    assert "Pinky and the Brain" in line, f"AT-3 FAIL: topic missing — {line!r}"
    assert "https://" not in line and "http://" not in line, (
        f"AT-3 FAIL: raw URL leaked into spoken line — {line!r}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_whats_happening_with_nba_routes_via_search_intent():
    """server.py uses is_search_intent for broader triggers like 'what's happening with X'.
    The context block the LLM gets must contain real result snippets, not a URL list."""
    utterance = "what's happening with the NBA"
    assert is_search_intent(utterance), (
        f"AT-4 FAIL: {utterance!r} not matched by is_search_intent — the broader "
        "trigger list in web_search.py must cover 'what's happening'"
    )
    sample = [
        SearchResult(
            title="NBA 2026 Season Opens",
            url="https://nba.example/news/opening",
            snippet="The 2026 NBA season tipped off on Tuesday with the Celtics defeating the Knicks 112-104.",
        ),
        SearchResult(
            title="Top plays of the week",
            url="https://nba.example/news/top-plays",
            snippet="Highlights included a buzzer-beater from Luka Doncic and a 50-point night from Jayson Tatum.",
        ),
    ]
    ctx = format_for_context(sample)
    assert ctx.startswith("[WEB_SEARCH_RESULTS]"), f"AT-4 FAIL: context header missing — {ctx!r}"
    assert "2026 NBA season tipped off" in ctx
    assert "buzzer-beater" in ctx


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_compose_found_rejects_promo_and_first_person_copy():
    """A spoken summary must be encyclopedic text, not marketing calls-to-action
    or someone's first-person opinion from a forum."""
    results = [
        SearchResult(
            title="Jitwam Radio",
            url="https://en.wikipedia.org/wiki/Jitwam",
            snippet=(
                "Jitwam Singh is an Australian-born producer and multi-instrumentalist "
                "known for blending house, soul, and hip-hop. His Jitwam Radio playlist "
                "collects his favourite tracks across those genres."
            ),
        ),
        SearchResult(
            title="Click here to subscribe",
            url="https://promo.example.com/signup",
            snippet="Subscribe now for exclusive content. Sign up today and get 20% off your first month.",
        ),
        SearchResult(
            title="My thoughts",
            url="https://quora.com/some-post",
            snippet="I've been listening to Jitwam for years and I think his music is incredible.",
        ),
    ]
    _ws.last_kg = {"title": "Jitwam", "description": ""}
    line = compose_found("Jitwam", results)
    assert line, "AT-5 FAIL: compose_found returned empty with usable Wikipedia source"
    assert "Click here" not in line and "Subscribe" not in line, (
        f"AT-5 FAIL: promo copy leaked — {line!r}"
    )
    assert "I've been listening" not in line and "I think" not in line, (
        f"AT-5 FAIL: first-person forum opinion leaked — {line!r}"
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_lookup_returns_b3_standard_shape():
    """lookup() is the entry point server.py calls for the explicit-search path.
    Its return shape is the {success, result, error} contract every B3 tool
    produces — the capability_status gate reads this."""
    env_patch, serp_patch, wiki_patch = _mock_pipeline(
        "Kalman filter",
        "Algorithm for recursive estimation of a system's state from noisy measurements.",
        "The Kalman filter is an algorithm that uses a series of measurements observed over "
        "time, including statistical noise and other inaccuracies, and produces estimates of "
        "unknown variables.",
    )
    with env_patch, serp_patch, wiki_patch:
        r = lookup("Kalman filter")
    assert set(r.keys()) == {"success", "result", "error"}, (
        f"AT-6 FAIL: lookup shape not B3 standard — {sorted(r.keys())}"
    )
    assert set(r["result"].keys()) >= {"name", "line", "sources", "provider", "results"}
    assert r["result"]["provider"] in ("serpapi", "ddg")
    assert isinstance(r["result"]["sources"], list)
    assert isinstance(r["result"]["line"], str) and r["result"]["line"].strip()
