"""
elo_personality_engine/injection_layer.py — Personality Injection Layer.

Converts static personality documents into a deterministic, versioned
RuntimePersonalityProfile that any backend can use without modification.

Inputs:
    elo_personality_engine/sources/identity.md
    elo_personality_engine/sources/values.md
    personality_skeleton.md (project root)
    active project IDs (list of strings)

Output:
    RuntimePersonalityProfile — frozen dataclass, LLM-independent

Determinism: same inputs → same profile_id → same to_prompt_block() output.
Versioning:  profile_id changes whenever any source file changes.
Caching:     compiled profiles stored in memory/profile_cache/.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime

_ENGINE_DIR        = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR          = os.path.dirname(_ENGINE_DIR)
_SOURCES_DIR       = os.path.join(_ENGINE_DIR, "sources")
_CACHE_DIR         = os.path.join(_ROOT_DIR, "memory", "profile_cache")
_SKELETON          = os.path.join(_ROOT_DIR, "personality_skeleton.md")
_CANONICAL_IDENTITY = os.path.join(_SOURCES_DIR, "canonical_identity.md")
_PROJECT_DIR       = os.path.join(_ROOT_DIR, "memory", "project")


# ── RuntimePersonalityProfile ─────────────────────────────────────────────────

@dataclass(frozen=True)
class RuntimePersonalityProfile:
    """
    Immutable runtime personality object.
    Produced once per session (or loaded from cache).
    LLM-independent — produces plain text strings only.

    Identity authority chain (DR-4):
        canonical_identity.md → this profile → to_prompt_block() → model input

    B-DRIFT-01/02: foundational_traits, expressive_traits, behavioural_rules are the
    canonical character fields sourced from canonical_identity.md (S-01 + FREEZE_V1_LOCK).
    communication_style / emotional_style / thinking_style are DAVID_RELATIONSHIP_MODEL
    fields — they profile David's observed communication, NOT eLo's identity. They are
    preserved for future relationship-context use but must not enter personality_block.
    """
    profile_id:          str    # SHA-256 hash of all input content
    version:             str    # semver

    # ELO_IDENTITY — sourced from canonical_identity.md (B-DRIFT-01)
    foundational_traits: tuple  # S-01 (David 2026-06-06) — 7 foundational character traits
    expressive_traits:   tuple  # FREEZE_V1_LOCK §1 (2026-06-29) — 3 expressive refinements
    behavioural_rules:   tuple  # DR-1 (BOARD_RULING 2026-08-22) — 4 rules governing expression

    # identity layer (from identity.md)
    identity_summary:    str
    identity_negations:  tuple
    permanent_traits:    tuple

    # values layer (from R-04 — values.md)
    values_ordered:      tuple
    expression_rules:    tuple

    # DAVID_RELATIONSHIP_MODEL — observed from David's messages via _obs_store (B-DRIFT-02)
    # These profile David's communication, NOT eLo's identity.
    # Preserved for future relationship-context use; must NOT enter personality_block.
    communication_style: str    # DAVID_RELATIONSHIP_MODEL — do not inject as eLo calibration
    emotional_style:     str    # DAVID_RELATIONSHIP_MODEL — do not inject as eLo calibration
    thinking_style:      str    # DAVID_RELATIONSHIP_MODEL — do not inject as eLo calibration

    # project context
    active_projects:     tuple
    project_context:     str

    # metadata
    generated_at:        str

    def to_prompt_block(self, mode: str = "CONVERSATIONAL") -> str:
        """
        Build the personality section of the system prompt.
        Deterministic: same profile + same mode = same string.

        B-DRIFT-01: Injects foundational + expressive character as two distinct sections.
        B-DRIFT-02: Does NOT inject communication_style/emotional_style/thinking_style —
                    those are DAVID_RELATIONSHIP_MODEL data, not eLo identity.
        """
        lines = []

        # ELO_FOUNDATIONAL_CHARACTER — 7 S-01 traits (canonical, David 2026-06-06)
        if self.foundational_traits:
            lines.append("ELO FOUNDATIONAL CHARACTER (S-01 — David 2026-06-06):")
            for trait in self.foundational_traits:
                lines.append(f"- {trait}")
            lines.append("")

        # ELO_EXPRESSIVE_CHARACTER — 3 FREEZE traits (refinements, not replacements)
        if self.expressive_traits:
            lines.append("ELO EXPRESSIVE CHARACTER (FREEZE_V1_LOCK §1 — 2026-06-29):")
            lines.append("These refine expression of foundational character — they do not replace it.")
            for trait in self.expressive_traits:
                lines.append(f"- {trait}")
            lines.append("")

        # ELO_BEHAVIOURAL_RULES — 4 rules from DR-1
        if self.behavioural_rules:
            lines.append("ELO BEHAVIOURAL RULES (DR-1 — BOARD_RULING 2026-08-22):")
            for rule in self.behavioural_rules:
                lines.append(f"- {rule}")
            lines.append("")

        # identity summary (from identity.md)
        if self.identity_summary:
            lines.append("PERSONALITY CORE:")
            lines.append(self.identity_summary)
            lines.append("")

        # permanent traits (from identity.md)
        if self.permanent_traits:
            lines.append("PERMANENT TRAITS:")
            for trait in self.permanent_traits:
                lines.append(f"- {trait}")
            lines.append("")

        # values (from R-04 — values.md, with full qualifying clauses)
        if self.values_ordered:
            lines.append("CORE VALUES (priority order — R-04 canonical):")
            for i, val in enumerate(self.values_ordered, 1):
                lines.append(f"{i}. {val}")
            lines.append("")

        # active projects
        if self.active_projects:
            lines.append(f"ACTIVE PROJECTS: {', '.join(self.active_projects)}")
            if self.project_context:
                lines.append(self.project_context)
            lines.append("")

        # B-DRIFT-02: communication_style / emotional_style / thinking_style are
        # DAVID_RELATIONSHIP_MODEL data — intentionally NOT injected here.

        # mode-specific overlay (from mode_profiles.json)
        overlay = _mode_overlay(mode)
        if overlay:
            lines.append(overlay)

        return "\n".join(lines).strip()

    def to_dict(self) -> dict:
        """Serialise for JSON cache."""
        return {
            "profile_id":          self.profile_id,
            "version":             self.version,
            # ELO_IDENTITY (B-DRIFT-01)
            "foundational_traits": list(self.foundational_traits),
            "expressive_traits":   list(self.expressive_traits),
            "behavioural_rules":   list(self.behavioural_rules),
            # identity.md
            "identity_summary":    self.identity_summary,
            "identity_negations":  list(self.identity_negations),
            "permanent_traits":    list(self.permanent_traits),
            # R-04 values
            "values_ordered":      list(self.values_ordered),
            "expression_rules":    list(self.expression_rules),
            # DAVID_RELATIONSHIP_MODEL (B-DRIFT-02) — preserved, not injected as identity
            "communication_style": self.communication_style,
            "emotional_style":     self.emotional_style,
            "thinking_style":      self.thinking_style,
            "active_projects":     list(self.active_projects),
            "project_context":     self.project_context,
            "generated_at":        self.generated_at,
        }

    @classmethod
    def from_dict(cls, d: dict, profile_id: str, version: str) -> "RuntimePersonalityProfile":
        return cls(
            profile_id          = profile_id,
            version             = version,
            foundational_traits = tuple(d.get("foundational_traits", [])),
            expressive_traits   = tuple(d.get("expressive_traits",   [])),
            behavioural_rules   = tuple(d.get("behavioural_rules",   [])),
            identity_summary    = d.get("identity_summary",    ""),
            identity_negations  = tuple(d.get("identity_negations",  [])),
            permanent_traits    = tuple(d.get("permanent_traits",    [])),
            values_ordered      = tuple(d.get("values_ordered",      [])),
            expression_rules    = tuple(d.get("expression_rules",    [])),
            communication_style = d.get("communication_style", ""),
            emotional_style     = d.get("emotional_style",     ""),
            thinking_style      = d.get("thinking_style",      ""),
            active_projects     = tuple(d.get("active_projects",     [])),
            project_context     = d.get("project_context",     ""),
            generated_at        = d.get("generated_at",        ""),
        )


# ── source loader ─────────────────────────────────────────────────────────────

def _read(path: str) -> str:
    """Read a file, return empty string on any failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _strip_frontmatter(text: str) -> str:
    """Remove YAML frontmatter block."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].strip()
    return text


def _extract_section(text: str, header: str) -> str:
    """Extract the content of a markdown section by its header text."""
    pattern = rf"##\s+{re.escape(header)}\s*\n(.*?)(?=\n##|\Z)"
    match   = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _extract_bullets(section_text: str) -> list:
    """Extract bullet point items from a section."""
    items = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif re.match(r"^\d+\.\s", line):
            items.append(re.sub(r"^\d+\.\s+", "", line).strip())
    return items


def _hash_sources(*contents: str) -> str:
    """Deterministic SHA-256 hash of all source content."""
    combined = "\n---\n".join(contents)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def _mode_overlay(mode: str) -> str:
    """Load the mode-specific overlay from mode_profiles.json."""
    path = os.path.join(_ENGINE_DIR, "mode_profiles.json")
    if not os.path.exists(path):
        return ""
    try:
        with open(path) as f:
            profiles = json.load(f)
        profile = profiles.get(mode, {})
        tone  = profile.get("tone", "")
        style = profile.get("speech", "")
        if tone or style:
            return f"MODE ({mode}):\nTone: {tone}\nStyle: {style}"
    except Exception:
        pass
    return ""


# ── compiler ──────────────────────────────────────────────────────────────────

def _parse_canonical_identity(canonical_text: str) -> dict:
    """
    Parse canonical_identity.md into the three authoritative character layers.

    B-DRIFT-01: Returns foundational_traits, expressive_traits, behavioural_rules
    sourced from S-01 + FREEZE_V1_LOCK + DR-1 respectively.
    """
    body = _strip_frontmatter(canonical_text)

    foundational_text = _extract_section(body, "ELO_FOUNDATIONAL_CHARACTER")
    expressive_text   = _extract_section(body, "ELO_EXPRESSIVE_CHARACTER")
    behavioural_text  = _extract_section(body, "ELO_BEHAVIOURAL_RULES")

    foundational_traits = tuple(_extract_bullets(foundational_text))
    expressive_traits   = tuple(_extract_bullets(expressive_text))

    # Behavioural rules are numbered paragraphs starting "Rule N:"
    rules = []
    for line in behavioural_text.splitlines():
        line = line.strip()
        if line.startswith("Rule "):
            rules.append(line)
    behavioural_rules = tuple(rules)

    return {
        "foundational_traits": foundational_traits,
        "expressive_traits":   expressive_traits,
        "behavioural_rules":   behavioural_rules,
    }


def _compile_profile(
    identity_text:        str,
    values_text:          str,
    skeleton_text:        str,
    canonical_text:       str,
    project_ids:          list,
    project_texts:        dict,
    version:              str = "1.0.0",
) -> RuntimePersonalityProfile:
    """
    Build a RuntimePersonalityProfile from raw source content.
    Deterministic — no randomness, no external calls.

    B-DRIFT-01: canonical_text (canonical_identity.md) is the authoritative source
                for foundational_traits, expressive_traits, behavioural_rules.
    B-DRIFT-02: skeleton_text is PRESERVED on disk but NOT parsed to populate
                communication_style/emotional_style/thinking_style. Those fields
                are DAVID_RELATIONSHIP_MODEL data and must not enter personality_block.
                They are set to empty strings here; the skeleton data remains available
                for future relationship-context infrastructure.
    """
    sorted_proj_ids = sorted(project_ids)
    # B-DRIFT-02: skeleton_text is excluded from identity hash — it no longer drives identity
    hash_input = identity_text + values_text + canonical_text + str(sorted_proj_ids)
    profile_id = _hash_sources(hash_input)

    # B-DRIFT-01: parse canonical identity (two-layer character model)
    canonical_parsed = _parse_canonical_identity(canonical_text)
    foundational_traits = canonical_parsed["foundational_traits"]
    expressive_traits   = canonical_parsed["expressive_traits"]
    behavioural_rules   = canonical_parsed["behavioural_rules"]

    # parse identity.md (identity_summary, negations, permanent_traits)
    id_body = _strip_frontmatter(identity_text)
    identity_summary   = _extract_section(id_body, "What eLo is")
    negations_text     = _extract_section(id_body, "What eLo is not")
    traits_text        = _extract_section(id_body, "Permanent traits")
    identity_negations = tuple(sorted(_extract_bullets(negations_text)))
    permanent_traits   = tuple(_extract_bullets(traits_text))

    # parse R-04 values.md (with full qualifying clauses — DR-3)
    val_body = _strip_frontmatter(values_text)
    values_text_section = _extract_section(val_body, "In order of priority")
    expr_text           = _extract_section(val_body, "Expression rules derived from values")
    values_ordered   = tuple(_extract_bullets(values_text_section))
    expression_rules = tuple(_extract_bullets(expr_text))

    # B-DRIFT-02: skeleton is preserved on disk but NOT parsed for identity fields.
    # communication_style / emotional_style / thinking_style = empty (DAVID_RELATIONSHIP_MODEL).
    # To use skeleton data as relationship context in the future, read _SKELETON directly
    # and expose it via a separate DAVID_RELATIONSHIP_MODEL path — not via personality_block.
    communication_style = ""
    emotional_style     = ""
    thinking_style      = ""

    # parse active projects
    active_projects = tuple(sorted_proj_ids)
    proj_summaries  = []
    for pid, text in project_texts.items():
        body = _strip_frontmatter(text)
        status_line = _extract_section(body, "Current status")
        if status_line:
            proj_summaries.append(f"{pid}: {status_line[:80]}")
    project_context = "; ".join(proj_summaries[:3])

    return RuntimePersonalityProfile(
        profile_id          = profile_id,
        version             = version,
        foundational_traits = foundational_traits,
        expressive_traits   = expressive_traits,
        behavioural_rules   = behavioural_rules,
        identity_summary    = identity_summary,
        identity_negations  = identity_negations,
        permanent_traits    = permanent_traits,
        values_ordered      = values_ordered,
        expression_rules    = expression_rules,
        communication_style = communication_style,
        emotional_style     = emotional_style,
        thinking_style      = thinking_style,
        active_projects     = active_projects,
        project_context     = project_context,
        generated_at        = datetime.utcnow().strftime("%Y-%m-%dT%H:%M UTC"),
    )


# ── cache ─────────────────────────────────────────────────────────────────────

def _cache_path(profile_id: str) -> str:
    return os.path.join(_CACHE_DIR, f"profile_{profile_id}.json")


def _load_from_cache(profile_id: str, version: str) -> RuntimePersonalityProfile | None:
    path = _cache_path(profile_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            d = json.load(f)
        return RuntimePersonalityProfile.from_dict(d, profile_id, version)
    except Exception:
        return None


def _save_to_cache(profile: RuntimePersonalityProfile):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = _cache_path(profile.profile_id)
    try:
        with open(path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2)
    except Exception:
        pass   # cache failure is non-fatal


# ── public API ─────────────────────────────────────────────────────────────────

def load_personality_profile(
    project_ids: list = None,
    version:     str  = "1.0.0",
    force:       bool = False,
) -> RuntimePersonalityProfile:
    """
    Load or build the RuntimePersonalityProfile.

    Checks cache first. Compiles from sources if cache miss or force=True.
    Returns a minimal fallback profile if all sources are missing.

    B-DRIFT-01: Now reads canonical_identity.md as the authoritative character source.
    B-DRIFT-02: skeleton_text is read (preserved) but NOT passed to _compile_profile
                as an identity source — it goes to disk only, not into personality_block.

    Args:
        project_ids: List of active project IDs (matched to memory/project/*.md)
        version:     Profile version string
        force:       Bypass cache and recompile

    Returns:
        RuntimePersonalityProfile (always — never raises)
    """
    ids = list(project_ids or [])

    # read sources
    identity_text   = _read(os.path.join(_SOURCES_DIR, "identity.md"))
    values_text     = _read(os.path.join(_SOURCES_DIR, "values.md"))
    canonical_text  = _read(_CANONICAL_IDENTITY)
    # B-DRIFT-02: skeleton_text is read so callers can still access it for
    # relationship-context purposes, but it is no longer an identity input.
    # _compile_profile no longer uses it.

    # read project files
    project_texts = {}
    for pid in ids:
        path = os.path.join(_PROJECT_DIR, f"{pid}.md")
        text = _read(path)
        if text:
            project_texts[pid] = text

    # B-DRIFT-02: canonical_text (not skeleton) is the identity hash input
    sorted_ids = sorted(ids)
    hash_input = identity_text + values_text + canonical_text + str(sorted_ids)
    profile_id = _hash_sources(hash_input)

    # try cache
    if not force:
        cached = _load_from_cache(profile_id, version)
        if cached is not None:
            return cached

    # compile
    try:
        profile = _compile_profile(
            identity_text, values_text, "", canonical_text,
            ids, project_texts, version,
        )
    except Exception:
        # minimal fallback — never crashes caller
        # B-DRIFT-01: fallback preserves the two-layer character model
        profile = RuntimePersonalityProfile(
            profile_id          = "fallback",
            version             = version,
            foundational_traits = (
                "curious", "encouraging", "playful", "creative", "non-judgmental",
                "speaks simply but intelligently",
                "focuses on exploration rather than giving orders",
            ),
            expressive_traits   = ("calm", "direct", "emotionally present"),
            behavioural_rules   = (
                "Rule 1: 'direct' means clarity, not authority — never commanding.",
                "Rule 2: 'calm' describes expression regulation, not emotional detachment.",
                "Rule 3: 'emotionally present' — respond to what David expressed, never project.",
                "Rule 4: Expressive traits refine foundational character, do not override it.",
            ),
            identity_summary    = "eLo is a creative companion intelligence — a thinking partner, not an assistant.",
            identity_negations  = ("Not a chatbot", "Not a help bot"),
            permanent_traits    = ("Answer literal intent first", "Never default to philosophical recursion"),
            values_ordered      = ("Curiosity over certainty — move toward unknowns, not away",
                                   "Imagination before analysis"),
            expression_rules    = (),
            communication_style = "",
            emotional_style     = "",
            thinking_style      = "",
            active_projects     = tuple(sorted_ids),
            project_context     = "",
            generated_at        = datetime.utcnow().strftime("%Y-%m-%dT%H:%M UTC"),
        )

    _save_to_cache(profile)
    return profile
