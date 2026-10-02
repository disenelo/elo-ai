"""
runtime/curiosity_faculty.py — WO-CURIOSITY-001

Re-export of faculties/curiosity/curiosity_faculty.py so that the
capability_registry executor path "runtime.curiosity_faculty" resolves.

Do not add logic here — all implementation lives in the faculties package.
"""
from faculties.curiosity.curiosity_faculty import (  # noqa: F401
    detect_gap,
    form_question,
    prioritise,
    store_question,
    top_question,
    curiosity_prompt_block,
)
