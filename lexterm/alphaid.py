# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The Alpha-ID-SE of the BfArM, as packages of a user's own store.

The Alpha-ID-SE is the alphabetical index to the ICD-10-GM as a file: the wordings of
diagnoses as they are written, each with a stable number of its own (the Alpha-ID), the
ICD-10-GM codes it is classified under and, for a rare disease, the Orpha number.  The
official titles of the ICD-10-GM seldom stand in a letter in so many words; these wordings
do.

Three packages come of the file, so that one wording is coded in every system the file
names for it (as the German profiles for a diagnosis put the three side by side):

- the **Alpha-ID** itself, a code system of its own: one concept for every wording, with the
  codes the file gives it as properties;
- a **supplement to the ICD-10-GM**: the wordings as further terms of the ICD-10-GM codes
  they are classified under.  It is a supplement and not a package under the ICD-10-GM's
  URL, so that it never takes the place of the classification with its titles and hierarchy;
- a **supplement to the ORPHAcodes** likewise.

A wording is taken as the file gives it.  Entries the file marks as no longer valid are left
out: they are kept there for decoding old numbers, not for coding.

Nothing of the Alpha-ID-SE comes with lexterm: a person downloads the file from the BfArM
under its conditions (``lexterm sources`` says where), and lexterm reads it.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

from lexcor import Concept, Package, PackageError, Term

ALPHA_ID = "http://fhir.de/CodeSystem/bfarm/alpha-id"
ICD_10_GM = "http://fhir.de/CodeSystem/bfarm/icd-10-gm"
ORPHA = "http://www.orpha.net"
PUBLISHER = "Bundesinstitut für Arzneimittel und Medizinprodukte (BfArM)"
# the statement of the source that the conditions of the download ask for (as of 1 August 2025)
SOURCE = ("Die Erstellung erfolgt unter Verwendung der maschinenlesbaren Fassung des"
          " Bundesinstituts für Arzneimittel und Medizinprodukte (BfArM). Für die in der"
          " Alpha-ID-SE enthaltenen Orpha-Kennnummern ist der Inhaber der Nutzungsrechte das"
          " INSERM US14 (Institut national de la santé et de la recherche médicale), 96, rue"
          " Didot, 75014 Paris, Frankreich.")
# the fields of a record after its validity and its number, and the property each becomes;
# the marks the file sets on a code (+ for a dagger, * for a star, ! for an additional code)
# say nothing its field does not say
CODES = ((2, "icd-10-gm-primary"), (3, "icd-10-gm-star"), (4, "icd-10-gm-additional"),
         (5, "icd-10-gm-primary-2"))
ORPHA_FIELD, ORPHA_PROPERTY, TEXT_FIELD, FIELDS = 6, "orpha", 7, 8
_YEAR = re.compile(r"alphaid(?:se)?(\d{4})", re.IGNORECASE)


def _not_the_file(german: str, english: str) -> PackageError:
    return PackageError("not-alpha-id", f"Das ist keine Datei der Alpha-ID-SE: {german}",
                        f"This is no file of the Alpha-ID-SE: {english}")


def _lines(file: Path) -> tuple[str, list[str]]:
    """The name and the lines of the data file: the file itself, or the one in the archive
    as it is downloaded (beside its description).  Nothing is unpacked onto the disk."""
    try:
        if zipfile.is_zipfile(file):
            with zipfile.ZipFile(file) as archive:
                members = [m for m in archive.infolist()
                           if m.filename.lower().endswith(".txt")
                           and "liesmich" not in m.filename.lower()]
                if not members:
                    raise _not_the_file("Das Archiv enthält keine Datendatei (.txt).",
                                        "the archive holds no data file (.txt).")
                member = max(members, key=lambda m: m.file_size)
                name, data = Path(member.filename).name, archive.read(member)
        else:
            name, data = file.name, file.read_bytes()
    except (OSError, zipfile.BadZipFile) as error:
        raise PackageError("unreadable", f"{file} lässt sich nicht lesen: {error}",
                           f"{file} cannot be read: {error}") from error
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:  # the editions before the file came in UTF-8
        text = data.decode("cp1252", errors="replace")
    return name, text.splitlines()


def read_alpha_id(file: str | Path) -> tuple[list[Package], int]:
    """The Alpha-ID-SE as packages: the Alpha-ID as a code system, and its wordings as a
    supplement to the ICD-10-GM and as one to the ORPHAcodes.  ``file`` is the archive as
    downloaded or the data file in it.  Returns the packages and how many entries were left
    out because the file marks them as no longer valid."""
    name, lines = _lines(Path(file))
    year = _YEAR.search(name)
    version = year.group(1) if year else ""
    wordings: list[Concept] = []
    coded: dict[str, list[Term]] = {}
    rare: dict[str, list[Term]] = {}
    retired = 0
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        fields = [" ".join(field.split()) for field in line.split("|")]
        if len(fields) != FIELDS or fields[0] not in ("0", "1") or not fields[1] \
                or not fields[TEXT_FIELD]:
            raise _not_the_file(
                f"Zeile {number} hat nicht die acht Felder eines Eintrags.",
                f"line {number} does not have the eight fields of an entry.")
        if fields[0] == "0":
            retired += 1
            continue
        term = Term(fields[TEXT_FIELD], "de", "preferred")
        properties = {}
        for place, called in CODES:
            code = fields[place].rstrip("+*!")
            if code:
                properties[called] = code
                coded.setdefault(code, []).append(Term(term.value, "de"))
        if fields[ORPHA_FIELD]:
            properties[ORPHA_PROPERTY] = fields[ORPHA_FIELD]
            rare.setdefault(fields[ORPHA_FIELD], []).append(Term(term.value, "de"))
        wordings.append(Concept(fields[1], term.value, "", "", [term], properties))
    if not wordings:
        raise _not_the_file("Sie enthält keinen gültigen Eintrag.", "it holds no valid entry.")

    def package(called: str, title: str, concepts: list[Concept], url: str = "",
                supplements: str = "") -> Package:
        return Package(url=url, version=version, name=called, title=title, publisher=PUBLISHER,
                       copyright=SOURCE, language="de", redistributable=False,
                       concepts=concepts, supplements=supplements)

    def supplement(terms: dict[str, list[Term]]) -> list[Concept]:
        return [Concept(code, terms=terms[code]) for code in sorted(terms)]

    packages = [
        package("AlphaIDSE", "Alpha-ID-SE", wordings, url=ALPHA_ID),
        # the edition of a year is the index to the ICD-10-GM of that year
        package("AlphaIDSE_ICD10GM", "Alpha-ID-SE: wordings for the ICD-10-GM",
                supplement(coded), supplements=f"{ICD_10_GM}|{version}" if version else ICD_10_GM),
    ]
    if rare:
        packages.append(package("AlphaIDSE_ORPHAcodes", "Alpha-ID-SE: wordings for the ORPHAcodes",
                                supplement(rare), supplements=ORPHA))
    return packages, retired
