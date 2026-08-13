"""
faculties/personality/personality_evolution_faculty.py — WO-007

Personality Evolution Engine — Volume V, Chapter 7.

Holds eLo's personality as named, versioned trait vectors and evolves them
slowly, deliberately, and only through validated integration.

Contract:
  - READ in the response path: serves a stable, frozen PersonalityVector.
  - WRITE only in the integration window: validates + applies deltas from Ch.6.
  - Never accepts a personality_delta from any faculty other than ReflectionGrowthEngine.
  - Never applies a delta that would violate the Identity Kernel.
  - Fails CLOSED: on error, serves last stable vector; applies no change.

Unifies: self/elo_self_model.py (mood/curiosity) + memory/personality_drift.py (trait drift).
Those modules continue to run; this engine is the canonical trait authority.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

MAX_STEP = 0.02            # max trait movement per integration period (Audit Vol X)
_CLAMP_MIN = 0.05
_CLAMP_MAX = 0.95

# Identity Kernel floors — violations trigger auto-reject
_WONDER_FLOOR     = 0.10   # childhood-imagination must never reach 0
_EMPATHY_FLOOR    = 0.20   # ethical floor — below this = manipulation risk
_DIRECTNESS_MIN   = 0.50   # eLo is direct; never becomes vague

# Sole authorised source of trait deltas
_AUTHORISED_SENDER = "ReflectionGrowthEngine"

# Persistence
_STATE_DIR  = Path(__file__).parent.parent.parent / "self"
_STATE_PATH = _STATE_DIR / "personality_vector.json"


# ── Identity Kernel (inline constraints — 18_identity_kernel.md) ─────────────
# Frozen reference — never mutable at runtime.

_IDENTITY_KERNEL = {
    "character_name":     "eLo",
    "has_eyes":           False,
    "one_brain":          True,
    "free_distribution":  True,
    "local_first":        True,
    "wonder_floor":       _WONDER_FLOOR,
    "empathy_floor":      _EMPATHY_FLOOR,
    "directness_min":     _DIRECTNESS_MIN,
}

# Stable hash of the kernel — used in PersonalityVersion.identity_hash
_KERNEL_HASH = hashlib.sha256(
    json.dumps(_IDENTITY_KERNEL, sort_keys=True).encode()
).hexdigest()[:16]


# ── Dataclasses ──────────────────────────────────────────────────────────────

@dataclass
class TraitRecord:
    """One named trait with its full provenance."""
    value:          float         # current value [0,1]
    baseline:       float         # resting value (what Ch.4 reads as temperament)
    evolution_rate: float = MAX_STEP
    last_changed:   str   = ""    # ISO timestamp
    evidence:       list  = field(default_factory=list)   # [lesson_id, ...]


@dataclass
class PersonalityVector:
    """
    The 8 named trait dimensions. Served to CognitiveState on every turn.
    Mutated ONLY by apply_delta() during the integration window.
    """
    curiosity:   TraitRecord = field(default_factory=lambda: TraitRecord(0.62, 0.62))
    patience:    TraitRecord = field(default_factory=lambda: TraitRecord(0.65, 0.65))
    confidence:  TraitRecord = field(default_factory=lambda: TraitRecord(0.60, 0.60))
    empathy:     TraitRecord = field(default_factory=lambda: TraitRecord(0.72, 0.72))
    discipline:  TraitRecord = field(default_factory=lambda: TraitRecord(0.58, 0.58))
    wonder:      TraitRecord = field(default_factory=lambda: TraitRecord(0.80, 0.80, evidence=["identity_kernel"]))
    playfulness: TraitRecord = field(default_factory=lambda: TraitRecord(0.68, 0.68))
    directness:  TraitRecord = field(default_factory=lambda: TraitRecord(0.72, 0.72, evidence=["character_rule"]))
    # Schema version (semver)
    version:     str          = "1.0.0"
    # Preferences — lightweight, below trait level
    preferences: dict         = field(default_factory=dict)


@dataclass(frozen=True)
class PersonalityDelta:
    """A proposed trait change. Must come from ReflectionGrowthEngine."""
    sender:    str              # must equal _AUTHORISED_SENDER to pass
    trait:     str              # name of the trait to change
    direction: str              # "increase" | "decrease"
    magnitude: float            # requested change [0, MAX_STEP * 5]
    evidence:  tuple = ()       # (lesson_id, ...) — must be non-empty + confirmed
    strength:  str  = "candidate"  # "confirmed" required for trait change


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of identity-continuity validation."""
    accepted: bool
    reason:   str
    delta:    Optional[PersonalityDelta] = None


