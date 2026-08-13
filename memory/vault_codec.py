"""
memory/vault_codec.py — Spot code encoder/decoder for the tiered memory vault.

Three tiers:
    spot    — compact 4-group code  e.g. EO·BL·2607·9
    bits    — binary read           e.g. 1100·1111·0111·1001
    summary — one-sentence human read
    deep    — full compressed memory block

Spot code anatomy:  [PROJECT]·[TYPE]·[YYMM]·[WEIGHT]

PROJECT  (2 chars)
    EO = eLo OS           EG = eLo Game         ER = eLo Robot
    EB = eLo Book         DX = DISENELO cross   DV = David personal
    GN = general

TYPE (2 chars)
    BL = build/make       FX = fix/debug        DC = decision
    LN = learn/insight    CN = connect/creative DS = design
    CV = conversation

YYMM   — 4-digit year+month (e.g. 2607 = July 2026)
WEIGHT — single digit 0-9  (9=core identity, 7+=important, 4-6=useful, 1-3=ephemeral)
"""
from __future__ import annotations

import re
from datetime import datetime

# ── Lookup tables ─────────────────────────────────────────────────────────────

PROJECT_CODES: dict[str, tuple[str, str]] = {
    "EO": ("elo-os",    "1100"),
    "EG": ("elo-game",  "1010"),
    "ER": ("elo-robot", "0110"),
    "EB": ("elo-book",  "0100"),
    "DX": ("disenelo",  "1110"),
    "DV": ("david",     "0010"),
    "GN": ("general",   "0000"),
}

TYPE_CODES: dict[str, tuple[str, str]] = {
    "BL": ("build",        "1111"),
    "FX": ("fix",          "1110"),
    "DC": ("decision",     "1100"),
    "LN": ("learn",        "1010"),
    "CN": ("connect",      "1000"),
    "DS": ("design",       "0110"),
    "CV": ("conversation", "0100"),
}

# Reverse lookups — domain label → project code, type name → type code
_PROJ_FROM_DOMAIN: dict[str, str] = {v[0]: k for k, v in PROJECT_CODES.items()}
_TYPE_FROM_NAME:   dict[str, str] = {v[0]: k for k, v in TYPE_CODES.items()}

_MONTH_BITS: dict[int, str] = {
    1: "0001", 2: "0010", 3: "0011", 4: "0100",
    5: "0101", 6: "0110", 7: "0111", 8: "1000",
    9: "1001", 10: "1010", 11: "1011", 12: "1100",
}


# ── Encode ────────────────────────────────────────────────────────────────────

def encode(
    *,
    project: str,
    memory_type: str,
    date: datetime | None = None,
    weight: int = 5,
) -> dict:
    """
    Produce a spot code + bit string for a memory record.

    Args:
        project     — domain label e.g. "elo-os", "elo-game", "david", "general"
        memory_type — type label e.g. "build", "fix", "decision", "learn"
        date        — defaults to now()
        weight      — 0-9 importance (9=core identity)

    Returns:
        {
            "spot":   "EO·BL·2607·9",
            "bits":   "1100·1111·0111·1001",
            "p_code": "EO",
            "t_code": "BL",
            "yymm":   "2607",
            "weight": 9,
        }
    """
    date   = date or datetime.now()
    p_code = _PROJ_FROM_DOMAIN.get(project, "GN")
    t_code = _TYPE_FROM_NAME.get(memory_type, "CV")
    weight = max(0, min(9, int(weight)))

    yymm        = f"{date.year % 100:02d}{date.month:02d}"
    month_bits  = _MONTH_BITS.get(date.month, "0000")
    weight_bits = f"{weight:04b}"

    return {
        "spot":   f"{p_code}·{t_code}·{yymm}·{weight}",
        "bits":   f"{PROJECT_CODES[p_code][1]}·{TYPE_CODES[t_code][1]}·{month_bits}·{weight_bits}",
        "p_code": p_code,
        "t_code": t_code,
        "yymm":   yymm,
        "weight": weight,
    }


# ── Decode ────────────────────────────────────────────────────────────────────

def decode(spot: str) -> dict:
    """
    Decode a spot code back to human-readable labels.

    Args:
        spot — e.g. "EO·BL·2607·9"

    Returns:
        {
            "project":     "Elo Os",
            "type":        "build",
            "year":        2026,
            "month":       7,
            "month_name":  "July",
            "weight":      9,
            "description": "Elo Os · build · July 2026 · weight 9"
        }

    Raises:
        ValueError — malformed spot code
    """
    parts = [p.strip() for p in spot.split("·")]
    if len(parts) != 4:
        raise ValueError(f"Malformed spot code (need 4 groups): {spot!r}")

    p_code, t_code, yymm, w_str = parts

    if p_code not in PROJECT_CODES:
        raise ValueError(f"Unknown project code: {p_code!r}")
    if t_code not in TYPE_CODES:
        raise ValueError(f"Unknown type code: {t_code!r}")
    if not re.match(r"^\d{4}$", yymm):
        raise ValueError(f"Bad YYMM: {yymm!r}")

    year        = 2000 + int(yymm[:2])
    month       = int(yymm[2:])
    weight      = int(w_str)
    month_name  = datetime(year, month, 1).strftime("%B")
    proj_label  = PROJECT_CODES[p_code][0].replace("-", " ").title()
    type_label  = TYPE_CODES[t_code][0]

    return {
        "project":     proj_label,
        "type":        type_label,
        "year":        year,
        "month":       month,
        "month_name":  month_name,
        "weight":      weight,
        "description": f"{proj_label} · {type_label} · {month_name} {year} · weight {weight}",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def spot_to_filename(spot: str) -> str:
    """'EO·BL·2607·9' → 'EO-BL-2607-9' (safe for filenames)."""
    return spot.replace("·", "-")


def compress_text(text: str, max_chars: int = 1200) -> str:
    """
    Compress memory text — collapse whitespace, truncate at sentence boundary.
    Used for deep records and summary lines.
    """
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    cutoff = text.rfind(".", 0, max_chars)
    if cutoff > max_chars // 2:
        return text[:cutoff + 1]
    return text[:max_chars] + "…"


def weight_label(w: int) -> str:
    if w >= 9: return "core"
    if w >= 7: return "important"
    if w >= 4: return "useful"
    return "ephemeral"


# ── CLI (test / debug) ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json

    test_cases = [
        dict(project="elo-os",   memory_type="build",    weight=9),
        dict(project="elo-game", memory_type="fix",      weight=7),
        dict(project="david",    memory_type="decision", weight=8),
        dict(project="general",  memory_type="learn",    weight=4),
    ]

    for tc in test_cases:
        coded = encode(**tc)
        print(f"Spot: {coded['spot']}   Bits: {coded['bits']}")
        decoded = decode(coded["spot"])
        print(f"  → {decoded['description']}")
        print()
