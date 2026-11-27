# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""SNOMED CT from the files a release comes in (RF2), as a package of a user's own store.

SNOMED CT is not published as a FHIR CodeSystem with its concepts in it.  A national edition
(the German one: the International Edition with the German extension) is given out as a ZIP
file of tab-separated files, to holders of an affiliate licence.  This module reads the
``Snapshot`` of such a release, from the ZIP file as it was downloaded or from the folder it
unpacks to: the active concepts, their active descriptions in the languages asked for that a
language reference set accepts, and from those reference sets which description is the
preferred one.  The class of a concept is the word in brackets at the end of its fully
specified name ("disorder", "procedure", "substance").

Nothing of SNOMED CT comes with lexterm, and the package made here is never passed on
(``redistributable`` is false): it is for the licence holder's own store.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from collections import Counter
from collections.abc import Iterator
from pathlib import Path, PurePosixPath
from types import TracebackType

from lexcor import Concept, Package, PackageError, Term

SNOMED = "http://snomed.info/sct"
FULLY_SPECIFIED_NAME = "900000000000003001"
PREFERRED = "900000000000548007"
_TAG = re.compile(r"\s\(([^()]+)\)\s*$")
_DATE = re.compile(r"_(\d{8})\.txt$")


class _Release:
    """The files of a release, in a ZIP file or in a folder, wherever its folders put them."""

    def __init__(self, source: Path) -> None:
        self.archive = zipfile.ZipFile(source) if source.is_file() else None
        if self.archive is not None:
            self.names = [n for n in self.archive.namelist() if n.endswith(".txt")]
        else:
            self.names = [str(p) for p in source.rglob("*.txt")] if source.is_dir() else []

    def __enter__(self) -> _Release:
        return self

    def __exit__(self, kind: type[BaseException] | None, error: BaseException | None,
                 trace: TracebackType | None) -> None:
        if self.archive is not None:
            self.archive.close()

    def files(self, beginning: str) -> list[str]:
        """The snapshot files of one kind."""
        return sorted(n for n in self.names
                      if (base := PurePosixPath(n.replace("\\", "/")).name).startswith(beginning)
                      and "Snapshot" in base)

    def rows(self, names: list[str]) -> Iterator[dict[str, str]]:
        """The rows of release files: tab-separated, a header line, no quoting."""
        for name in names:
            raw = self.archive.open(name) if self.archive is not None else open(name, "rb")
            with raw, io.TextIOWrapper(raw, encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
                header = next(reader, [])
                for row in reader:
                    yield dict(zip(header, row, strict=False))


def _not_a_release() -> PackageError:
    return PackageError(
        "not-a-release",
        "Das ist keine SNOMED-CT-Ausgabe (es fehlen die Snapshot-Dateien sct2_Concept und"
        " sct2_Description). Erwartet wird die ZIP-Datei, wie sie geladen wurde, oder der"
        " Ordner, zu dem sie entpackt wurde.",
        "This is no SNOMED CT release (the snapshot files sct2_Concept and sct2_Description"
        " are missing). Expected is the ZIP file as it was downloaded, or the folder it was"
        " unpacked to.")


def read_rf2(source: str | Path, languages: tuple[str, ...] = ("de",)) -> Package:
    """A release of SNOMED CT as a package: every active concept that has an active
    description in one of ``languages``, with those descriptions as its terms.  ``source`` is
    the release as downloaded (a ZIP file) or the folder it unpacks to.  A description counts
    when a language reference set of the release accepts it (when the release has none, every
    active one counts).  The name shown is the preferred term in the first of the languages
    the concept has."""
    try:
        release = _Release(Path(source))
    except zipfile.BadZipFile:
        raise _not_a_release() from None
    with release:
        concepts = release.files("sct2_Concept_")
        descriptions = release.files("sct2_Description_")
        if not concepts or not descriptions:
            raise _not_a_release()
        active = {row["id"] for row in release.rows(concepts) if row.get("active") == "1"}
        wanted = {language: place for place, language in enumerate(languages)}
        classes: dict[str, str] = {}
        found: dict[str, tuple[str, int, str, str, str]] = {}
        for row in release.rows(descriptions):
            concept = row.get("conceptId", "")
            if row.get("active") != "1" or concept not in active:
                continue
            term, language = row.get("term", "").strip(), row.get("languageCode", "")
            if row.get("typeId") == FULLY_SPECIFIED_NAME:
                tag = _TAG.search(term)
                if tag and concept not in classes:
                    classes[concept] = tag.group(1)
            elif language in wanted and term:
                found[row["id"]] = (concept, wanted[language], term, language,
                                    row.get("moduleId", ""))
        references = release.files("der2_cRefset_Language")
        accepted: dict[str, bool] = {}
        for row in release.rows(references):
            if row.get("active") == "1" and (key := row.get("referencedComponentId")) in found:
                accepted[key] = accepted.get(key, False) or row.get("acceptabilityId") == PREFERRED
        dates = sorted(m.group(1) for name in concepts + descriptions
                       if (m := _DATE.search(name)))
    terms: dict[str, list[tuple[int, bool, Term]]] = {}
    modules: Counter[str] = Counter()
    for key, (concept, place, term, language, module) in found.items():
        if references and key not in accepted:
            continue
        first = accepted.get(key, False)
        terms.setdefault(concept, []).append(
            (place, not first, Term(term, language, "preferred" if first else "synonym")))
        modules[module] += 1
    listed = []
    for code in sorted(terms):
        ranked = sorted(terms[code], key=lambda t: (t[0], t[1], t[2].value))
        listed.append(Concept(code, ranked[0][2].value, classes.get(code, ""), "",
                              [term for _place, _other, term in ranked]))
    version = dates[-1] if dates else ""
    if version and modules:
        version = f"{SNOMED}/{modules.most_common(1)[0][0]}/version/{version}"
    return Package(
        url=SNOMED, version=version, name="SNOMED_CT",
        title=f"SNOMED CT ({', '.join(languages)})", publisher="SNOMED International",
        copyright="SNOMED CT, © SNOMED International; read from a release for the licence"
                  " holder's own use, not to be passed on.",
        language=languages[0], redistributable=False, concepts=listed)
