"""
faculties/perception/perception_faculty.py — Perception Faculty (WO-009)

Transforms raw multimodal sensor output into one typed PerceptionResult per turn.
Architecture Audit gap #5. Addresses the missing unified perception transform.

Spec:  docs/architecture/Volume_XII/01_Perception_Faculty.md
Canon: "Sensation ≠ perception. Layer 1 captures; Layer 2 interprets."

Rules (MUST):
  - Interprets; never decides (One Brain).
  - Each modality is independently degradable — one failing never blocks the result.
  - Anti-fabrication: if vision is absent/denied, source_health.vision='absent'.
    eLo must NOT claim to see the screen in that case.
  - Produces exactly ONE frozen PerceptionResult per turn.
  - Confidence may only be lowered when modalities are missing.
"""

from __future__ import annotations

import json
import os
import time as _time
from dataclasses import dataclass, field
from typing import Literal

_SURFACE = Literal["creative", "code", "browser", "terminal", "media", "idle", "unknown"]
_ACTIVITY = Literal["working", "browsing", "watching", "away", "conversing", "unknown"]
_SOURCE_STATUS = Literal["live", "stale", "absent"]

# App name → surface mapping
_APP_TO_SURFACE: dict[str, str] = {
    "code":        "code",
    "vscode":      "code",
    "xcode":       "code",
    "pycharm":     "code",
    "vim":         "code",
    "nvim":        "code",
    "terminal":    "terminal",
    "iterm":       "terminal",
    "safari":      "browser",
    "chrome":      "browser",
    "firefox":     "browser",
    "arc":         "browser",
    "brave":       "browser",
    "figma":       "creative",
    "blender":     "creative",
    "photoshop":   "creative",
    "illustrator": "creative",
    "procreate":   "creative",
    "davinci":     "media",
    "premiere":    "media",
    "final cut":   "media",
    "vlc":         "media",
    "spotify":     "media",
    "notes":       "idle",
    "finder":      "idle",
}

_SURFACE_TO_ACTIVITY: dict[str, str] = {
    "code":      "working",
    "terminal":  "working",
    "creative":  "working",
    "browser":   "browsing",
    "media":     "watching",
    "idle":      "away",
    "unknown":   "unknown",
}


# ── WO-025: Spatial sensor (Vol XV §2) ───────────────────────────────────────

_SPATIAL_TRACE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "blender", "spatial_trace.json",
)
_SPATIAL_FRAME_COUNTER = [0]


@dataclass(frozen=True)
class SpatialPoint:
    x:    float = 0.0
    y:    float = 0.0
    z:    float = 0.0
    conf: float = 1.0


@dataclass(frozen=True)
class SpatialFrame:
    """
    Vol XV §2 spatial frame — normalised pointcloud/depth snapshot.
    x/y/z in normalised [−1, 1]; conf in [0, 1].
    """
    points:   tuple           = field(default_factory=tuple)   # tuple[SpatialPoint]
    frame_id: str             = ""
    ts:       float           = 0.0
    source:   str             = "stub"

    def as_dict(self) -> dict:
        return {
            "points":   [{"x": p.x, "y": p.y, "z": p.z, "conf": p.conf} for p in self.points],
            "frame_id": self.frame_id,
            "ts":       self.ts,
            "source":   self.source,
        }


def _stub_spatial_frame() -> SpatialFrame:
    """
    Synthetic depth-camera stub — 16 points on a flat surface at z≈0.5.
    Deterministic-ish per frame_id; suitable for schema validation and INT-3.
    """
    _SPATIAL_FRAME_COUNTER[0] += 1
    fid = f"f{_SPATIAL_FRAME_COUNTER[0]:06d}"
    now = _time.time()
    import math
    pts = []
    for i in range(16):
        angle = (i / 16.0) * 2.0 * math.pi
        r = 0.3 + 0.1 * (i % 4) / 3.0
        pts.append(SpatialPoint(
            x=round(r * math.cos(angle), 4),
            y=round(r * math.sin(angle), 4),
            z=round(0.5 + 0.05 * math.sin(angle * 2), 4),
            conf=round(0.85 + 0.1 * (i % 3) / 2.0, 4),
        ))
    return SpatialFrame(points=tuple(pts), frame_id=fid, ts=now, source="stub")


