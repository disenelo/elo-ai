"""
faculties/learning/faculty.py — the Learning Faculty (ADR-Exec-005 D6).

David 2026-08-21: "LOOP-7 — 'does a lesson change a future decision?' why is this still there?"

ADR-Exec-005 D6, ratified David L3 2026-08-06, names this component exactly:

    "a Learning Faculty — a faculty the Executive ASKS, like any other ... never inside the
     Executive. It runs simulations, learns policies, evaluates rewards, stores policies,
     and reports confidence."

D2 — position: Execute -> Verify -> Outcome -> Reflect -> Learn -> Memory. AFTER verify.
D4 — may change: action preferences - exploration weighting - confidence - planning heuristics
                 - curiosity thresholds.
     may NEVER change: memory truth - verified observations - Executive Authority - speech
                       verification.
D5 — "Identity is immutable; policies adapt, skills improve, preferences evolve, truth never
      changes."

🔴 DAVID 2026-08-21: "Learns and asses not adopts, wants to learn more, and there is a reason to why"

So this faculty ASSESSES. It does not hand the Executive a conclusion to adopt — it weighs the
lesson AGAINST THE PRESENT SITUATION and reports:
  - does it FIT here (and a lesson that does not fit is allowed to LOSE),
  - how confident,
  - 🔴 THE REASON — the why travels with the lesson; a preference with no traceable reason is a bias,
  - and when it only half-fits: CURIOSITY, not compliance (ADR-Exec-005 D4 "curiosity thresholds").

It ADVISES. It does not decide, does not write into the Executive, does not touch truth or speech.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
import os
import time

_CURIOSITY_Q_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "curiosity_questions.jsonl",
)

_log = logging.getLogger(__name__)

# The 9 CAL actions. FROZEN (FREEZE_V1_LOCK §5). This faculty may weight them; it may never
# add, remove or rename one.
_CAL_ACTIONS = ("answer", "build", "connect", "celebrate", "reflect",
                "ground", "challenge", "witness", "silence")


@dataclass
class LearningAdvice:
    """An ASSESSMENT, not a conclusion. David: "learns and asses not adopts"."""
    preferences:  dict = field(default_factory=dict)  # action -> weight delta, D4 scope only
    confidence:   float = 0.0                          # how well the lesson fits THIS situation
    lesson_ids:   list = field(default_factory=list)   # traceable to the lessons that produced it
    reasons:      list = field(default_factory=list)   # 🔴 the WHY, per lesson — never a bare weight
    curiosity:    float = 0.0                          # D4 curiosity threshold — half-fit raises this
    wants_to_know: str = ""                            # what would settle it, when he is unsure
    fit:          str = "none"                         # "fits" | "partial" | "conflicts" | "none"
    rationale:    str = ""
    consulted:    bool = False

    def as_dict(self) -> dict:
        return {"preferences": dict(self.preferences), "confidence": round(self.confidence, 3),
                "lesson_ids": list(self.lesson_ids), "reasons": list(self.reasons),
                "curiosity": round(self.curiosity, 3), "wants_to_know": self.wants_to_know,
                "fit": self.fit, "rationale": self.rationale, "consulted": self.consulted}


def _evidence_is_verified(lesson: dict) -> bool:
    """ADR-Exec-005 D1 — 'Language alone is never evidence.'

    Only a lesson traceable to an EXECUTED ACTION with a VERIFIED CONSEQUENCE may influence
    policy. Mirrors the gate already built in build_executive_context (card 0075) so the two
    cannot diverge; a lesson rejected there must be rejected here.
    """
    for ev in (lesson.get("evidence") or []):
        if not isinstance(ev, dict):   # pre-v1 ledger has string entries — skip silently (card 0082 F-4)
            continue
        if not ev.get("verified"):
            continue
        sid = str(ev.get("session_id") or "").strip()
        if not sid or sid.isdigit():      # pure-numeric session ids were process ids, not sessions
            continue
        if not (ev.get("action") or ev.get("outcome")):   # must name a real executed action/outcome
            continue
        return True
    return False


def _fit(lesson: dict, context: dict) -> tuple[str, float]:
    """Does this lesson fit THIS situation? A lesson that does not fit is allowed to lose.

    David: "learns and asses not adopts". So the lesson is weighed against the present
    moment, not applied because it exists.
    """
    ctx_intent = str((context or {}).get("intent") or "").lower()
    ctx_thread = str((context or {}).get("focal_thread") or "").lower()
    scope      = str(lesson.get("scope") or "").lower()
    applies    = [str(x).lower() for x in (lesson.get("applies_when") or [])]

    if applies:
        hits = sum(1 for a in applies if a and (a in ctx_intent or a in ctx_thread))
        if hits == len(applies):
            return "fits", 1.0
        if hits:
            return "partial", hits / len(applies)
        return "conflicts", 0.0
    if scope and (scope in ctx_intent or scope in ctx_thread):
        return "fits", 1.0
    # A lesson with no stated conditions cannot claim to fit — it can only be a partial signal.
    return "partial", 0.5


def consult(lessons: list | None,
            candidate_action: str = "",
            context: dict | None = None) -> LearningAdvice:
    """The Executive ASKS. This is the entire public surface.

    Returns advice about ACTION PREFERENCE only (D4). Never returns truth, never returns
    speech permission, never returns an instruction to act.
    """
    advice = LearningAdvice(consulted=True)
    rows = [l for l in (lessons or []) if isinstance(l, dict)]
    if not rows:
        advice.rationale = "no lessons available"
        return advice

    usable = [l for l in rows if _evidence_is_verified(l)]
    if not usable:
        advice.rationale = f"{len(rows)} lesson(s) recalled, 0 clear ADR-Exec-005 D1 (verified consequence)"
        advice.curiosity = 0.3
        advice.wants_to_know = "what actually happened — none of these lessons name a verified outcome"
        return advice

    prefs: dict = {}
    ids: list = []
    reasons: list = []
    fits: list = []
    for l in usable:
        fit, weight = _fit(l, context)
        fits.append(fit)
        if fit == "conflicts":
            # 🔴 The lesson LOSES here. It does not get to push. But not fitting is
            # interesting — it raises curiosity rather than being silently dropped.
            advice.curiosity = max(advice.curiosity, 0.6)
            reasons.append({"lesson_id": l.get("lesson_id") or l.get("id"),
                            "why": l.get("statement") or "",
                            "fit": "conflicts",
                            "note": "learned elsewhere; does not match this situation"})
            continue

        strength = float(l.get("strength") or 0.5) * weight
        pref  = str(l.get("prefers_action") or "").strip().lower()
        avoid = str(l.get("avoids_action") or "").strip().lower()
        if pref in _CAL_ACTIONS:
            prefs[pref] = prefs.get(pref, 0.0) + strength
        if avoid in _CAL_ACTIONS:
            prefs[avoid] = prefs.get(avoid, 0.0) - strength

        lid = l.get("lesson_id") or l.get("id")
        if lid:
            ids.append(lid)
        # 🔴 THE REASON TRAVELS WITH THE LESSON. A weight with no why is a bias.
        reasons.append({"lesson_id": lid,
                        "why": l.get("statement") or "(lesson carries no stated reason)",
                        "fit": fit,
                        "from": (l.get("evidence") or [{}])[0].get("outcome") or "a verified outcome"})
        if fit == "partial":
            advice.curiosity = max(advice.curiosity, 0.5 * (1.0 - weight))

    advice.reasons = reasons
    advice.lesson_ids = ids
    advice.fit = ("fits" if "fits" in fits else "partial" if "partial" in fits
                  else "conflicts" if "conflicts" in fits else "none")

    if not prefs:
        advice.rationale = (f"{len(usable)} verified lesson(s); none applies here"
                            if advice.fit == "conflicts" else
                            f"{len(usable)} verified lesson(s), none carries an action preference")
        advice.wants_to_know = "whether the earlier outcome would repeat in this situation"
        return advice

    advice.preferences = prefs
    advice.confidence = min(1.0, sum(abs(v) for v in prefs.values()) / max(1, len(prefs)))
    top = max(prefs.items(), key=lambda kv: kv[1])
    why = next((r["why"] for r in reasons if r.get("fit") != "conflicts"), "")
    advice.rationale = f"prefers '{top[0]}' — {why}" if why else f"prefers '{top[0]}'"

    # 🔴 WANTS TO LEARN MORE. Partial fit or thin confidence is curiosity, not compliance.
    if advice.curiosity >= 0.4 or advice.confidence < 0.6:
        advice.wants_to_know = (f"whether '{top[0]}' is right here, or whether this situation "
                                f"differs from the one the lesson came from")

    # WO-CURIOSITY-QSTORE-001: persist wants_to_know so it survives the turn.
    _persist_curiosity_question(advice)
    return advice


def _persist_curiosity_question(advice: "LearningAdvice") -> None:
    """WO-CURIOSITY-QSTORE-001: append wants_to_know to data/curiosity_questions.jsonl."""
    if not advice.wants_to_know:
        return
    try:
        record = {
            "_ts":          time.time(),
            "wants_to_know": advice.wants_to_know,
            "fit":           advice.fit,
            "confidence":    round(advice.confidence, 3),
            "curiosity":     round(advice.curiosity, 3),
            "lesson_ids":    list(advice.lesson_ids),
        }
        os.makedirs(os.path.dirname(_CURIOSITY_Q_PATH), exist_ok=True)
        with open(_CURIOSITY_Q_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # fail quietly — never blocks advice delivery


# ── WO-CURIOSITY-QSTORE-READ-001: read path ──────────────────────────────────

def _load_curiosity_questions() -> list[dict]:
    """Read all records from curiosity_questions.jsonl. Missing file = empty list."""
    rows: list[dict] = []
    if not os.path.exists(_CURIOSITY_Q_PATH):
        return rows
    try:
        with open(_CURIOSITY_Q_PATH, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return rows


def _open_curiosity_questions(rows: list[dict]) -> list[dict]:
    """
    Return only "open" questions.

    A question is closed when a later record with `resolved_wants_to_know` matching
    its `wants_to_know` text exists. Records without a `wants_to_know` key are
    resolution tombstones — skip them for the question list.
    """
    resolved: set[str] = set()
    for r in rows:
        wtk = r.get("resolved_wants_to_know", "")
        if wtk:
            resolved.add(wtk.strip().lower())

    open_qs: list[dict] = []
    for r in rows:
        wtk = r.get("wants_to_know", "")
        if not wtk:
            continue
        if wtk.strip().lower() in resolved:
            continue
        open_qs.append(r)
    return open_qs


def _match_curiosity_question(question: dict, turn_text: str) -> bool:
    """
    True if the question is relevant to turn_text.

    Tokenises both the `wants_to_know` text and `turn_text` to lower-case words,
    then checks for at least 2 overlapping meaningful tokens (len >= 4, ignoring
    stopwords).  An empty turn_text always returns False.
    """
    if not turn_text:
        return False
    _STOP = frozenset({
        "about", "after", "also", "been", "from", "have", "here", "into",
        "just", "like", "make", "more", "over", "some", "that", "their",
        "them", "then", "there", "they", "this", "what", "when", "where",
        "whether", "which", "with", "would", "your", "the", "and", "for",
        "are", "but", "not", "all", "was", "were", "will", "does",
    })
    def _tokens(text: str) -> set[str]:
        # Punctuation is stripped from the edges of each word. Without this,
        # a stored question reading "whether 'challenge' is right here," had
        # the tokens "'challenge'" and "here," — so a turn saying challenge
        # could not match the question ABOUT challenge. Quoting is exactly
        # what a writer does to the term a question is about, which made the
        # most distinctive token the systematically unmatchable one.
        import string as _str
        return {
            w for w in (t.strip(_str.punctuation) for t in text.lower().split())
            if len(w) >= 4 and w not in _STOP
        }

    q_tokens = _tokens(question.get("wants_to_know", ""))
    t_tokens  = _tokens(turn_text)
    return len(q_tokens & t_tokens) >= 2


def curiosity_questions_prompt_block(turn_text: str) -> str:
    """
    WO-CURIOSITY-QSTORE-READ-001: surface unanswered curiosity questions relevant
    to the current turn as a prompt block.

    Returns a string like:
      [CURIOSITY: You have an unanswered question about X. This turn may be relevant.]
      [CURIOSITY: You wondered whether Y...]

    Returns "" when no relevant open questions exist or on any error.
    """
    try:
        rows = _load_curiosity_questions()
        open_qs = _open_curiosity_questions(rows)
        # Sort oldest first; surface oldest 1–2 that match this turn.
        open_qs.sort(key=lambda r: float(r.get("_ts", 0)))
        # De-duplicated by text before slicing. The live store holds 50 rows
        # and 2 distinct questions, so an oldest-first [:2] could fill both
        # slots with the SAME text — eLo asking himself one thing twice in a
        # single prompt.
        matching = []
        _seen_q: set[str] = set()
        for q in open_qs:
            text = str(q.get("wants_to_know", "") or "").strip()
            key = text.lower()
            if not text or key in _seen_q:
                continue
            if _match_curiosity_question(q, turn_text):
                _seen_q.add(key)
                matching.append(q)
            if len(matching) == 2:
                break
        if not matching:
            return ""
        lines = [
            f"[CURIOSITY: You have an unanswered question: {q['wants_to_know'].rstrip('.')}."
            f" This turn may be relevant.]"
            for q in matching
        ]
        return "\n".join(lines)
    except Exception:
        return ""


def resolve_curiosity_question(wants_to_know: str) -> None:
    """
    WO-CURIOSITY-QSTORE-READ-001: mark a curiosity question as answered by
    appending a resolution tombstone to the jsonl.

    Does nothing if the question isn't found or on any error.
    """
    if not wants_to_know:
        return
    try:
        tombstone = {
            "_ts":                   time.time(),
            "resolved_wants_to_know": wants_to_know.strip(),
        }
        os.makedirs(os.path.dirname(_CURIOSITY_Q_PATH), exist_ok=True)
        with open(_CURIOSITY_Q_PATH, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(tombstone, ensure_ascii=False) + "\n")
    except Exception:
        pass
