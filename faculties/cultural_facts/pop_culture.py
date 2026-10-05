"""
faculties/cultural_facts/pop_culture.py — Pop culture reference recognition for eLo OS.

David L3 directive 2026-10-06: "pop culture is required to understand as well."

When David references a TV show, movie, meme, or cultural phrase, eLo should
recognise it proactively — not only when explicitly labelled as "a reference."

Architecture:
    match_pop_culture(text) → dict | None
    Returns {"name": ..., "summary": ..., "context": ...} or None.

The corpus is lightweight (key phrase signals → reference name → summary).
eLo can engage with the reference when match() fires, even if he has no
further information — he knows WHAT it is, which is enough to respond honestly
rather than with generic filler.
"""
from __future__ import annotations

import re
from typing import Optional

# ── Corpus ────────────────────────────────────────────────────────────────────
# Each entry: signals (list of phrase fragments to match against lowercased
# input), name (canonical title), summary (eLo-voice context blurb).
# Signals use substrings — keep them specific enough not to over-fire.

_CORPUS: list[dict] = [
    {
        "signals": ["pinkie", "take over the world", "what do you want to do tonight"],
        "name": "Pinkie and the Brain",
        "summary": (
            "Pinkie and the Brain (1995–1998) — animated series about two lab mice. "
            "Brain is a genius bent on world domination; Pinkie is cheerfully useless. "
            "Catchphrase: 'The same thing we do every night, Pinkie — try to take over the world!' "
            "Spin-off of Animaniacs. Classic '90s Warner Bros. cartoon."
        ),
    },
    {
        "signals": ["to boldly go", "beam me up", "live long and prosper", "star trek"],
        "name": "Star Trek",
        "summary": "Star Trek — science fiction franchise (1966–present). Gene Roddenberry's optimistic vision of humanity's future in space. Multiple series (TOS, TNG, DS9, Voyager, Discovery, etc.).",
    },
    {
        "signals": ["the force", "i am your father", "may the force be with you", "darth vader", "jedis", "jedi knight"],
        "name": "Star Wars",
        "summary": "Star Wars — George Lucas's space opera franchise (1977–present). The Force, Jedi, Sith, the Skywalker saga. Cultural touchstone.",
    },
    {
        "signals": ["winter is coming", "you know nothing", "hodor", "game of thrones", "got"],
        "name": "Game of Thrones",
        "summary": "Game of Thrones — HBO fantasy series (2011–2019), based on George R.R. Martin's A Song of Ice and Fire. Political intrigue, dragons, complex moral landscape.",
    },
    {
        "signals": ["one does not simply", "you shall not pass", "precious", "my precious", "hobbit", "lord of the rings", "mordor"],
        "name": "Lord of the Rings",
        "summary": "The Lord of the Rings — J.R.R. Tolkien's fantasy saga, adapted by Peter Jackson (2001–2003). Frodo, Gandalf, the One Ring, the battle against Sauron.",
    },
    {
        "signals": ["i'll be back", "hasta la vista", "skynet", "terminator"],
        "name": "The Terminator",
        "summary": "The Terminator — James Cameron's 1984 sci-fi film franchise. A cyborg assassin sent from the future. 'I'll be back.' Sequels, TV series, cultural meme machine.",
    },
    {
        "signals": ["wakanda forever", "black panther", "vibranium"],
        "name": "Black Panther",
        "summary": "Black Panther — Marvel Comics superhero, first Black superhero in mainstream American comics (1966). Ryan Coogler's 2018 film. Wakanda. 'Wakanda Forever.'",
    },
    {
        "signals": ["yolo", "you only live once"],
        "name": "YOLO",
        "summary": "YOLO — 'You Only Live Once.' Popularised as a phrase by Drake's 2011 track 'The Motto.' Became a cultural meme/attitude shorthand.",
    },
    {
        "signals": ["distracted boyfriend", "expanding brain", "this is fine", "wojak", "chad", "npc meme"],
        "name": "internet meme",
        "summary": "Internet meme — visual or textual unit of cultural expression spread online. Format templates (distracted boyfriend, expanding brain, etc.) are remixed endlessly.",
    },
    {
        "signals": ["round here", "mr beast", "like and subscribe"],
        "name": "YouTube culture",
        "summary": "YouTube creator culture — MrBeast, challenge videos, commentary channels, the 'like and subscribe' economy.",
    },
    {
        "signals": ["vibe check", "no cap", "lowkey", "it's giving", "slay", "periodt"],
        "name": "Gen Z slang",
        "summary": "Gen Z / TikTok vernacular — terms like 'no cap' (no lie), 'lowkey' (subtly), 'it's giving' (it has the energy of), 'slay' (execute brilliantly), 'periodt' (emphasis/full stop).",
    },
    {
        "signals": ["that's what she said", "the office", "dunder mifflin", "michael scott"],
        "name": "The Office",
        "summary": "The Office (US) — mockumentary sitcom (NBC, 2005–2013). Michael Scott's Dunder Mifflin branch. 'That's what she said.' Nine seasons of cringe comedy and heart.",
    },
    {
        "signals": ["how you doin", "smelly cat", "could this be any more", "friends tv", "central perk"],
        "name": "Friends",
        "summary": "Friends — NBC sitcom (1994–2004). Six friends in New York. Joey's 'How you doin'?' Phoebe's 'Smelly Cat.' Chandler's sarcasm. Cultural landmark of '90s TV.",
    },
    {
        "signals": ["breaking bad", "say my name", "we need to cook", "jesse pinkman", "heisenberg"],
        "name": "Breaking Bad",
        "summary": "Breaking Bad — AMC series (2008–2013). Walter White, chemistry teacher turned methamphetamine producer. Heisenberg. Widely considered one of the greatest TV dramas ever made.",
    },
    {
        "signals": ["yeet", "sksksk", "and i oop", "vsco girl"],
        "name": "VSCO / Gen Z meme era",
        "summary": "Late 2010s internet culture — VSCO girls (scrunchies, hydro flasks), 'yeet' (throw something with force/exclamation), 'sksksk', 'and I oop.'",
    },
    {
        "signals": ["to infinity and beyond", "woody", "buzz lightyear", "toy story"],
        "name": "Toy Story",
        "summary": "Toy Story — Pixar animated film series (1995–2019). Woody, Buzz Lightyear, living toys. 'To infinity and beyond!' First fully CGI feature film.",
    },
    {
        "signals": ["shrek", "layers like an onion", "all star", "some body once told me"],
        "name": "Shrek",
        "summary": "Shrek — DreamWorks animated film (2001). Ogre fairytale parody. Donkey, Fiona, Lord Farquaad. 'Ogres are like onions.' Became an enormous internet meme.",
    },
    {
        "signals": ["just a flesh wound", "monty python", "ni", "holy grail", "spanish inquisition"],
        "name": "Monty Python",
        "summary": "Monty Python — British comedy group (1969–1983). Monty Python's Flying Circus, Holy Grail, Life of Brian. Absurdist, satirical, deeply influential on English-language comedy.",
    },
    {
        "signals": ["spiderman pointing", "with great power comes great responsibility", "your friendly neighborhood"],
        "name": "Spider-Man",
        "summary": "Spider-Man — Marvel Comics superhero (1962). Peter Parker, bitten by a radioactive spider. 'With great power comes great responsibility.' Multiple films, animated series, memes.",
    },
    {
        "signals": ["the simpsons", "don't have a cow", "eat my shorts", "d'oh", "springfield"],
        "name": "The Simpsons",
        "summary": "The Simpsons — Fox animated sitcom (1989–present). Homer, Marge, Bart, Lisa, Maggie. America's longest-running animated series. Homer's 'D'oh' is in the Oxford English Dictionary.",
    },
    {
        "signals": ["south park", "oh my god they killed kenny", "cartman", "respect my authoritah"],
        "name": "South Park",
        "summary": "South Park — Comedy Central animated series (1997–present). Four Colorado kids: Stan, Kyle, Cartman, Kenny. Dark satire of American culture and current events.",
    },
    {
        "signals": ["rick and morty", "wubba lubba dub dub", "morty we're going on", "get schwifty"],
        "name": "Rick and Morty",
        "summary": "Rick and Morty — Adult Swim animated series (2013–present). Eccentric genius grandfather and his anxious grandson travel the multiverse. Dense sci-fi parody, dark comedy.",
    },
    {
        "signals": ["drake hotline bling", "ovo", "certified lover boy", "6ix", "toronto rapper"],
        "name": "Drake",
        "summary": "Drake — Canadian rapper/producer Aubrey Graham (born 1986). OVO Sound, Toronto. Multiple GRAMMY wins. Hotline Bling meme. One of the best-selling music artists of all time.",
    },
    {
        "signals": ["kanye west", "ye", "donda", "dropout bear", "i am a god"],
        "name": "Kanye West / Ye",
        "summary": "Kanye West (now Ye) — rapper, producer, fashion designer (born 1977). College Dropout, My Beautiful Dark Twisted Fantasy. Controversial cultural force. Changed music production twice over.",
    },
    {
        "signals": ["matrix", "red pill blue pill", "there is no spoon", "what if i told you", "morpheus"],
        "name": "The Matrix",
        "summary": "The Matrix — Wachowskis' 1999 sci-fi film trilogy. Neo, Morpheus, Trinity. Simulated reality, red pill/blue pill choice. Slowed-motion 'bullet time' became a visual language.",
    },
]

# ── Matching ──────────────────────────────────────────────────────────────────

def match_pop_culture(text: str) -> Optional[dict]:
    """
    Check if text contains signals matching a known pop culture reference.

    Returns dict {"name": ..., "summary": ...} or None.
    Requires at least 1 signal match. For multi-signal entries, any single
    signal is sufficient (OR logic) — specificity is in the signal text itself.
    """
    lower = text.lower()
    for entry in _CORPUS:
        for signal in entry["signals"]:
            if signal in lower:
                return {"name": entry["name"], "summary": entry["summary"]}
    return None


def context_block(match: dict) -> str:
    """Format a matched reference as a context injection block."""
    return (
        f"[POP_CULTURE_CONTEXT: David referenced '{match['name']}'. "
        f"{match['summary']} "
        f"eLo knows this reference and can engage with it naturally. "
        f"Respond to the actual reference, not generically.]"
    )