def _emit_spatial_trace(frame: SpatialFrame) -> None:
    """Atomic write of spatial_trace.json for observability."""
    try:
        payload = {
            "frame_id":    frame.frame_id,
            "point_count": len(frame.points),
            "source":      frame.source,
            "_ts":         frame.ts,
        }
        tmp = _SPATIAL_TRACE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _SPATIAL_TRACE_PATH)
    except Exception:
        pass


# ── PerceptionResult ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SalientObject:
    label:     str   = ""
    where:     str   = ""    # e.g. "top-left", "centre", "dock"
    relevance: float = 0.0   # 0.0–1.0


@dataclass(frozen=True)
class PerceptionResult:
    """
    One frozen per-turn result of the Perception Faculty.
    Feeds LiveWorldState (Vol XV) and CognitiveState.

    FT-2: produced once per turn; frozen.
    Ch.4 §4.3: partial=True when confidence < 0.7 or a primary modality is absent.
    """
    modality_reads:  dict              = field(default_factory=dict)   # {vision, window, voice, files} → raw text
    scene:           str               = ""         # one-line context ("focused coding session in VS Code")
    active_surface:  str               = "unknown"  # creative|code|browser|terminal|media|idle|unknown
    salient_objects: tuple             = field(default_factory=tuple)  # tuple[SalientObject], relevance-ranked
    user_activity:   str               = "unknown"  # working|browsing|watching|away|conversing|unknown
    confidence:      float             = 1.0        # 0.0–1.0; lower when modalities missing
    source_health:   dict              = field(default_factory=dict)   # {source: {status, ts}}
    spatial_frame:   "SpatialFrame | None" = None  # WO-025: Vol XV §2 spatial domain; None when ELO_SPATIAL_SENSOR not set
    partial:         bool              = False      # Ch.4 §4.3: True when confidence < 0.7 or primary modality absent


# ── Interpret helpers ─────────────────────────────────────────────────────────

def _infer_surface(app_name: str) -> str:
    name = app_name.lower()
    for key, surface in _APP_TO_SURFACE.items():
        if key in name:
            return surface
    return "unknown"


def _infer_activity(surface: str, user_present: bool = True) -> str:
    if not user_present:
        return "unknown"  # no window data = can't determine presence
    return _SURFACE_TO_ACTIVITY.get(surface, "unknown")


def _infer_scene(app_name: str, window_title: str, surface: str) -> str:
    if not app_name and not window_title:
        return "idle session"
    parts = []
    if surface != "unknown":
        parts.append(f"{surface} session")
    if app_name:
        parts.append(f"in {app_name}")
    if window_title and window_title.lower() != app_name.lower():
        short = window_title[:40]
        parts.append(f"— {short}")
    return " ".join(parts) or "active session"


def _source_health(status: str, ts: float = 0.0) -> dict:
    return {"status": status, "ts": ts}


# ── Core: perceive() ──────────────────────────────────────────────────────────

