# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""What was found, in the forms other programs take: FHIR first.

A mention with its assignments becomes a FHIR ``CodeableConcept`` (design, section 8.1): its
``text`` is the wording in the document, and it holds one ``coding`` for every assignment,
whatever code system it comes from.  That is what a CodeableConcept is for: one concept of
the text, coded in every system that knows it.

A CodeableConcept is not a resource.  What it becomes (a condition, an observation, a
medication) is for the program that takes it over, and so is the record of who confirmed it.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from lexcor import Annotation
from lexcor.annotation import CONFIRMED, PERSON, Assigned, Noted


def coding(assigned: Assigned) -> dict[str, Any]:
    """One assignment as a FHIR ``Coding``.  ``userSelected`` is true where a person
    confirmed the assignment or made it."""
    data: dict[str, Any] = {"system": assigned.system}
    if assigned.version:
        data["version"] = assigned.version
    data["code"] = assigned.code
    if assigned.display:
        data["display"] = assigned.display
    if assigned.status == CONFIRMED or assigned.by == PERSON:
        data["userSelected"] = True
    return data


def codeable_concept(noted: Noted, statuses: Iterable[str] = (CONFIRMED,)) -> dict[str, Any] | None:
    """One mention as a FHIR ``CodeableConcept``: a coding for each of its assignments of
    these statuses, from every code system among them, and the wording as its text.  None
    when the mention has no such assignment."""
    wanted = set(statuses)
    codings = [coding(a) for a in noted.assignments if a.status in wanted]
    return {"coding": codings, "text": noted.exact} if codings else None


def codeable_concepts(annotation: Annotation, statuses: Iterable[str] = (CONFIRMED,),
                      together: bool = True) -> list[dict[str, Any]]:
    """The mentions of an annotation document as FHIR CodeableConcepts, in reading order,
    each with the mention it belongs to and its place::

        {"mention": "m1", "start": 11, "end": 27, "codeableConcept": {"coding": [...], "text": "…"}}

    By default only what a person confirmed is given.  With ``together`` the codings of a
    mention stand in one CodeableConcept: whoever confirmed them said that they are what
    this wording means.  Where a mention's codings may be different meanings, ``together``
    off gives a CodeableConcept for each."""
    wanted = tuple(statuses)
    out = []
    for noted in annotation.mentions:
        concept = codeable_concept(noted, wanted)
        if concept is None:
            continue
        parts = [concept] if together else [{"coding": [c], "text": noted.exact}
                                            for c in concept["coding"]]
        out += [{"mention": noted.id, "start": noted.start, "end": noted.end,
                 "codeableConcept": part} for part in parts]
    return out
