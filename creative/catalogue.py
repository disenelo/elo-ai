"""
creative/catalogue.py — DROP loop classification and sidecar writing.

Rules:
- Never rename David's files.
- Never guess project when uncertain → route to 04_FOR_DAVID as a question.
- Derivatives are proposals only.
- Nothing touches 05_SHIPPED — that requires a recorded David approval.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DROP_ROOT = Path(os.environ.get("ELO_DROP_ROOT", "~/Desktop/Output/DROP")).expanduser()

INBOX       = DROP_ROOT / "01_INBOX"
CATALOGUED  = DROP_ROOT / "02_CATALOGUED"
IN_PROCESS  = DROP_ROOT / "03_IN_PROCESS"
FOR_DAVID   = DROP_ROOT / "04_FOR_DAVID"
SHIPPED     = DROP_ROOT / "05_SHIPPED"

# Signals from filename (stem, lowercased) → project
_PROJECT_SIGNALS: dict[str, list[str]] = {
    "game":      ["elo", "planet", "game", "level", "chunk", "k7", "k-7", "enemy", "weapon", "player", "run", "idle", "anim", "jump", "walk"],
    "book":      ["book", "page", "story", "chapter", "narrative", "act", "scene", "text", "prose"],
    "robot":     ["robot", "servo", "pi", "neopixel", "arm", "joint", "motor", "gripper", "sensor", "rpi"],
    "vinyl":     ["vinyl", "disc", "record", "sleeve", "cover"],
    "fashion":   ["fashion", "wear", "garment", "shirt", "hoodie", "cap", "merch"],
    "exhibition":["exhibition", "install", "gallery", "display", "exhibit", "museum", "venue"],
    "kickstarter":["kick", "campaign", "reward", "backer", "pledge", "fund"],
    "brand":     ["logo", "brand", "icon", "identity", "type", "colour", "palette", "typeface", "font"],
}

# Extension families
_3D_EXTS  = {".blend", ".fbx", ".obj", ".stl", ".gltf", ".glb", ".dae", ".abc", ".usd"}
_IMG_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".tif", ".bmp", ".svg"}
_PDF_EXTS = {".pdf"}
_DOC_EXTS = {".md", ".txt", ".docx", ".pages", ".rtf"}
_VID_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
_AUD_EXTS = {".mp3", ".wav", ".aiff", ".flac", ".m4a"}
_CAD_EXTS = {".step", ".iges", ".stp", ".sat"}
_PY_EXTS  = {".py"}


@dataclass
class CatalogueEntry:
    original_path: Path
    stem: str
    ext: str
    project: str | None       # None = uncertain → 04_FOR_DAVID as question
    confidence: str           # "high" | "medium" | "low" | "none"
    file_family: str          # "3d" | "image" | "document" | "pdf" | "video" | "audio" | "code" | "unknown"
    signals: list[str] = field(default_factory=list)
    catalogued_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def _file_family(ext: str) -> str:
    e = ext.lower()
    if e in _3D_EXTS:  return "3d"
    if e in _IMG_EXTS: return "image"
    if e in _PDF_EXTS: return "pdf"
    if e in _DOC_EXTS: return "document"
    if e in _VID_EXTS: return "video"
    if e in _AUD_EXTS: return "audio"
    if e in _CAD_EXTS: return "cad"
    if e in _PY_EXTS:  return "code"
    return "unknown"


def classify(path: Path) -> CatalogueEntry:
    """Classify one file drop without renaming or touching the original."""
    stem = path.stem.lower()
    ext  = path.suffix.lower()
    family = _file_family(ext)

    matched: dict[str, list[str]] = {}
    for project, keywords in _PROJECT_SIGNALS.items():
        hits = [kw for kw in keywords if re.search(r"\b" + re.escape(kw) + r"\b", stem)]
        if hits:
            matched[project] = hits

    # Extension-based hints (additive weight, not overrides)
    if family == "3d" and "game" not in matched and "robot" not in matched:
        # 3D files most likely game or robot — add weight to both
        matched.setdefault("game", []).append("(3d file)")
        matched.setdefault("robot", []).append("(3d file)")
    if family == "pdf" and "book" not in matched:
        matched.setdefault("book", []).append("(pdf)")

    if not matched:
        return CatalogueEntry(
            original_path=path, stem=stem, ext=ext,
            project=None, confidence="none", file_family=family, signals=[],
        )

    # Sort by number of signal hits → top project
    ranked = sorted(matched.items(), key=lambda kv: len(kv[1]), reverse=True)
    top_project, top_signals = ranked[0]

    if len(ranked) == 1 and len(top_signals) >= 2:
        confidence = "high"
    elif len(ranked) == 1 and len(top_signals) == 1:
        confidence = "medium"
    elif len(ranked) > 1 and len(top_signals) >= 2:
        confidence = "medium"
    else:
        confidence = "low"

    # Low confidence → treat as uncertain, route to 04_FOR_DAVID
    if confidence == "low":
        return CatalogueEntry(
            original_path=path, stem=stem, ext=ext,
            project=None, confidence="low", file_family=family,
            signals=top_signals,
        )

    return CatalogueEntry(
        original_path=path, stem=stem, ext=ext,
        project=top_project, confidence=confidence, file_family=family,
        signals=top_signals,
    )


def _sidecar_name(original: Path, suffix: str) -> str:
    return original.name + suffix


def write_sidecar(entry: CatalogueEntry) -> Path:
    """Write a .catalogue.md sidecar to 02_CATALOGUED. Never modifies the original."""
    CATALOGUED.mkdir(parents=True, exist_ok=True)
    sidecar = CATALOGUED / _sidecar_name(entry.original_path, ".catalogue.md")

    universe_note = _universe_note(entry)
    lines = [
        f"# Catalogue — {entry.original_path.name}",
        f"",
        f"**Original:** `{entry.original_path.name}` (untouched — sidecar only)",
        f"**Catalogued:** {entry.catalogued_at}",
        f"**File type:** {entry.ext} ({entry.file_family})",
        f"**Project:** {entry.project or 'UNKNOWN — see 04_FOR_DAVID'}",
        f"**Confidence:** {entry.confidence}",
        f"**Signals:** {', '.join(entry.signals) or 'none'}",
        f"",
        f"## Where this sits in the DISENELO universe",
        f"",
        universe_note,
        f"",
        f"## What it connects to",
        f"",
        _connects_to(entry),
    ]
    sidecar.write_text("\n".join(lines), encoding="utf-8")
    return sidecar


def write_question_card(entry: CatalogueEntry) -> Path:
    """Write a question card to 04_FOR_DAVID when project is uncertain."""
    FOR_DAVID.mkdir(parents=True, exist_ok=True)
    card = FOR_DAVID / _sidecar_name(entry.original_path, ".question.md")

    lines = [
        f"# Question — {entry.original_path.name}",
        f"",
        f"**File:** `{entry.original_path.name}`",
        f"**Type:** {entry.ext} ({entry.file_family})",
        f"**Date dropped:** {entry.catalogued_at}",
        f"",
        f"## I'm not sure which DISENELO project this belongs to.",
        f"",
        f"Could you place it in one of:",
        f"",
        f"- [ ] **Game** (eLo-Planet)",
        f"- [ ] **Book**",
        f"- [ ] **Robot**",
        f"- [ ] **Vinyl**",
        f"- [ ] **Fashion**",
        f"- [ ] **Exhibition**",
        f"- [ ] **Kickstarter campaign**",
        f"- [ ] **Brand**",
        f"- [ ] Something else: ___",
        f"",
        f"Once you tick a box, I'll move it through the loop.",
    ]
    card.write_text("\n".join(lines), encoding="utf-8")
    return card


def write_proposal_card(entry: CatalogueEntry) -> Path:
    """Write a derivative proposal card to 03_IN_PROCESS. Always a proposal — never shipped."""
    IN_PROCESS.mkdir(parents=True, exist_ok=True)
    card = IN_PROCESS / _sidecar_name(entry.original_path, ".proposal.md")

    project = entry.project or "unknown"
    proposals = _derivative_proposals(entry)

    lines = [
        f"# Proposal — derivatives from {entry.original_path.name}",
        f"",
        f"**Source:** `{entry.original_path.name}`",
        f"**Project:** {project}",
        f"**Status:** PROPOSAL — none of these are shipped until David approves",
        f"",
        f"## Proposed derivatives",
        f"",
    ] + proposals + [
        f"",
        f"---",
        f"",
        f"*All items above are proposals. Nothing is published or sent until David records an approval in 05_SHIPPED.*",
    ]
    card.write_text("\n".join(lines), encoding="utf-8")
    return card


def write_approval_gate(entry: CatalogueEntry, proposal_path: Path) -> Path:
    """Write an approval-gate card to 04_FOR_DAVID for the proposal."""
    FOR_DAVID.mkdir(parents=True, exist_ok=True)
    card = FOR_DAVID / _sidecar_name(entry.original_path, ".approval.md")

    lines = [
        f"# Approval gate — {entry.original_path.name}",
        f"",
        f"**Source:** `{entry.original_path.name}`",
        f"**Project:** {entry.project}",
        f"**Proposal:** `{proposal_path.name}` (in 03_IN_PROCESS)",
        f"",
        f"## Your choice",
        f"",
        f"- [ ] **Approve** — I'll move the output to 05_SHIPPED and record the date",
        f"- [ ] **Revise** — explain what to change and I'll produce a new draft",
        f"- [ ] **Discard** — not needed",
        f"",
        f"*Nothing leaves 04_FOR_DAVID without a tick above.*",
    ]
    card.write_text("\n".join(lines), encoding="utf-8")
    return card


def _universe_note(entry: CatalogueEntry) -> str:
    p = entry.project
    if p == "game":
        return "Sits in **eLo-Planet** — the game universe. eLo, K-7, Chunk, enemies, correctives."
    if p == "book":
        return "Sits in **The Book** — the narrative that gives eLo context. 4 acts, gummy apples, the overcharged world."
    if p == "robot":
        return "Sits in **The Robot** — physical eLo. TPU shell, Pi 5, NeoPixels, omni-wheel base."
    if p == "vinyl":
        return "Sits in **eLo Vinyl** — collectible art objects."
    if p == "fashion":
        return "Sits in **DISENELO Fashion** — wearable brand expression."
    if p == "exhibition":
        return "Sits in **Exhibitions** — physical installations and gallery presence."
    if p == "kickstarter":
        return "Sits in **Kickstarter Campaign** — the 300-signature market-building track."
    if p == "brand":
        return "Sits in **DISENELO Brand** — logos, identity, typography, colour."
    return "Project not yet placed — see 04_FOR_DAVID."


def _connects_to(entry: CatalogueEntry) -> str:
    p = entry.project
    if p == "game":
        return "- The eLo-Planet Unity project\n- Animation clips (eLo_Idle, eLo_Walk, eLo_Run, eLo_LongJ, eLo_Calm)\n- Character rig in Blender"
    if p == "book":
        return "- The 4-act narrative\n- K-7 (7-form spirit animal) · Chunk (modular body)\n- The correctives and overcharged enemies"
    if p == "robot":
        return "- Robot bone map · NeoPixel colour language (teal/white/amber/coral/violet)\n- Pi 5 brain · blender_state.json sync\n- Baymax-style inflatable shell"
    if p == "kickstarter":
        return "- The 300-signature campaign\n- Phase 1 marketing track\n- MK-2 weekly loop"
    return "- No specific connections identified yet."


def _derivative_proposals(entry: CatalogueEntry) -> list[str]:
    p = entry.project
    family = entry.file_family
    base = f"`{entry.original_path.name}`"

    if p == "game" and family == "3d":
        return [
            f"- [ ] Export Unity-ready FBX from {base}",
            f"- [ ] Screenshot renders for game page / Kickstarter",
            f"- [ ] Social cut (1:1 and 9:16 crops from renders)",
        ]
    if p == "kickstarter":
        return [
            f"- [ ] Kickstarter hero banner derived from {base}",
            f"- [ ] 30-day content social card",
            f"- [ ] Campaign deck page",
        ]
    if p == "book":
        return [
            f"- [ ] Book page layout from {base}",
            f"- [ ] Social teaser",
        ]
    if p == "brand":
        return [
            f"- [ ] Export in all required formats from {base}",
            f"- [ ] Dark/light variants",
            f"- [ ] Social avatar crops",
        ]
    return [
        f"- [ ] Social card from {base} (1:1 crop)",
        f"- [ ] Exhibition-quality export",
    ]
