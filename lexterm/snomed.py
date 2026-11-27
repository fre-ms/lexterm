# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""SNOMED CT from the files a release comes in (RF2), as a package of a user's own store.

SNOMED CT is not published as a FHIR CodeSystem with its concepts in it.  A national edition
(the German one: the International Edition with the German extension) is given out as a
folder of tab-separated files, to holders of an affiliate licence.  This module reads the
``Snapshot`` of such a release: the active concepts, their active descriptions in the
languages asked for, and from the language reference sets which description is the preferred
one.  The class of a concept is the word in brackets at the end of its fully specified name
("disorder", "procedure", "substance").

Nothing of SNOMED CT comes with lexterm, and the package made here is never passed on
(``redistributable`` is false): it is for the licence holder's own store.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

from lexcor import Concept, Package, PackageError, Term

SNOMED = "http://snomed.info/sct"
FULLY_SPECIFIED_NAME = "900000000000003001"
PREFERRED = "900000000000548007"
_TAG = re.compile(r"\s\(([^()]+)\)\s*$")
_DATE = re.compile(r"_(\d{8})\.txt$")


def _rows(file: Path) -> Iterator[dict[str, str]]:
    """The rows of a release file: tab-separated, a header line, no quoting."""
    with file.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        header = next(reader, [])
        for row in reader:
            yield dict(zip(header, row, strict=False))


def _files(folder: Path, beginning: str) -> list[Path]:
    """The snapshot files of one kind in a release, wherever its folders put them."""
    return sorted(p for p in folder.rglob(f"{beginning}*.txt") if "Snapshot" in p.name)


def read_rf2(folder: str | Path, languages: tuple[str, ...] = ("de",)) -> Package:
    """A release of SNOMED CT as a package: every active concept that has an active
    description in one of ``languages``, with those descriptions as its terms.  The name
    shown is the preferred term in the first of the languages the concept has."""
    folder = Path(folder)
    concepts = _files(folder, "sct2_Concept_")
    descriptions = _files(folder, "sct2_Description_")
    if not concepts or not descriptions:
        raise PackageError(
            "not-a-release",
            "Der Ordner enthält keine SNOMED-CT-Ausgabe (es fehlen die Snapshot-Dateien"
            " sct2_Concept und sct2_Description).",
            "The folder holds no SNOMED CT release (the snapshot files sct2_Concept and"
            " sct2_Description are missing).")
    active = {row["id"] for file in concepts for row in _rows(file) if row.get("active") == "1"}
    preferred = {row["referencedComponentId"]
                 for file in _files(folder, "der2_cRefset_Language") for row in _rows(file)
                 if row.get("active") == "1" and row.get("acceptabilityId") == PREFERRED}
    wanted = {language: place for place, language in enumerate(languages)}
    classes: dict[str, str] = {}
    terms: dict[str, list[tuple[int, bool, Term]]] = {}
    modules: Counter[str] = Counter()
    for file in descriptions:
        for row in _rows(file):
            concept = row.get("conceptId", "")
            if row.get("active") != "1" or concept not in active:
                continue
            term, language = row.get("term", "").strip(), row.get("languageCode", "")
            if row.get("typeId") == FULLY_SPECIFIED_NAME:
                tag = _TAG.search(term)
                if tag and concept not in classes:
                    classes[concept] = tag.group(1)
            elif language in wanted and term:
                first = row["id"] in preferred
                terms.setdefault(concept, []).append(
                    (wanted[language], not first, Term(term, language,
                                                       "preferred" if first else "synonym")))
                modules[row.get("moduleId", "")] += 1
    listed = []
    for code in sorted(terms):
        ranked = sorted(terms[code], key=lambda t: (t[0], t[1], t[2].value))
        listed.append(Concept(code, ranked[0][2].value, classes.get(code, ""), "",
                              [term for _place, _other, term in ranked]))
    dates = sorted(m.group(1) for file in concepts + descriptions
                   if (m := _DATE.search(file.name)))
    version = dates[-1] if dates else ""
    if version and modules:
        version = f"{SNOMED}/{modules.most_common(1)[0][0]}/version/{version}"
    return Package(
        url=SNOMED, version=version, name="SNOMED_CT",
        title=f"SNOMED CT ({', '.join(languages)})", publisher="SNOMED International",
        copyright="SNOMED CT, © SNOMED International; read from a release for the licence"
                  " holder's own use, not to be passed on.",
        language=languages[0], redistributable=False, concepts=listed)
