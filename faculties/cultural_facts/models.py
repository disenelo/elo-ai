"""faculties/cultural_facts/models.py — CulturalFact data model."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class CulturalFact:
    id:            str
    person:        str        # person or group (e.g. "Onesimus", "Dogon people")
    fact:          str        # full reference text — accurate, sourced
    delivery:      str        # eLo-voice version — spoken directly, no preamble
    group:         str        # see GROUP_WEIGHTS in faculty.py
    sub_tradition: str        # e.g. diaspora_modern, ethiopian, west_african_empires
    category:      str        # inventor|scientist|empire|medicine|cultural|folklore|mathematics|astronomy
    era:           str        # ancient|medieval|colonial|modern
    tags:          List[str]  = field(default_factory=list)
