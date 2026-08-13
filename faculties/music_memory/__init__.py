"""faculties/music_memory — Music Memory Faculty for eLo OS."""
from faculties.music_memory.faculty import faculty
from faculties.music_memory.models import MusicMemory, MusicFact, MusicInterpretation, MusicObservation

__all__ = ["faculty", "MusicMemory", "MusicFact", "MusicInterpretation", "MusicObservation"]
