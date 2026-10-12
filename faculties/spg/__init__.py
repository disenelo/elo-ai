"""
faculties/spg — Builder 2's SPG lane.

START_HERE names `faculties/spg/` as Builder 2's, and until now it did not
exist; the SPG work lived in `memory/` beside files other seats own.
Everything new goes here.
"""
from faculties.spg.content_index import (
    content_for, record_content, sync_from_interactions,
)

__all__ = ["content_for", "record_content", "sync_from_interactions"]