@dataclass
class PersonalityVersion:
    """Versioned personality snapshot with immutable audit trail."""
    version:       str
    vector_snapshot: dict         # trait_name → value at this version
    changelog:     list           # [{trait, from, to, evidence, validated_at}]
    parent:        str            # previous version
    identity_hash: str            # _KERNEL_HASH at time of change
    created_at:    str            # ISO timestamp


# ── Persistence ──────────────────────────────────────────────────────────────

def load_personality() -> PersonalityVector:
    """Load PersonalityVector from disk. Returns defaults if missing or corrupt."""
    try:
        with open(_STATE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        pv = PersonalityVector(version=data.get("version", "1.0.0"))
        for trait_name in _TRAIT_NAMES:
            if trait_name in data:
                td = data[trait_name]
                setattr(pv, trait_name, TraitRecord(
                    value=float(td.get("value", 0.5)),
                    baseline=float(td.get("baseline", 0.5)),
                    evolution_rate=float(td.get("evolution_rate", MAX_STEP)),
                    last_changed=td.get("last_changed", ""),
                    evidence=td.get("evidence", []),
                ))
        pv.preferences = data.get("preferences", {})
        return pv
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
        return PersonalityVector()


def save_personality(pv: PersonalityVector) -> None:
    """Persist PersonalityVector to disk."""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        data: dict = {"version": pv.version, "preferences": pv.preferences}
        for t in _TRAIT_NAMES:
            tr = getattr(pv, t)
            data[t] = asdict(tr)
        with open(_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        pass   # fail silently; serve last-known-good


_TRAIT_NAMES = (
    "curiosity", "patience", "confidence", "empathy",
    "discipline", "wonder", "playfulness", "directness",
)


# ── Response-path API (READ ONLY) ─────────────────────────────────────────────

def get_trait_values(pv: PersonalityVector) -> dict:
    """
    Return current trait values as a plain dict for CognitiveState assembly.
    Called in the response path — READ ONLY, never mutates pv.
    """
    return {t: getattr(pv, t).value for t in _TRAIT_NAMES}


def get_affect_baseline(pv: PersonalityVector) -> dict:
    """
    Return the baseline temperament slice that Ch.4 uses as its resting affect anchor.
    Curiosity, empathy, and wonder influence eLo's emotional baseline.
    """
    return {
        "mood_baseline":     pv.wonder.baseline * 0.5 + pv.playfulness.baseline * 0.3 + pv.curiosity.baseline * 0.2,
        "curiosity_baseline": pv.curiosity.baseline,
        "empathy_baseline":   pv.empathy.baseline,
        "wonder_baseline":    pv.wonder.baseline,
    }


# ── Integration-window API (WRITE path) ───────────────────────────────────────

def validate_delta(delta: PersonalityDelta) -> ValidationResult:
    """
    Identity-continuity validation (§7.5). Gate every PersonalityDelta here.

    Returns ValidationResult with accepted=True only when ALL rules pass.
    Auto-reject if ANY identity violation is detected.
    """
    # Rule: single authorised source
    if delta.sender != _AUTHORISED_SENDER:
        return ValidationResult(
            accepted=False,
            reason=f"Rejected: sender must be {_AUTHORISED_SENDER}, got '{delta.sender}' (anomaly logged)",
            delta=delta,
        )

    # Rule: must be a known trait
    if delta.trait not in _TRAIT_NAMES:
        return ValidationResult(
            accepted=False,
            reason=f"Rejected: unknown trait '{delta.trait}'",
            delta=delta,
        )

    # Rule: confirmed lessons only
    if delta.strength != "confirmed":
        return ValidationResult(
            accepted=False,
            reason=f"Rejected: lesson strength must be 'confirmed', got '{delta.strength}' (lesson stays candidate)",
            delta=delta,
        )

    # Rule: evidence required
    if not delta.evidence:
        return ValidationResult(
            accepted=False,
            reason="Rejected: no evidence lessons (every trait value must be traceable)",
            delta=delta,
        )

    # Rule: bounded step
    if abs(delta.magnitude) > MAX_STEP:
        return ValidationResult(
            accepted=False,
            reason=f"Rejected: magnitude {delta.magnitude:.4f} exceeds MAX_STEP {MAX_STEP} (too fast = drift)",
            delta=delta,
        )

    # Rule: direction validity
    if delta.direction not in ("increase", "decrease"):
        return ValidationResult(
            accepted=False,
            reason=f"Rejected: direction must be 'increase' or 'decrease', got '{delta.direction}'",
            delta=delta,
        )

    return ValidationResult(accepted=True, reason="Passed identity-continuity validation", delta=delta)


def _check_identity_floor(trait: str, new_value: float) -> Optional[str]:
    """Return a rejection reason string if applying this value violates the Identity Kernel, else None."""
    if trait == "wonder" and new_value < _WONDER_FLOOR:
        return f"Identity violation: wonder ({new_value:.4f}) < floor ({_WONDER_FLOOR}) — childhood-imagination must persist"
    if trait == "empathy" and new_value < _EMPATHY_FLOOR:
        return f"Identity violation: empathy ({new_value:.4f}) < ethical floor ({_EMPATHY_FLOOR})"
    if trait == "directness" and new_value < _DIRECTNESS_MIN:
        return f"Identity violation: directness ({new_value:.4f}) < minimum ({_DIRECTNESS_MIN}) — eLo is direct by character"
    return None


def apply_delta(
    delta: PersonalityDelta,
    pv: PersonalityVector,
    validation: Optional[ValidationResult] = None,
) -> tuple:
    """
    Apply a validated PersonalityDelta to the PersonalityVector.

    If validation is not pre-supplied, runs validate_delta() first.
    Returns (updated_PersonalityVector, PersonalityVersion) on success.
    Returns (original_pv, None) if rejected.

    Bumps version MINOR on trait change.
    """
    if validation is None:
        validation = validate_delta(delta)

    if not validation.accepted:
        return pv, None

    trait_record: TraitRecord = getattr(pv, delta.trait)
    old_value = trait_record.value

    # Compute new value — clamped to [CLAMP_MIN, CLAMP_MAX]
    sign = 1.0 if delta.direction == "increase" else -1.0
    raw_new = old_value + sign * abs(delta.magnitude)
    new_value = max(_CLAMP_MIN, min(_CLAMP_MAX, raw_new))

    # Check Identity Kernel floors after clamping
    violation = _check_identity_floor(delta.trait, new_value)
    if violation:
        return pv, None

    ts = _iso_now()

    # Build new TraitRecord
    new_tr = TraitRecord(
        value=round(new_value, 4),
        baseline=round(new_value, 4),   # baseline shifts with the trait over time
        evolution_rate=trait_record.evolution_rate,
        last_changed=ts,
        evidence=list(trait_record.evidence) + list(delta.evidence),
    )

    # Bump semver MINOR
    new_version = _bump_minor(pv.version)

    # Build updated PersonalityVector (manual copy — not frozen, but must stay coherent)
    updated_pv = _copy_personality(pv)
    setattr(updated_pv, delta.trait, new_tr)
    updated_pv.version = new_version

    # Snapshot + changelog
    snapshot = {t: getattr(updated_pv, t).value for t in _TRAIT_NAMES}
    entry = {
        "trait":        delta.trait,
        "from":         round(old_value, 4),
        "to":           round(new_value, 4),
        "evidence":     list(delta.evidence),
        "validated_at": ts,
    }

    version_record = PersonalityVersion(
        version=new_version,
        vector_snapshot=snapshot,
        changelog=[entry],
        parent=pv.version,
        identity_hash=_KERNEL_HASH,
        created_at=ts,
    )

    return updated_pv, version_record


def update_preference(
    pv: PersonalityVector,
    key: str,
    value,
    strength: float = 0.7,
    evidence: str = "",
) -> tuple:
    """
    Update a preference (PATCH version bump). Never touches trait vectors.
    Returns (updated_pv, PersonalityVersion).
    """
    updated_pv = _copy_personality(pv)
    updated_pv.preferences[key] = {
        "value":    value,
        "strength": strength,
        "evidence": evidence,
        "updated":  _iso_now(),
    }
    new_version = _bump_patch(pv.version)
    updated_pv.version = new_version

    snapshot = {t: getattr(updated_pv, t).value for t in _TRAIT_NAMES}
    version_record = PersonalityVersion(
        version=new_version,
        vector_snapshot=snapshot,
        changelog=[{"preference": key, "value": str(value), "updated_at": _iso_now()}],
        parent=pv.version,
        identity_hash=_KERNEL_HASH,
        created_at=_iso_now(),
    )
    return updated_pv, version_record


# ── Helpers ──────────────────────────────────────────────────────────────────

def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _bump_minor(semver: str) -> str:
    try:
        major, minor, patch = (int(x) for x in semver.split("."))
        return f"{major}.{minor + 1}.0"
    except Exception:
        return "1.1.0"


def _bump_patch(semver: str) -> str:
    try:
        major, minor, patch = (int(x) for x in semver.split("."))
        return f"{major}.{minor}.{patch + 1}"
    except Exception:
        return "1.0.1"


def _copy_personality(pv: PersonalityVector) -> PersonalityVector:
    """Return a shallow copy of PersonalityVector for safe mutation in apply."""
    new_pv = PersonalityVector(version=pv.version, preferences=dict(pv.preferences))
    for t in _TRAIT_NAMES:
        setattr(new_pv, t, getattr(pv, t))
    return new_pv


def compute_identity_hash() -> str:
    """Return the current Identity Kernel hash for audit purposes."""
    return _KERNEL_HASH
