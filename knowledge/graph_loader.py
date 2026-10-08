"""
knowledge/graph_loader.py — eLo OS Connection Engine.

WO-CANON-XXIV (Ruling A): one canonical graph (relationships/world_graph.json).
Retrieval contract: results carry confidence + kind + evidence[] + score.
Ranked by score DESC. Unknown facts return empty list — never backfilled from LLM.

Reads world_graph.json, concepts.json, and viewpoints.json.
Before each response, finds:
  1. Entities mentioned in user input (ranked by keyword match count)
  2. Relationships between those entities
  3. Relevant viewpoint
  4. Relevant concept

Returns a compact context string for injection into the system prompt.
"""

from __future__ import annotations
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_GRAPH_PATH      = os.path.join(_ROOT, "relationships", "world_graph.json")
_CONCEPTS_PATH   = os.path.join(_ROOT, "relationships", "concepts.json")
_VIEWPOINTS_PATH = os.path.join(_ROOT, "knowledge",     "viewpoints.json")
# WO-102 (Vol XXIV §1.3.5-7): Person / Place / Event stores. Empty by default —
# David populates them; nothing is seeded. Card 0021 P0-Y: loading them is a
# prerequisite for eLo to know his own world instead of the internet.
_PEOPLE_PATH     = os.path.join(_ROOT, "relationships", "people.json")
_PLACES_PATH     = os.path.join(_ROOT, "relationships", "places.json")
_EVENTS_PATH     = os.path.join(_ROOT, "relationships", "events.json")

# WO-102: closed set of entity types. Free-form was how two ontologies drifted apart.
_ALLOWED_ENTITY_TYPES = frozenset({
    "project", "brand", "character", "companion", "state", "mechanic",
    "world_stage", "system", "person", "place", "event",
})

# Module-level cache — loaded once per process
_graph:      dict = {}
_concepts:   dict = {}
_viewpoints: dict = {}

# WKG Phase 1 — sections within _graph (Amendment C: no separate store/loader)
# Populated by _load_all() from world_graph.json.  retrieve_wkg() reads these directly from _graph.
_WKG_CLAIMS_KEY:          str = "wkg_claims"
_WKG_SOURCES_KEY:         str = "wkg_sources"
_WKG_PROPOSED_CLAIMS_KEY: str = "wkg_proposed_claims"
# WKG Phase 2 — additional sections
_WKG_ENTITIES_KEY:        str = "wkg_entities"
_WKG_CLAIM_RELS_KEY:      str = "wkg_claim_relationships"


