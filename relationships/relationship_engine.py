"""
relationships/relationship_engine.py — meaning layer for eLo OS.

Input:  conversation string
Output: {observations, relationships, viewpoints}

Injection limit: max 1 observation + 1 connection + 1 viewpoint per response.

Not therapy. Not advice. Not analysis.
Observations only — patterns noticed, connections found, perspectives offered.

Examples:
    "Your projects seem to meet around the same idea."
    "That sounds like uncertainty looking for form."
    "Meaning usually arrives after movement."
"""
from __future__ import annotations

from relationships.world_graph    import WorldGraph
from relationships.concept_graph  import ConceptGraph
from relationships.viewpoint_graph import ViewpointGraph

# project entity ids — used to detect multi-project mentions
_PROJECT_IDS = {"book", "game", "os", "robot", "disenelo"}

# observation templates for entity pairs
_PAIR_OBSERVATIONS = {
    frozenset({"game",  "os"}):     "The game and the OS seem to meet around the same core idea.",
    frozenset({"game",  "book"}):   "The game and the book are expressions of the same question.",
    frozenset({"os",    "robot"}):  "The OS is the mind for the robot — they complete each other.",
    frozenset({"book",  "robot"}):  "The book gives the robot its personality before it has a body.",
    frozenset({"game",  "robot"}):  "The game's movement language is the robot's body language.",
    frozenset({"os",    "book"}):   "The OS and the book are the same question — what does it mean to stay present?",
    frozenset({"elo",   "sugarcore"}): "eLo moves through Sugarcore by understanding it, not by fighting it.",
    frozenset({"elo",   "k7"}):     "K-7 offers eLo the perspective it can't reach alone.",
    frozenset({"elo",   "chunk"}):  "Chunk shows that broken things don't restore — they transform.",
    frozenset({"k7",    "chunk"}):  "K-7 and Chunk each complete something eLo alone cannot close.",
}

# multi-project observation (3+ projects mentioned)
_MULTI_PROJECT_OBS = "Your projects seem to meet around the same idea — different forms, one question."


class RelationshipEngine:
    def __init__(self):
        self._world    = WorldGraph.get()
        self._concepts = ConceptGraph.get()
        self._views    = ViewpointGraph.get()

    def analyse(self, text: str) -> dict:
        """
        Analyse conversation text for meaning.

        Returns:
            {
                "observations":  list[str],   — max 1, pattern noticed
                "relationships": list[str],   — max 1, explicit connection
                "viewpoints":    list[str],   — max 1, perspective
            }
        """
        entities  = self._world.find(text, max_results=3)
        entity_ids = [e.id for e in entities]
        concept   = self._concepts.find(text)
        viewpoint = self._views.find(text)

        observation  = self._observation(entity_ids, text)
        relationship = self._relationship(entities, entity_ids)
        perspective  = viewpoint.perspective if (viewpoint and viewpoint.perspective) else None

        return {
            "observations":  [observation]  if observation  else [],
            "relationships": [relationship] if relationship else [],
            "viewpoints":    [perspective]  if perspective  else [],
        }

    def inject(self, text: str) -> str:
        """
        Return a compact context string — at most 1+1+1 lines.
        Empty string if nothing relevant found.
        """
        result = self.analyse(text)
        lines  = []

        if result["observations"]:
            lines.append(f"Pattern: {result['observations'][0]}")
        if result["relationships"]:
            lines.append(f"Connection: {result['relationships'][0]}")
        if result["viewpoints"]:
            lines.append(f"Perspective: {result['viewpoints'][0]}")

        return "\n".join(lines)

    # ── private ───────────────────────────────────────────────────────────────

    def _observation(self, entity_ids: list, text: str) -> str | None:
        # multi-project mention — most distinctive observation
        project_ids = set(entity_ids) & _PROJECT_IDS
        if len(project_ids) >= 3:
            return _MULTI_PROJECT_OBS

        # two-entity pattern
        if len(project_ids) == 2:
            key = frozenset(project_ids)
            if key in _PAIR_OBSERVATIONS:
                return _PAIR_OBSERVATIONS[key]

        # all entity pair check (including non-project)
        if len(entity_ids) >= 2:
            for i in range(len(entity_ids)):
                for j in range(i + 1, len(entity_ids)):
                    key = frozenset({entity_ids[i], entity_ids[j]})
                    if key in _PAIR_OBSERVATIONS:
                        return _PAIR_OBSERVATIONS[key]

        return None

    def _relationship(self, entities: list, entity_ids: list) -> str | None:
        if len(entities) < 2:
            return None
        pairs = self._world.connections_between(entity_ids)
        if not pairs:
            return None
        a, b = pairs[0]
        return f"{_display(a.id)} and {_display(b.id)} are connected."


def _display(eid: str) -> str:
    _NAMES = {"os": "OS", "k7": "K-7", "cyber_garden": "Cyber Garden",
              "elo": "eLo", "disenelo": "DISENELO"}
    return _NAMES.get(eid, eid.replace("_", " ").title())


# module-level singleton
_engine: RelationshipEngine | None = None


def get_engine() -> RelationshipEngine:
    global _engine
    if _engine is None:
        _engine = RelationshipEngine()
    return _engine


def inject(text: str) -> str:
    """Convenience function — returns context string for prompt injection."""
    return get_engine().inject(text)


def analyse(text: str) -> dict:
    """Convenience function — returns structured analysis dict."""
    return get_engine().analyse(text)
