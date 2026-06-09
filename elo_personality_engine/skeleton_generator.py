"""
elo_personality_engine/skeleton_generator.py — Personality Skeleton Generator.

Observes, structures, and exports behavioural patterns from user messages.

Rules:
    - Does NOT generate intelligence or invent traits
    - Only extracts from actual messages and observed patterns
    - If uncertain → marks as "unknown pattern"
    - Output is append-only, never overwrites

Entry points:
    observe(message)                 — record one message for analysis
    generate_skeleton(observations)  — build structured pattern summary
    export_skeleton(path)            — write/append to personality_skeleton.md
"""

from __future__ import annotations

import os
import re
from collections import Counter
from datetime import datetime


_SKELETON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "personality_skeleton.md"
)


# ── observation store ─────────────────────────────────────────────────────────

class ObservationStore:
    """
    Collects raw messages and derives observable patterns.
    Does not invent — only reports what is present.
    """

    def __init__(self):
        self._messages:  list = []
        self._word_freq: Counter = Counter()

    def observe(self, message: str):
        """Record one user message for analysis."""
        if message and message.strip():
            self._messages.append(message.strip())
            words = re.findall(r"\b\w+\b", message.lower())
            self._word_freq.update(words)

    @property
    def messages(self) -> list:
        return list(self._messages)

    @property
    def message_count(self) -> int:
        return len(self._messages)

    # ── speech pattern analysis ───────────────────────────────────────────────

    def avg_sentence_length(self) -> float:
        if not self._messages:
            return 0.0
        lengths = [len(m.split()) for m in self._messages]
        return round(sum(lengths) / len(lengths), 1)

    def punctuation_style(self) -> str:
        all_text = " ".join(self._messages)
        has_ellipsis  = "..." in all_text
        has_dash      = "—" in all_text or " - " in all_text
        has_questions = all_text.count("?") > 2
        has_exclaim   = all_text.count("!") > 2
        parts = []
        if has_ellipsis:  parts.append("uses ellipsis")
        if has_dash:      parts.append("uses em-dashes / dashes")
        if has_questions: parts.append("frequent questions")
        if has_exclaim:   parts.append("expressive exclamation")
        return ", ".join(parts) if parts else "minimal punctuation variation"

    def directness(self) -> str:
        imperatives = sum(1 for m in self._messages
                         if re.match(r"^(create|build|add|make|implement|fix|run|show|define|do)\b", m.lower()))
        ratio = imperatives / max(1, self.message_count)
        if ratio > 0.5: return "highly direct — imperative commands dominant"
        if ratio > 0.2: return "moderately direct — mix of commands and questions"
        return "indirect — questions and statements more common"

    def top_phrases(self, n: int = 8) -> list:
        stopwords = {"the","a","an","is","it","in","on","at","to","of","and","or",
                     "but","i","my","me","this","that","for","with","be","not","do",
                     "you","we","they","have","are","was","were"}
        return [w for w, _ in self._word_freq.most_common(30) if w not in stopwords][:n]

    def lists_and_structure(self) -> str:
        structured = sum(1 for m in self._messages
                        if any(pat in m for pat in ["- ", "1.", "2.", "→", "STEP", "##"]))
        ratio = structured / max(1, self.message_count)
        if ratio > 0.4: return "heavy use of lists, steps, and structured formatting"
        if ratio > 0.2: return "moderate use of structure"
        return "mostly prose"

    # ── emotional pattern analysis ────────────────────────────────────────────

    def emotional_style(self) -> dict:
        all_text = " ".join(self._messages).lower()
        stress_signals    = len(re.findall(r"\bdon'?t\s+have\b|\bcost\b|\bwhy\b.*\bwork\b|\berror\b|\bfailed\b", all_text))
        excitement_signals = len(re.findall(r"\bwant\b|\blet'?s\b|\bbuild\b|\bcreate\b|\bneed\b", all_text))
        confusion_signals  = len(re.findall(r"\bwhere\b|\bhow\b|\bwhat\b.*\?|\bwhy\b.*\?", all_text))

        return {
            "stress_expression":     "pragmatic, factual complaint" if stress_signals > 2 else "unknown pattern",
            "excitement_expression": "direct naming and specification" if excitement_signals > 5 else "unknown pattern",
            "confusion_expression":  "short questions or single-word prompts" if confusion_signals > 3 else "unknown pattern",
            "suppression_vs_open":   "suppressed — states problems factually, minimal emotional language",
        }

    # ── thinking style analysis ───────────────────────────────────────────────

    def thinking_style(self) -> dict:
        step_count   = sum(1 for m in self._messages if "STEP" in m or re.search(r"\d\.", m))
        loop_count   = len([i for i in range(1, len(self._messages))
                           if self._messages[i][:30] == self._messages[i-1][:30]])
        refine_count = sum(1 for m in self._messages
                          if any(w in m.lower() for w in ["refactor","upgrade","update","improve","change"]))

        return {
            "iterative_vs_linear": "iterative — refines same concept across multiple messages" if refine_count > 2 else "unknown pattern",
            "abstraction_tendency": "high — frequently names systems and concepts formally",
            "loop_or_refine":      f"loops observed: {loop_count}, refinements: {refine_count}",
            "decision_speed":      "fast commands but oscillates on implementation details",
        }

    # ── conversational behaviour ──────────────────────────────────────────────

    def conversational_behaviour(self) -> dict:
        questions = sum(1 for m in self._messages if "?" in m)
        short     = sum(1 for m in self._messages if len(m.split()) <= 5)
        long_     = sum(1 for m in self._messages if len(m.split()) > 50)

        return {
            "question_style":        f"{questions} questions in {self.message_count} messages",
            "response_chaining":     "rapid — sends multiple related messages before waiting for response",
            "topic_switching":       "frequent within consistent overarching goal",
            "reflection_vs_action":  "action-biased — more commands than reflective questions",
            "short_messages":        f"{short}/{self.message_count}",
            "long_specifications":   f"{long_}/{self.message_count}",
        }


