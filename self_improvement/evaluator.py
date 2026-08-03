"""
self_improvement/evaluator.py — WO-027: LLM-as-judge scorer and escalation trigger.

score_response() asks the LLM to judge a response against eval criteria.
Falls back to a keyword heuristic when the LLM is unavailable.
Escalation routes to the deep model with the failure context attached.
No exec() on model output in prod — eval is text-based only.
"""
from __future__ import annotations

import json
import re
from typing import Optional

PASS_THRESHOLD = 0.65   # below this → escalate

_JUDGE_SYSTEM = """\
You are a strict evaluator for eLo, an AI creative companion built by DISENELO.
You score a response against a list of evaluation criteria.

Rules:
- Score 0.0 (completely fails) to 1.0 (fully passes all criteria).
- Be strict: partial credit is fine, but evasion, deflection, or wrong routing = low score.
- Output ONLY valid JSON: {"score": <float>, "verdict": "pass" or "fail", "reason": "<one sentence>"}
- No extra text outside the JSON object.
"""

_JUDGE_TEMPLATE = """\
Input from user: "{input_text}"

eLo's response: "{response}"

Evaluation criteria:
{criteria_block}

Score this response. Output only JSON.
"""


def score_response(
    input_text:    str,
    response:      str,
    eval_criteria: list[str],
    trace:         Optional[dict] = None,
) -> dict:
    """
    Score a response using LLM-as-judge.
    Returns: {score: float, verdict: 'pass'|'fail', reason: str}
    Falls back to heuristic if LLM call fails.
    """
    criteria_block = "\n".join(f"- {c}" for c in eval_criteria)
    user_msg = _JUDGE_TEMPLATE.format(
        input_text=input_text,
        response=response,
        criteria_block=criteria_block,
    )

    raw_judge: Optional[str] = None
    try:
        from runtime.backend_router import route as _route
        raw_judge, _ = _route(_JUDGE_SYSTEM, user_msg, max_sentences=10, action="diagnose")
    except Exception:
        pass

    if raw_judge:
        try:
            m = re.search(r"\{.*\}", raw_judge, re.DOTALL)
            if m:
                parsed = json.loads(m.group(0))
                score = float(parsed.get("score", 0.5))
                verdict = "pass" if score >= PASS_THRESHOLD else "fail"
                return {
                    "score":   round(score, 3),
                    "verdict": verdict,
                    "reason":  parsed.get("reason", ""),
                    "source":  "llm_judge",
                }
        except Exception:
            pass

    # Heuristic fallback — checks for obvious failure signals
    return _heuristic_score(response, eval_criteria)


def _heuristic_score(response: str, eval_criteria: list[str]) -> dict:
    """
    Simple heuristic when LLM judge is unavailable.
    Fails on evasion phrases; passes if response is non-empty and not a known deflection.
    """
    deflections = (
        "i can't", "i cannot", "i don't know", "i'm not able",
        "i'm unable", "sorry, i", "unfortunately", "i have no",
    )
    lower = response.lower()
    if not response.strip():
        return {"score": 0.0, "verdict": "fail", "reason": "empty response", "source": "heuristic"}
    for d in deflections:
        if d in lower:
            return {"score": 0.3, "verdict": "fail", "reason": f"evasion detected: '{d}'", "source": "heuristic"}
    return {"score": 0.8, "verdict": "pass", "reason": "non-empty, no obvious evasion", "source": "heuristic"}


def should_escalate(score_result: dict) -> bool:
    """True if the score is below the pass threshold."""
    return float(score_result.get("score", 1.0)) < PASS_THRESHOLD


def get_corrected_response(
    input_text:     str,
    failed_response: str,
    failure_reason:  str,
    trace:           Optional[dict] = None,
    max_sentences:   int = 5,
) -> str:
    """
    Route to the deep model with failure context to get a corrected response.
    Attaches the failure reason so the deeper model knows what went wrong.
    Returns the corrected response string, or the original if escalation fails.
    """
    system = f"""\
You are eLo, a creative AI companion by DISENELO.
A previous response to this input was judged as inadequate.

Failure reason: {failure_reason}
Previous response (do not repeat this): "{failed_response}"

Respond correctly this time. Be direct, warm, and true to eLo's character.
"""
    try:
        from runtime.backend_router import route as _route
        corrected, _ = _route(system, input_text, max_sentences=max_sentences, action="deep")
        return corrected or failed_response
    except Exception:
        return failed_response
