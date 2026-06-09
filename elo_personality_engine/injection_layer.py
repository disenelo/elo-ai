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

_ENGINE_DIR  = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR    = os.path.dirname(_ENGINE_DIR)
_SOURCES_DIR = os.path.join(_ENGINE_DIR, "sources")
_CACHE_DIR   = os.path.join(_ROOT_DIR, "memory", "profile_cache")
_SKELETON    = os.path.join(_ROOT_DIR, "personality_skeleton.md")
_PROJECT_DIR = os.path.join(_ROOT_DIR, "memory", "project")


# ── RuntimePersonalityProfile ─────────────────────────────────────────────────

@dataclass(frozen=True)
class RuntimePersonalityProfile:
    """
    Immutable runtime personality object.
    Produced once per session (or loaded from cache).
    LLM-independent — produces plain text strings only.
    """
    profile_id:          str    # SHA-256 hash of all input content
    version:             str    # semver

    # identity layer
    identity_summary:    str
    identity_negations:  tuple
    permanent_traits:    tuple

    # values layer
    values_ordered:      tuple
    expression_rules:    tuple

    # behavioural patterns (from skeleton — high/medium confidence only)
    communication_style: str
    emotional_style:     str
    thinking_style:      str

    # project context
    active_projects:     tuple
    project_context:     str

    # metadata
    generated_at:        str

    def to_prompt_block(self, mode: str = "CONVERSATIONAL") -> str:
        """
        Build the personality section of the system prompt.
        Deterministic: same profile + same mode = same string.
        """
        lines = []

        # identity
        if self.identity_summary:
            lines.append("PERSONALITY CORE:")
            lines.append(self.identity_summary)
            lines.append("")

        # permanent traits
        if self.permanent_traits:
            lines.append("PERMANENT TRAITS:")
            for trait in self.permanent_traits:
                lines.append(f"- {trait}")
            lines.append("")

        # values
        if self.values_ordered:
            lines.append("CORE VALUES (priority order):")
            for i, val in enumerate(self.values_ordered, 1):
                lines.append(f"{i}. {val}")
            lines.append("")

        # active projects
        if self.active_projects:
            lines.append(f"ACTIVE PROJECTS: {', '.join(self.active_projects)}")
            if self.project_context:
                lines.append(self.project_context)
            lines.append("")

        # communication calibration (from skeleton)
        if self.communication_style:
            lines.append("COMMUNICATION CALIBRATION:")
            lines.append(self.communication_style)
            lines.append("")

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
            "identity_summary":    self.identity_summary,
            "identity_negations":  list(self.identity_negations),
            "permanent_traits":    list(self.permanent_traits),
            "values_ordered":      list(self.values_ordered),
            "expression_rules":    list(self.expression_rules),
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

def _compile_profile(
    identity_text:  str,
    values_text:    str,
    skeleton_text:  str,
    project_ids:    list,
    project_texts:  dict,
    version:        str = "1.0.0",
) -> RuntimePersonalityProfile:
    """
    Build a RuntimePersonalityProfile from raw source content.
    Deterministic — no randomness, no external calls.
    """
    # hash all inputs
    sorted_proj_ids = sorted(project_ids)
    hash_input = identity_text + values_text + skeleton_text + str(sorted_proj_ids)
    profile_id = _hash_sources(hash_input)

    # parse identity
    id_body = _strip_frontmatter(identity_text)
    identity_summary   = _extract_section(id_body, "What eLo is")
    negations_text     = _extract_section(id_body, "What eLo is not")
    traits_text        = _extract_section(id_body, "Permanent traits")
    identity_negations = tuple(sorted(_extract_bullets(negations_text)))
    permanent_traits   = tuple(_extract_bullets(traits_text))

    # parse values
    val_body = _strip_frontmatter(values_text)
    values_text_section = _extract_section(val_body, "In order of priority")
    expr_text           = _extract_section(val_body, "Expression rules derived from values")
    values_ordered  = tuple(_extract_bullets(values_text_section))
    expression_rules = tuple(_extract_bullets(expr_text))

    # parse skeleton (high + medium confidence only)
    skel_body = _strip_frontmatter(skeleton_text)
    comm_section = _extract_section(skel_body, "1. Communication Style")
    emot_section = _extract_section(skel_body, "2. Emotional Patterns")
    think_section = _extract_section(skel_body, "3. Thinking Style")

    # extract first meaningful line from each section
    def _first_line(text: str) -> str:
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("|"):
                return line[:200]
        return ""

    communication_style = _first_line(comm_section)
    emotional_style     = _first_line(emot_section)
    thinking_style      = _first_line(think_section)

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

    Args:
        project_ids: List of active project IDs (matched to memory/project/*.md)
        version:     Profile version string
        force:       Bypass cache and recompile

    Returns:
        RuntimePersonalityProfile (always — never raises)
    """
    ids = list(project_ids or [])

    # read sources
    identity_text = _read(os.path.join(_SOURCES_DIR, "identity.md"))
    values_text   = _read(os.path.join(_SOURCES_DIR, "values.md"))
    skeleton_text = _read(_SKELETON)

    # read project files
    project_texts = {}
    for pid in ids:
        path = os.path.join(_PROJECT_DIR, f"{pid}.md")
        text = _read(path)
        if text:
            project_texts[pid] = text

    # compute profile_id
    sorted_ids = sorted(ids)
    hash_input = identity_text + values_text + skeleton_text + str(sorted_ids)
    profile_id = _hash_sources(hash_input)

    # try cache
    if not force:
        cached = _load_from_cache(profile_id, version)
        if cached is not None:
            return cached

    # compile
    try:
        profile = _compile_profile(
            identity_text, values_text, skeleton_text,
            ids, project_texts, version,
        )
    except Exception:
        # minimal fallback — never crashes caller
        profile = RuntimePersonalityProfile(
            profile_id          = "fallback",
            version             = version,
            identity_summary    = "eLo is a creative companion intelligence — a thinking partner, not an assistant.",
            identity_negations  = ("Not a chatbot", "Not a help bot"),
            permanent_traits    = ("Answer literal intent first", "Never default to philosophical recursion"),
            values_ordered      = ("Curiosity over certainty", "Imagination before analysis"),
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
