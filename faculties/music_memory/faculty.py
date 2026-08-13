"""
faculties/music_memory/faculty.py — Music Memory Faculty interface.

Architecture position:
    Faculties → CognitiveState → Executive → CognitivePlan → Embodiment

The Music Memory Faculty:
    - Observes the music library and produces MusicObservation
    - Never decides what to do with an observation
    - Never controls Spotify or SoundCloud
    - Never assumes meaning without evidence

The Executive receives the observation and decides:
    - Does this become conversation?
    - Does this become a journal entry?
    - Does this become a creative suggestion?
    - Is it ignored this turn?

Entry points:
    observe(trigger)        — produce a MusicObservation for the Executive
    ingest(source)          — import from a platform export or manual entry
    annotate(title, artist) — add meaning to an existing track
    status()                — quick stats (for debug/memory-status reports)
"""
from __future__ import annotations

from faculties.music_memory.models import MusicMemory, MusicObservation


class MusicMemoryFaculty:
    """
    The Music Memory Faculty.

    Instantiate once and keep alive for the session.
    All state lives in the library.json file — no in-memory session state.
    """

    # ── Observation ───────────────────────────────────────────────────────────

    def observe(self, trigger: str = "") -> MusicObservation:
        """
        Produce a MusicObservation for the Executive.

        Args:
            trigger — what prompted this observation (user message, session start, etc.)

        Returns:
            MusicObservation — facts + patterns + plain-language summary.
            has_signal = True only if something is worth surfacing this turn.
        """
        from faculties.music_memory import storage, patterns, journal

        all_memories = list(storage.load_all().values())

        significant = storage.load_by_significance(min_sig=0.45)
        recent_disc = [
            MusicMemory.from_dict(e) for e in
            _entries_to_memories(journal.recent_discoveries(5))
        ]

        pattern_text = patterns.pattern_summary(all_memories) if all_memories else ""
        obs_text     = journal.observation_text(significant)

        combined = (pattern_text + " " + obs_text).strip()

        has_signal = bool(significant or recent_disc)

        return MusicObservation(
            trigger             = trigger,
            patterns            = [pattern_text] if pattern_text else [],
            significant_tracks  = significant[:10],
            recent_discoveries  = recent_disc,
            observation_text    = combined,
            has_signal          = has_signal,
        )

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, source: "str | dict | list", context: str = "") -> list[MusicMemory]:
        """
        Import music data from a platform export or manual entry.

        Args:
            source  — file path (str), manual dict, or list of dicts
            context — optional description of how/when discovered

        Returns:
            List of new or updated MusicMemory objects.
        """
        from faculties.music_memory.importer import ingest as _ingest
        return _ingest(source, context)

    # ── Annotation ────────────────────────────────────────────────────────────

    def annotate(
        self,
        title:   str,
        artist:  str,
        *,
        emotion:           str            = "",
        notes:             str            = "",
        creative_projects: list[str]      = None,
        life_period:       str | None     = None,
        mood_tags:         list[str]      = None,
        memories:          list[str]      = None,
        log_inspiration:   str            = "",   # project name → logs to inspiration journal
    ) -> MusicMemory | None:
        """
        Add or update interpretation for a track.

        Looks up the track by artist+title, applies annotation, rescores,
        resaves. Returns updated MusicMemory or None if track not found.
        """
        from faculties.music_memory import storage, analyser, journal
        from dataclasses import replace

        lib = storage.load_all()
        from faculties.music_memory.models import MusicFact
        key = MusicFact(title=title, artist=artist).key()

        if key not in lib:
            return None

        mem   = lib[key]
        interp= mem.interpretation
        interp_dict = {
            "emotion":           emotion           or interp.emotion,
            "notes":             notes             or interp.notes,
            "creative_projects": (creative_projects or []) + interp.creative_projects,
            "life_period":       life_period       or interp.life_period,
            "mood_tags":         (mood_tags        or []) + interp.mood_tags,
            "memories":          (memories         or []) + interp.memories,
            "importance":        interp.importance,
        }

        from faculties.music_memory.models import MusicInterpretation
        new_interp = MusicInterpretation(**{
            k: list(set(v)) if isinstance(v, list) else v
            for k, v in interp_dict.items()
        })

        mem = replace(mem, interpretation=new_interp)
        mem = analyser.score_and_update(mem)
        storage.save(mem)
        storage.save_to_vault(mem)

        if log_inspiration:
            journal.log_inspiration(mem.fact, log_inspiration, notes)

        return mem

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> str:
        """Plain-language status for debug/memory-status reports."""
        from faculties.music_memory import storage
        stats = storage.library_stats()
        return (
            f"Music memory: {stats['total']} tracks, "
            f"{stats['significant']} significant, "
            f"{stats['artists']} artists."
        )

    # ── Conversation listener ─────────────────────────────────────────────────

    def detect_music_mention(self, text: str) -> MusicMemory | None:
        """
        Detect a music mention in a conversation message.
        Returns a candidate MusicMemory if found, None otherwise.
        Caller is responsible for asking David to confirm before storing.
        """
        from faculties.music_memory.importers.manual import from_conversation
        return from_conversation(text)


def _entries_to_memories(entries: list[dict]) -> list[dict]:
    """Convert journal entry dicts to MusicMemory-compatible dicts (best-effort)."""
    result = []
    for e in entries:
        result.append({
            "title":  e.get("title",  ""),
            "artist": e.get("artist", ""),
            "sources": [e.get("source", "")],
            "discovered": {"date": e.get("discovered_date"), "context": e.get("context", "")},
            "memory": {},
        })
    return result


# ── Module-level singleton ────────────────────────────────────────────────────
# Import and use this directly — no need to instantiate per call.

faculty = MusicMemoryFaculty()