def _load_json(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _person_to_entity(p: dict) -> dict:
    """Project a Vol XXIV Person into the entity shape retrieve() expects."""
    facts = p.get("facts") or []
    descr = "; ".join(str(f.get("fact", "")).strip() for f in facts if f.get("fact")) or ""
    relation = str(p.get("relation") or "").strip()
    note     = str(p.get("relation_note") or "").strip()
    header   = f"{p.get('name', p.get('id', ''))} — {relation}".strip(" —")
    body     = " — ".join(bit for bit in (note, descr) if bit)
    aliases  = [str(a) for a in (p.get("also_known_as") or []) if a]
    keywords = list(p.get("keywords") or [])
    for tok in [str(p.get("name") or ""), *aliases]:
        if tok:
            keywords.append(tok.lower())
    return {
        "id":          p.get("id", ""),
        "name":        p.get("name", p.get("id", "")),
        "type":        "person",
        "description": (header + (": " + body if body else "")).strip(": "),
        "keywords":    [k for k in (kw.lower() for kw in keywords) if k],
        "confidence":  1.0,
        "sensitivity": p.get("sensitivity", "normal"),
    }


def _place_to_entity(pl: dict) -> dict:
    keywords = list(pl.get("keywords") or [])
    for tok in [str(pl.get("name") or ""), str(pl.get("locality") or "")]:
        if tok:
            keywords.append(tok.lower())
    sig = pl.get("significance") or ""
    return {
        "id":          pl.get("id", ""),
        "name":        pl.get("name", pl.get("id", "")),
        "type":        "place",
        "description": f"{pl.get('kind', 'place')} — {sig}" if sig else pl.get("kind", "place"),
        "keywords":    [k for k in (kw.lower() for kw in keywords) if k],
        "confidence":  1.0,
        "sensitivity": pl.get("sensitivity", "normal"),
    }


def _event_to_entity(ev: dict) -> dict:
    keywords = list(ev.get("keywords") or [])
    what = str(ev.get("what") or "").strip()
    outcome = str(ev.get("outcome") or "").strip()
    when = ev.get("when") or {}
    when_str = str(when.get("date") or "").strip()
    header = f"event: {what}" if what else "event"
    body = " — ".join(bit for bit in (when_str, outcome) if bit)
    return {
        "id":          ev.get("id", ""),
        "name":        ev.get("id", "event"),
        "type":        "event",
        "description": (header + (" — " + body if body else "")).strip(),
        "keywords":    [k for k in (kw.lower() for kw in keywords) if k],
        "confidence":  1.0,
        "sensitivity": ev.get("sensitivity", "normal"),
    }


def _load_all():
    global _graph, _concepts, _viewpoints
    if _graph:
        return
    _graph      = _load_json(_GRAPH_PATH)      or {"entities": [], "relationships": []}
    _concepts   = _load_json(_CONCEPTS_PATH)
    _viewpoints = _load_json(_VIEWPOINTS_PATH)

    # WO-102: merge people / places / events into the single entity table (Ruling A —
    # one canonical graph). Type validation: unknown types are dropped with a warning.
    import logging as _lg
    _log = _lg.getLogger(__name__)
    for src, projector in (
        (_load_json(_PEOPLE_PATH).get("people", []), _person_to_entity),
        (_load_json(_PLACES_PATH).get("places", []), _place_to_entity),
        (_load_json(_EVENTS_PATH).get("events", []), _event_to_entity),
    ):
        for item in src:
            try:
                ent = projector(item)
                if ent["type"] not in _ALLOWED_ENTITY_TYPES:
                    _log.warning("WO-102: dropped entity id=%r with out-of-set type=%r",
                                 ent.get("id"), ent.get("type"))
                    continue
                # sensitivity=private hides the entry from open retrieval (Vol XXIII).
                if ent.get("sensitivity") == "private":
                    continue
                _graph.setdefault("entities", []).append(ent)
            except Exception as _e:
                _log.warning("WO-102: entity projection failed: %s", _e)

    # Ruling A: identity/world_graph.json is retired. If it exists, log — do not load.
    _legacy = os.path.join(_ROOT, "identity", "world_graph.json")
    if os.path.exists(_legacy):
        _log.warning("Ruling A: legacy identity/world_graph.json present but IGNORED — canonical graph is relationships/")

    # WKG (Amendment C): WKG sections are part of the same world_graph.json.
    # No separate file or loader. _graph holds wkg_claims / wkg_sources /
    # wkg_proposed_claims / wkg_entities / wkg_claim_relationships alongside
    # the existing eLo-universe entities + relationships.
    _wkg_count = (
        len(_graph.get(_WKG_CLAIMS_KEY, [])) +
        len(_graph.get(_WKG_SOURCES_KEY, [])) +
        len(_graph.get(_WKG_PROPOSED_CLAIMS_KEY, [])) +
        len(_graph.get(_WKG_ENTITIES_KEY, [])) +
        len(_graph.get(_WKG_CLAIM_RELS_KEY, []))
    )
    if _wkg_count:
        _log.info("WKG: loaded %d WKG nodes from world_graph.json", _wkg_count)


# ── entity matching ────────────────────────────────────────────────────────────

def _kw_match(keyword: str, text_lower: str) -> bool:
    """True if keyword appears as a whole word in text (not as a substring of another word).
    B3-BOARD-RULINGS Issue 3 2026-10-06: bare 'k in t' matched 'ai' inside 'brain'/'again'/'said'.
    """
    return bool(re.search(r"\b" + re.escape(keyword) + r"\b", text_lower))


def _find_entities(text: str) -> list[dict]:
    """Return entities whose keywords appear in the lowercased input, with match count."""
    _load_all()
    t = text.lower()
    matched = []
    for e in _graph.get("entities", []):
        score = sum(1 for k in e.get("keywords", []) if _kw_match(k, t))
        if score > 0:
            matched.append((score, e))
    matched.sort(key=lambda x: x[0], reverse=True)
    return [e for _, e in matched]


def _find_relationships(entity_ids: list[str]) -> list[dict]:
    """Return relationships where both ends are in the matched entity set."""
    _load_all()
    id_set = set(entity_ids)
    return [
        r for r in _graph.get("relationships", [])
        if r.get("from") in id_set or r.get("to") in id_set
    ]


# ── concept matching ───────────────────────────────────────────────────────────

def _find_concept(text: str) -> dict | None:
    """Return the most relevant concept for this input."""
    _load_all()
    t = text.lower()
    for concept in _concepts.get("concepts", []):
        keys = concept.get("related", []) + [concept.get("id", ""), concept.get("name", "").lower()]
        if any(_kw_match(k, t) for k in keys if k):
            return concept
    return None


# ── viewpoint matching ─────────────────────────────────────────────────────────

def _find_viewpoint(text: str) -> dict | None:
    """Return the most relevant viewpoint for this input."""
    _load_all()
    t = text.lower()
    for vp in _viewpoints.get("viewpoints", []):
        if any(_kw_match(k, t) for k in vp.get("keywords", []) if k):
            return vp
    return None


# ── ranked structured retrieval ────────────────────────────────────────────────

def retrieve(user_input: str, top_k: int = 3) -> list[dict]:
    """
    Return up to top_k ranked knowledge items for user_input.

    Each result dict carries:
      label:      display label (entity name or relationship pair)
      content:    description / connection text
      confidence: epistemic confidence 0.0–1.0 (graph field or default 1.0)
      kind:       entity type or "relationship"
      evidence:   list of source strings (graph field or [])
      score:      keyword match count (salience rank)

    Returns [] when no graph knowledge matches — never backfills from LLM.
    """
    _load_all()
    if not _graph:
        return []

    text     = user_input.strip().lower()
    entities = _find_entities(text)
    results: list[dict] = []

    # WO-CANON-XXIV §D: statuses that are excluded from retrieval (behaviourally real)
    _EXCLUDED_STATUSES = frozenset({"contested", "retracted"})

    # entity hits — skip contested/retracted nodes
    for e in entities:
        if e.get("status") in _EXCLUDED_STATUSES:
            continue
        kw_score = sum(1 for k in e.get("keywords", []) if _kw_match(k, text.lower()))
        # §D: epistemic_kind is distinct from ontology type.
        # Authored entities use their ontology type (person/place/event/fact) when no
        # explicit epistemic_kind is present; promoted nodes carry their own kind.
        entity_type    = e.get("type", "entity")
        epistemic_kind = e.get("epistemic_kind") or e.get("status") or entity_type
        results.append({
            "label":      e.get("name", e.get("id", "")),
            "content":    e.get("description", ""),
            "confidence": float(e.get("confidence", 1.0)),
            "kind":       epistemic_kind,
            "type":       entity_type,
            "evidence":   list(e.get("evidence", [])),
            "score":      kw_score,
        })

    # relationship hits (from/to entity in matched set)
    if entities:
        entity_ids = {e["id"] for e in entities}
        for r in _graph.get("relationships", []):
            if r.get("from") in entity_ids or r.get("to") in entity_ids:
                from_name = next((e["name"] for e in _graph["entities"] if e["id"] == r["from"]), r["from"])
                to_name   = next((e["name"] for e in _graph["entities"] if e["id"] == r["to"]),   r["to"])
                results.append({
                    "label":      f"{from_name} → {to_name}",
                    "content":    r.get("connection", r.get("meaning", "")),
                    "confidence": float(r.get("confidence", 1.0)),
                    "kind":       "relationship",
                    "type":       "relationship",
                    "evidence":   list(r.get("evidence", [])),
                    "score":      float(r.get("strength", 0.5)),
                })

    # rank: entity match count DESC, then confidence DESC
    results.sort(key=lambda x: (x["score"], x["confidence"]), reverse=True)
    return results[:top_k]


# ── context assembly ──────────────────────────────────────────────────────────

def build_context(user_input: str, max_chars: int = 800) -> str:
    """
    Build a compact context string from the knowledge graph.

    Returns up to max_chars of relevant:
      - Entity descriptions and relationships
      - A relevant viewpoint
      - A relevant concept connection

    Returns empty string if nothing relevant found.
    """
    _load_all()
    if not _graph and not _viewpoints:
        return ""

    text      = user_input.strip()
    entities  = _find_entities(text)
    rels      = _find_relationships([e["id"] for e in entities]) if entities else []
    viewpoint = _find_viewpoint(text)
    concept   = _find_concept(text)

    lines: list[str] = []

    # entity context
    if entities:
        for e in entities[:2]:   # max 2 entities
            lines.append(f"{e['name']}: {e['description']}")

    # relationship context — most relevant connection
    if rels:
        r = rels[0]
        # find both entity names
        from_name = next((e["name"] for e in _graph.get("entities", []) if e["id"] == r["from"]), r["from"])
        to_name   = next((e["name"] for e in _graph.get("entities", []) if e["id"] == r["to"]),   r["to"])
        lines.append(f"Connection ({from_name} → {to_name}): {r['connection']}")

    # viewpoint
    if viewpoint:
        lines.append(f"Perspective: {viewpoint['viewpoint']}")

    # concept (only if no viewpoint or there's room)
    if concept and not viewpoint:
        lines.append(f"Concept note: {concept['emotional_significance']}")

    if not lines:
        return ""

    context = "\n".join(lines)
    return context[:max_chars]


# ── WO-CANON-XXIV §D: write-path validation + referential integrity ───────────

_EPISTEMIC_KINDS = frozenset({"fact", "perspective", "inference", "promoted_memory"})


def validate_graph_write(entry: dict) -> None:
    """
    §D: Validate an entity dict before writing to the knowledge graph.
    Raises ValueError on violations.

    Rules:
    - epistemic_kind must be one of {fact, perspective, inference, promoted_memory}
    - fact and promoted_memory MUST have non-empty evidence[]
    - perspective MUST carry epistemic_kind="perspective" (always tagged)
    - strength is salience only — never treated as confidence (read-path guard)
    """
    kind = entry.get("epistemic_kind") or entry.get("kind")
    if kind and kind not in _EPISTEMIC_KINDS and kind not in ("contested", "retracted"):
        raise ValueError(f"Unknown epistemic_kind {kind!r}; must be one of {_EPISTEMIC_KINDS}")

    if kind in ("fact", "promoted_memory"):
        evidence = entry.get("evidence") or []
        if not evidence:
            raise ValueError(
                f"epistemic_kind={kind!r} requires non-empty evidence[]; "
                "no orphan facts allowed (Vol XXIV §2.4)"
            )


def check_referential_integrity(graph: dict) -> list[str]:
    """
    §D: Check that every relationship from/to resolves to an existing entity id.
    Returns list of problem strings (empty = clean).
    """
    entity_ids = {e.get("id") for e in graph.get("entities", []) if e.get("id")}
    problems: list[str] = []
    for r in graph.get("relationships", []):
        frm = r.get("from")
        to  = r.get("to")
        if frm and frm not in entity_ids:
            problems.append(f"relationship {r.get('id','?')!r}: dangling from={frm!r}")
        if to and to not in entity_ids:
            problems.append(f"relationship {r.get('id','?')!r}: dangling to={to!r}")
    return problems


# ── WKG Phase 1: retrieve_wkg() ───────────────────────────────────────────────

def retrieve_wkg(user_input: str, top_k: int = 3) -> list[dict]:
    """
    WKG Phase 1 (Amendment C): retrieve WKG claims from the canonical graph.

    Results carry the same envelope as retrieve(), plus wkg_epistemic_class.
    Amendment A dual-classification: Vol XXIV kind + confidence are computed at
    the retrieval boundary from wkg_epistemic_class — not stored in the graph.

    Returns [] when no WKG data matches (Phase 1: corpus is empty).
    Never backfills from LLM (same guarantee as retrieve()).

    Phase 7 will extend this into a structured KnowledgeQuery interface.
    """
    from knowledge.wkg_schema import map_to_vol_xxiv
    _load_all()
    claims = list(_graph.get(_WKG_CLAIMS_KEY, []))

    # Also pull runtime claims from memory/wkg/claims.json (interaction-derived).
    # These use entity IDs; look up labels for keyword matching.
    try:
        import json as _json
        import os as _os
        _wkg_dir = _os.path.join(_os.path.dirname(__file__), "..", "memory", "wkg")
        _rt_claims_path  = _os.path.join(_wkg_dir, "claims.json")
        _rt_entities_path = _os.path.join(_wkg_dir, "entities.json")
        if _os.path.exists(_rt_claims_path) and _os.path.exists(_rt_entities_path):
            with open(_rt_claims_path, encoding="utf-8") as _f:
                _rt_claims = _json.load(_f)
            with open(_rt_entities_path, encoding="utf-8") as _f:
                _rt_entities = {e["entity_id"]: e for e in _json.load(_f)}
            for _c in _rt_claims:
                _subj = _rt_entities.get(_c.get("subject_entity_id", ""), {})
                _obj  = _rt_entities.get(_c.get("object_entity_id",  ""), {})
                claims.append({
                    "id":                 _c.get("claim_id", ""),
                    "subject":            _subj.get("label", _c.get("subject_entity_id", "")),
                    "predicate":          _c.get("relationship_type", ""),
                    "object":             _obj.get("label",  _c.get("object_entity_id",  "")),
                    "wkg_epistemic_class": _c.get("epistemic_class", "UNKNOWN"),
                    "confidence":          _c.get("confidence"),
                    "evidence":           [],
                    "interpretation":     f"{_subj.get('label','')} {_c.get('relationship_type','')} {_obj.get('label','')}",
                    "notes":              _subj.get("description", "") + " " + _obj.get("description", ""),
                    "source":             "runtime-wkg",
                })
    except Exception:
        pass

    if not claims:
        return []

    text = user_input.strip().lower()
    results: list[dict] = []

    # GRAPH-LOADER-P0: stopwords that score on every claim (fired on "Pinkie and the Brain").
    # Only content words (≥4 chars, not stopwords) count toward WKG match score.
    _WKG_STOPWORDS = frozenset({
        "what", "that", "this", "with", "from", "have", "been", "will", "would",
        "could", "should", "does", "were", "they", "them", "their", "then",
        "than", "when", "where", "which", "while", "also", "about", "into",
        "over", "more", "some", "your", "just", "very", "much",
        "and", "the", "for", "are", "but", "not", "you", "all", "can",
        "her", "was", "one", "our", "out", "how", "its", "him", "his",
        "she", "had", "has", "may", "let",
        "it", "is", "in", "a", "an", "at", "be", "by", "do", "go",
        "if", "me", "my", "no", "of", "on", "or", "so", "to", "up", "us", "we",
    })

    def _wkg_word_scores(word: str, searchable: str) -> bool:
        """Content-word whole-boundary match: word must be ≥4 chars, not a stopword,
        and appear as a whole word in the searchable claim text."""
        if len(word) < 4 or word in _WKG_STOPWORDS:
            return False
        return bool(re.search(r"\b" + re.escape(word) + r"\b", searchable))

    for claim in claims:
        searchable = " ".join(str(v) for v in [
            claim.get("subject",        ""),
            claim.get("object",         ""),
            claim.get("predicate",      ""),
            claim.get("notes",          "") or "",
            claim.get("interpretation", "") or "",
        ]).lower()

        score = sum(1 for word in text.split() if _wkg_word_scores(word, searchable))
        if score == 0:
            continue

        cls       = claim.get("wkg_epistemic_class", "UNKNOWN")
        vol_xxiv  = map_to_vol_xxiv(cls)
        # claim-level confidence overrides schema default when explicitly set
        confidence = claim.get("confidence")
        if confidence is None:
            confidence = vol_xxiv["confidence"]

        # COG-011: for runtime-wkg claims, include entity descriptions in content
        # so the full constraint text reaches the model, not just the bare relation.
        _base_content = (
            claim.get("interpretation")
            or f"{claim.get('subject')} {claim.get('predicate')} {claim.get('object')}"
        )
        _notes = (claim.get("notes") or "").strip()
        _content = (
            f"{_base_content}\n{_notes}" if _notes and claim.get("source") == "runtime-wkg"
            else _base_content
        )
        results.append({
            "label":               claim.get("id", ""),
            "content":             _content,
            "confidence":          float(confidence) if confidence is not None else 0.5,
            "kind":                vol_xxiv["kind"],
            "evidence":            list(claim.get("evidence") or []),
            "score":               score,
            "wkg_epistemic_class": cls,
            "provisional":         vol_xxiv.get("provisional", False),
            "source":              claim.get("source", ""),
        })

    results.sort(key=lambda x: (x["score"], x["confidence"]), reverse=True)
    return results[:top_k]


# ── WKG-001: retrieve_wkg_context_items() — structured ContextItem wrapper ────

def retrieve_wkg_context_items(user_input: str, top_k: int = 5) -> list:
    """
    WKG-001: retrieve WKG claims as ContextItem objects (structured provenance).

    Maps wkg_epistemic_class → EpistemicClass / AuthorityLevel / PersistenceClass.
    Returns [] when no matching claims (same zero-backfill guarantee as retrieve_wkg).
    """
    from memory.provenance import (
        ContextItem, EpistemicClass, AuthorityLevel, PersistenceClass,
    )

    _MAP = {
        "VERIFIED":         (EpistemicClass.CANONICAL,       AuthorityLevel.VERIFIED,      PersistenceClass.IMMUTABLE),
        "HISTORICAL":       (EpistemicClass.CANONICAL,       AuthorityLevel.VERIFIED,      PersistenceClass.IMMUTABLE),
        "SPECULATIVE":      (EpistemicClass.INFERRED,        AuthorityLevel.ADVISORY,      PersistenceClass.PERSISTENT),
        "HYPOTHESIS":       (EpistemicClass.INFERRED,        AuthorityLevel.ADVISORY,      PersistenceClass.PERSISTENT),
        "DISPUTED":         (EpistemicClass.INFERRED,        AuthorityLevel.NON_CANONICAL, PersistenceClass.PERSISTENT),
        "SOURCE_ATTRIBUTED":(EpistemicClass.RETRIEVED_LORE,  AuthorityLevel.NON_CANONICAL, PersistenceClass.PERSISTENT),
        "SYMBOLIC":         (EpistemicClass.RETRIEVED_LORE,  AuthorityLevel.NON_CANONICAL, PersistenceClass.PERSISTENT),
    }
    _UNKNOWN = (EpistemicClass.UNKNOWN, AuthorityLevel.UNKNOWN, PersistenceClass.PERSISTENT)

    _load_all()
    if not _graph.get(_WKG_CLAIMS_KEY):
        return []

    raw_claims = retrieve_wkg(user_input, top_k=top_k)
    if not raw_claims:
        return []

    items: list[ContextItem] = []
    for claim in raw_claims:
        cls = claim.get("wkg_epistemic_class", "UNKNOWN")
        ep_class, authority, persistence = _MAP.get(cls, _UNKNOWN)

        # Build content: interpretation + evidence if present
        content = claim.get("content", "")
        evidence = claim.get("evidence", [])
        if evidence:
            content = f"{content}\nEvidence: {'; '.join(str(e) for e in evidence)}"

        items.append(ContextItem(
            content=content,
            source="WKG",
            provenance=f"WKG:{cls}",
            timestamp=None,
            session_id=None,
            epistemic_class=ep_class,
            persistence_class=persistence,
            authority=authority,
        ))

    return items


# ── WKG Phase 2: claim relationship accessor ──────────────────────────────────

def get_wkg_claim_relationships(rel_type: str | None = None) -> list[dict]:
    """
    Return WKG claim-to-claim relationships from wkg_claim_relationships[].

    Pass rel_type to filter by relationship type (e.g. "CONTRADICTS").
    Returns all relationships when rel_type is None.
    """
    _load_all()
    rels = _graph.get(_WKG_CLAIM_RELS_KEY, [])
    if rel_type is not None:
        return [r for r in rels if r.get("type") == rel_type]
    return list(rels)
