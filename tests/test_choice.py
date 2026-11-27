# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""Every run chooses its packages, the annotation document records what it applied, and
codes that are no codes to code with are marked and can be left out of the output."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lexcor import Concept, Package, Term, load_annotation

import lexterm
from lexterm import bundled
from lexterm.cli import main
from lexterm.export import codeable_concepts

ICD = "http://fhir.de/CodeSystem/bfarm/icd-10-gm"


def classification() -> Package:
    """An invented classification with a hierarchy, under the URL of the ICD-10-GM."""
    return Package(url=ICD, version="2027", title="Invented classification", language="de-DE",
                   concepts=[
                       Concept("X10-X14", "Musterkrankheit"),
                       Concept("X11", "Musterkrankheit, Typ 2", "", "X10-X14"),
                       Concept("X11.9", "Musterkrankheit, Typ 2, ohne Komplikation", "", "X11",
                               [Term("Musterkrankheit Typ 2", "de")])])


def test_without_a_store_the_document_names_the_package_lexterm_brings() -> None:
    document = lexterm.annotate("Ramipril seit 2019.")
    assert document.packages == [{
        "url": bundled.WIKIDATA, "version": bundled.WIKIDATA_VERSION,
        "sha256": bundled.wikidata().sha256(), "title": bundled.wikidata().title}]
    assert lexterm.listing() == document.packages
    assert lexterm.listing(packages=["http://example.org/none"]) == []


def test_terminal_codes_are_marked_and_can_be_left_out(tmp_path: Path) -> None:
    with lexterm.open_store(tmp_path / "store.sqlite") as store:
        store.add_package(classification())
        text = "Musterkrankheit, später Musterkrankheit Typ 2."
        # the comma does not count: the category's title stands there as well
        assert {a.code: a.terminal for m in lexterm.tag(text, store)
                for a in m.assignments} == {"X10-X14": False, "X11": False, "X11.9": True}
        document = lexterm.annotate(text, store)
        document.confirm_all(ICD)
    coded = [[c["code"] for c in concept["codeableConcept"]["coding"]]
             for concept in codeable_concepts(document)]
    assert coded == [["X10-X14"], ["X11", "X11.9"]]
    kept = [[c["code"] for c in concept["codeableConcept"]["coding"]]
            for concept in codeable_concepts(document, terminal_codes=True)]
    assert kept == [["X11.9"]]


def test_lexterm_records_and_repeats_its_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                              capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setenv("LEXCOR_DATA", str(tmp_path / "data"))
    letter, document = tmp_path / "letter.txt", tmp_path / "letter.json"
    letter.write_text("Musterkrankheit Typ 2, Ramipril.", encoding="utf-8")
    assert main(["tag", str(letter), "--annotation", str(document)]) == 0  # an empty store
    assert [p["url"] for p in load_annotation(document).packages] == [bundled.WIKIDATA]
    assert main(["tag", str(letter), "--annotation", str(document), "--repeat"]) == 0
    with lexterm.open_store() as store:
        store.add_package(classification())
    capsys.readouterr()
    assert main(["--language", "en", "tag", str(letter), "--annotation", str(document),
                 "--repeat"]) == 1  # the store now answers with other packages
    said = capsys.readouterr().err
    assert f"{bundled.WIKIDATA} is no longer in the store" in said and f"{ICD} is new" in said
    assert main(["tag", str(letter), "--annotation", str(document)]) == 0
    assert [p["url"] for p in load_annotation(document).packages] == [ICD]
    capsys.readouterr()
    assert main(["--json", "tag", str(letter), "--without", ICD]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "no-package-chosen"

    with lexterm.open_store() as store:
        document_now = lexterm.annotate(letter.read_text(encoding="utf-8"), store)
    document_now.confirm_all(ICD)
    document_now.save(document)
    assert main(["export", "fhir", str(document), "--terminal-codes"]) == 0
    concepts = json.loads(capsys.readouterr().out)["concepts"]
    assert [c["code"] for concept in concepts for c in concept["codeableConcept"]["coding"]] \
        == ["X11.9"]