def perceive(
    vision_text:      str | None = None,   # GPT-4o vision description
    window_app:       str | None = None,   # frontmost application name
    window_title:     str | None = None,   # window title
    voice_transcript: str | None = None,   # Whisper STT result
    file_context:     str | None = None,   # dropped/recent file context
    vision_permitted: bool       = True,   # False if screen-record denied
    spatial_data:     "SpatialFrame | None" = None,  # WO-025: pre-fetched frame or None
) -> PerceptionResult:
    """
    Transform raw sensor input into one frozen PerceptionResult.

    FT-1: given sensor data, produce a meaningful scene + surface + activity.
    ST-1: each modality independent — any absent = status:absent, confidence lowered.
    ST-2: vision denied → source_health.vision=absent; eLo never claims to see screen.
    ST-3: ambiguous → low confidence + generic; no fabrication.
    """
    import time
    now_ts = time.time()
    source_health: dict[str, dict] = {}
    modality_reads: dict[str, str] = {}
    confidence = 1.0
    confidence_penalties: list[float] = []

    # ── Window (authoritative surface/activity source) ────────────────────────
    if window_app is not None:
        modality_reads["window"] = f"{window_app}: {window_title or ''}".strip(": ")
        source_health["window"] = _source_health("live", now_ts)
    else:
        source_health["window"] = _source_health("absent", 0.0)
        confidence_penalties.append(0.15)

    # ── Vision (visual description from screen capture) ───────────────────────
    if not vision_permitted:
        source_health["vision"] = _source_health("absent", 0.0)
        confidence_penalties.append(0.1)
    elif vision_text is not None:
        modality_reads["vision"] = vision_text[:300]
        source_health["vision"] = _source_health("live", now_ts)
    else:
        source_health["vision"] = _source_health("absent", 0.0)
        confidence_penalties.append(0.05)

    # ── Voice ─────────────────────────────────────────────────────────────────
    if voice_transcript is not None:
        modality_reads["voice"] = voice_transcript[:200]
        source_health["voice"] = _source_health("live", now_ts)
    else:
        source_health["voice"] = _source_health("absent", 0.0)

    # ── Files ─────────────────────────────────────────────────────────────────
    if file_context is not None:
        modality_reads["files"] = file_context[:200]
        source_health["files"] = _source_health("live", now_ts)
    else:
        source_health["files"] = _source_health("absent", 0.0)

    # ── Spatial (WO-025: Vol XV §2) ───────────────────────────────────────────
    if spatial_data is not None:
        source_health["spatial"] = _source_health("live", spatial_data.ts)
    else:
        source_health["spatial"] = _source_health("absent", 0.0)

    # ── Interpret surface + activity ──────────────────────────────────────────
    app = window_app or ""
    title = window_title or ""
    surface = _infer_surface(app) if app else "unknown"
    activity = _infer_activity(surface, user_present=bool(app))

    # ── Scene ─────────────────────────────────────────────────────────────────
    scene = _infer_scene(app, title, surface)

    # ── Salient objects (from vision text if available) ───────────────────────
    salient: list[SalientObject] = []
    if vision_text and vision_permitted:
        # Simple keyword extraction — full CV pipeline is for later phases
        words = set(vision_text.lower().split())
        objects_of_interest = ["monitor", "keyboard", "mouse", "mug", "phone", "notebook",
                                "code", "text", "image", "browser", "window", "desk"]
        for obj in objects_of_interest:
            if obj in words:
                salient.append(SalientObject(label=obj, where="visible", relevance=0.5))

    # ── Confidence ────────────────────────────────────────────────────────────
    for penalty in confidence_penalties:
        confidence = max(0.0, confidence - penalty)

    # Scene confidence degrades on ambiguous surface
    if surface == "unknown":
        confidence = max(0.0, confidence - 0.1)

    _confidence_final = round(confidence, 3)
    # Ch.4 §4.3: partial when primary modalities (window, vision) are absent or confidence low
    _partial = (
        _confidence_final < 0.7
        or source_health.get("window", {}).get("status") == "absent"
        or (not vision_permitted and source_health.get("vision", {}).get("status") == "absent")
    )

    return PerceptionResult(
        modality_reads=modality_reads,
        scene=scene,
        active_surface=surface,
        salient_objects=tuple(salient),
        user_activity=activity,
        confidence=_confidence_final,
        source_health=source_health,
        spatial_frame=spatial_data,
        partial=_partial,
    )


# ── Convenience: perceive_from_live_state ─────────────────────────────────────

def perceive_from_live_state() -> PerceptionResult:
    """
    Perceive from available live sensors (window state + vision cache).
    Called at top of turn by the spine / CognitiveState assembly.
    Gracefully degrades — any sensor failure returns absent for that modality.
    """
    app: str | None = None
    title: str | None = None
    vision_text: str | None = None

    try:
        from desktop.window_state import get_active_window
        win = get_active_window()
        app = win.get("app") or None
        title = win.get("title") or None
    except Exception:
        pass

    try:
        from blender_bridge.state_writer import read as _sr_read
        bs = _sr_read()
        vision = bs.get("vision", {})
        if vision.get("active") and vision.get("description"):
            vision_text = vision["description"]
    except Exception:
        pass

    # WO-025: spatial sensor stub — active only when ELO_SPATIAL_SENSOR=1
    spatial: SpatialFrame | None = None
    if os.environ.get("ELO_SPATIAL_SENSOR", "0") == "1":
        spatial = _stub_spatial_frame()
        _emit_spatial_trace(spatial)

    return perceive(
        vision_text=vision_text,
        window_app=app,
        window_title=title,
        spatial_data=spatial,
    )
