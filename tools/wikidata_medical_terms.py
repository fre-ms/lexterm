# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""Build the package of German medical terms from Wikidata (CC0 1.0).

German labels and aliases of every item that carries an ATC code (P267) or a WHO INN (P2275)
(class drug), an ICD-10 code (P494) (disorder), a LOINC code (P4338) (laboratory test), or a
MeSH descriptor (P486) in one of the trees A to G (P672): A anatomy, B organism, C disorder
(C23.888 symptom), D substance, E procedure, F psychology, G physiology.  A term may carry
several classes, one row each; the Wikidata item is the code.

This is the one script of lexterm that uses the network, and only when a person runs it:

    python tools/wikidata_medical_terms.py [target.csv.gz]

It writes ``lexterm/data/wikidata_medical_de.csv.gz``; set ``WIKIDATA_VERSION`` in
``lexterm/bundled.py`` to the day it ran.
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import io
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://query.wikidata.org/sparql"
AGENT = "lexterm/0.1 (open-source recognition of medical terms)"
TARGET = Path(__file__).resolve().parent.parent / "lexterm" / "data" / "wikidata_medical_de.csv.gz"
MESH_CLASSES = {"A": "anatomy", "B": "organism", "C": "disorder", "D": "substance",
                "E": "procedure", "F": "psychology", "G": "physiology", "S": "symptom"}
MESH_PREFIXES = ("D000", "D001", "D002", "D003", "D004", "D005", "D006", "D007", "D008",
                 "D009", "D01", "D02", "D03", "D04", "D05", "D06", "D07")
_LABELS = """{ ?item rdfs:label ?label } UNION { ?item skos:altLabel ?label }
  FILTER(LANG(?label) = "de")"""
Row = tuple[str, str, str]


def query(sparql: str, attempts: int = 5) -> list[list[str]]:
    """The rows of a query, tried again after a pause when the service is busy."""
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": sparql})
    for attempt in range(attempts):
        request = urllib.request.Request(url, headers={"Accept": "text/csv", "User-Agent": AGENT})
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                text = response.read().decode("utf-8")
            return list(csv.reader(io.StringIO(text)))[1:]
        except Exception as error:  # noqa: BLE001 (time-outs and "too many requests" alike)
            pause = 15 * (attempt + 1)
            print(f"  attempt {attempt + 1} failed ({error}); waiting {pause} s", file=sys.stderr)
            time.sleep(pause)
    raise RuntimeError("the query to Wikidata failed repeatedly")


def item(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def by_property(prop: str, cls: str) -> list[Row]:
    rows = query(f"SELECT DISTINCT ?item ?label WHERE {{ ?item wdt:{prop} ?v . {_LABELS} }}")
    return [(r[1], cls, item(r[0])) for r in rows if len(r) >= 2]


def by_mesh(prefix: str) -> list[Row]:
    sparql = f"""SELECT ?item ?label (GROUP_CONCAT(DISTINCT ?k; separator=" ") AS ?classes)
WHERE {{
  ?item wdt:P486 ?v . FILTER(STRSTARTS(?v, "{prefix}"))
  ?item wdt:P672 ?tree . FILTER(REGEX(?tree, "^[A-G]"))
  BIND(IF(STRSTARTS(?tree, "C23.888"), "S", SUBSTR(?tree, 1, 1)) AS ?k)
  {_LABELS}
}} GROUP BY ?item ?label"""
    out = []
    for r in query(sparql):
        if len(r) >= 3:
            out += [(r[1], MESH_CLASSES[k], item(r[0])) for k in sorted(set(r[2].split()))]
    return out


def main(target: Path) -> None:
    found: list[Row] = []
    steps = [("ATC (P267)", lambda: by_property("P267", "drug")),
             ("INN (P2275)", lambda: by_property("P2275", "drug")),
             ("ICD-10 (P494)", lambda: by_property("P494", "disorder")),
             ("LOINC (P4338)", lambda: by_property("P4338", "laboratory test"))]
    steps += [(f"MeSH {p}*", lambda p=p: by_mesh(p)) for p in MESH_PREFIXES]
    for name, step in steps:
        started = time.time()
        new = step()
        found += new
        print(f"{name}: {len(new)} rows ({time.time() - started:.0f} s)")
        time.sleep(2)
    unique: dict[tuple[str, str], Row] = {}
    for term, cls, code in found:
        term = " ".join(term.split())
        if len(term) >= 3 and not term.isdigit():
            unique.setdefault((term.casefold(), cls), (term, cls, code))
    rows = sorted(unique.values(), key=lambda r: (r[0].casefold(), r[1], r[2]))
    text = io.StringIO()
    text.write("# Source: Wikidata (ATC P267, INN P2275, ICD-10 P494, LOINC P4338, MeSH"
               f" P486/P672), fetched {dt.date.today().isoformat()}; licence: CC0 1.0,"
               " https://creativecommons.org/publicdomain/zero/1.0/\n")
    writer = csv.writer(text, lineterminator="\n")
    writer.writerow(["term", "class", "code"])
    writer.writerows(rows)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as raw, gzip.GzipFile(filename="", fileobj=raw, mode="wb",
                                                 mtime=0) as packed:
        packed.write(text.getvalue().encode("utf-8"))
    print(f"written: {target} ({target.stat().st_size / 1e6:.2f} MB), {len(rows)} rows")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else TARGET)
