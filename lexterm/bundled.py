# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The packages that come with lexterm: free ones only.

So far one: the German names of what Wikidata lists with a medical identifier (an ICD-10
code, an ATC code, a WHO INN, a LOINC code or a MeSH descriptor of the trees A to G), under
CC0 1.0.  Its codes are Wikidata's own identifiers, and its URI is Wikidata's
(``http://www.wikidata.org/entity/``), so that a code of this package is the item itself:
the package is an extract of that system, not a system of lexterm's.  ``tools/`` holds the
script that builds the file.

The file does not say which of an item's names is its label, so the name shown for a
concept is the first of its names by the alphabet; and an item that Wikidata puts into
several classes gets one, the most specific (``PRIORITY``).

Packages a user holds a licence for (SNOMED CT, a medical dictionary) are never here: they
are imported into the user's own store.
"""

from __future__ import annotations

import csv
import gzip
from functools import cache
from importlib import resources

from lexcor import Concept, Package, Term

WIKIDATA = "http://www.wikidata.org/entity/"
WIKIDATA_VERSION = "2026-11-02"  # the day the names were fetched (first line of the file)
# where an item has several classes it gets the first of these that it has: the more specific
# role first (a drug before a substance, a symptom before a disorder)
PRIORITY = ("drug", "symptom", "disorder", "laboratory test", "procedure", "anatomy", "organism",
            "psychology", "physiology", "substance")


@cache
def wikidata() -> Package:
    """German medical terms from Wikidata, with the item as the code of each."""
    names: dict[str, list[str]] = {}
    classes: dict[str, set[str]] = {}
    source = resources.files("lexterm").joinpath("data", "wikidata_medical_de.csv.gz")
    with source.open("rb") as raw, gzip.open(raw, "rt", encoding="utf-8", newline="") as file:
        rows = csv.reader(line for line in file if not line.startswith("#"))
        next(rows)  # the header line: term, class, code
        for term, cls, item in rows:
            names.setdefault(item, [])
            if term not in names[item]:
                names[item].append(term)
            classes.setdefault(item, set()).add(cls)
    concepts = []
    for item in sorted(names):
        cls = next((c for c in PRIORITY if c in classes[item]), sorted(classes[item])[0])
        terms = sorted(names[item])
        concepts.append(Concept(item, terms[0], cls, "", [Term(t, "de") for t in terms]))
    return Package(
        url=WIKIDATA, version=WIKIDATA_VERSION, name="WikidataMedicalTermsGerman",
        title="Medical terms from Wikidata (German)", publisher="Wikidata",
        copyright="CC0 1.0, https://creativecommons.org/publicdomain/zero/1.0/",
        language="de", redistributable=True, concepts=concepts)


def packages() -> tuple[Package, ...]:
    """Every package that comes with lexterm."""
    return (wikidata(),)