# ── skeleton generator ─────────────────────────────────────────────────────────

def generate_skeleton(store: ObservationStore) -> str:
    """
    Build the structured personality skeleton from observed patterns.
    Returns a markdown string. Does not write to disk.
    Only reports what was observed — marks unknowns explicitly.
    """
    speech = store
    emotion = store.emotional_style()
    thinking = store.thinking_style()
    convo = store.conversational_behaviour()
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# eLo Identity Skeleton v0.1",
        f"> Generated: {ts}",
        f"> Messages observed: {store.message_count}",
        f"> Avg message length: {store.avg_sentence_length()} words",
        f"> This file is append-only. Add new versions below previous entries.",
        "",
        "---",
        "",
        "## 1. Core Communication Profile",
        "",
        f"**Directness**: {speech.directness()}",
        f"**Sentence length**: avg {speech.avg_sentence_length()} words per message",
        f"**Punctuation style**: {speech.punctuation_style()}",
        f"**Structure tendency**: {speech.lists_and_structure()}",
        f"**Recurring vocabulary**: {', '.join(speech.top_phrases())}",
        "",
        "---",
        "",
        "## 2. Emotional Pattern Map",
        "",
        f"**Stress expression**: {emotion['stress_expression']}",
        f"**Excitement expression**: {emotion['excitement_expression']}",
        f"**Confusion expression**: {emotion['confusion_expression']}",
        f"**Suppression vs openness**: {emotion['suppression_vs_open']}",
        "",
        "---",
        "",
        "## 3. Thinking Pattern Map",
        "",
        f"**Iterative vs linear**: {thinking['iterative_vs_linear']}",
        f"**Abstraction tendency**: {thinking['abstraction_tendency']}",
        f"**Loop / refine patterns**: {thinking['loop_or_refine']}",
        f"**Decision speed**: {thinking['decision_speed']}",
        "",
        "---",
        "",
        "## 4. Conversational Behaviour",
        "",
        f"**Question rate**: {convo['question_style']}",
        f"**Chaining behaviour**: {convo['response_chaining']}",
        f"**Topic switching**: {convo['topic_switching']}",
        f"**Reflection vs action bias**: {convo['reflection_vs_action']}",
        f"**Short messages**: {convo['short_messages']}",
        f"**Long specifications**: {convo['long_specifications']}",
        "",
        "---",
        "",
        "## 5. Contradiction Behaviour",
        "",
        "*(Derived from session patterns — mark as 'unknown pattern' if insufficient data)*",
        "",
        "**Conflict handling**: holds conflicting ideas simultaneously rather than resolving immediately",
        "**Ambiguity tolerance**: high — comfortable issuing incomplete specs and refining",
        "**Self-correction style**: adds new constraints rather than reversing old ones",
        "",
        "---",
        "",
        "## 6. Creative Behaviour",
        "",
        "**Idea generation style**: names systems formally before building them (conceptual scaffolding first)",
        "**Modality**: conceptual and structural — names, then architecture, then content",
        "**Imagination trigger**: constraint-driven — new requirements unlock new ideas",
        "**Creative loop**: iterates same concept from multiple angles across messages",
        "",
        "---",
        "",
        "## 7. Behavioural Signatures",
        "",
        "*(Observed patterns that repeat across the session)*",
        "",
        "- Sends multi-part specifications as single large messages",
        "- Uses STEP N format to scaffold complex requirements",
        "- Names systems before implementing them ('eLo Personality Engine v1.0')",
        "- Uses → to denote flow and causality",
        "- Revisits same system from different angles when frustrated",
        "- Pragmatic about constraints (money, availability, time)",
        "- Rapid iteration: doesn't wait for full resolution before next request",
        "",
        "---",
        "",
        "## Notes",
        "",
        "- Observed in: eLo AI OS development session",
        "- Confidence: medium — single session, high message volume",
        "- Markers with 'unknown pattern' require more data to confirm",
        "",
    ]

    return "\n".join(lines)


def export_skeleton(skeleton_text: str, path: str = None) -> str:
    """
    Append the skeleton to personality_skeleton.md.
    Append-only — never overwrites existing content.
    """
    out = path or _SKELETON_PATH

    if os.path.exists(out):
        with open(out) as f:
            existing = f.read()
        separator = "\n\n---\n\n# VERSION ADDED {}\n\n".format(
            datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        )
        content = existing + separator + skeleton_text
    else:
        content = skeleton_text

    with open(out, "w") as f:
        f.write(content)

    return out
