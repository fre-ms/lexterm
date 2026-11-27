# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm as a library: it brings no terminology, tags with the packages of a store, and
answers the generous question."""

from __future__ import annotations

import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest
from lexcor import Concept, Kind, Package, Term
from sample_terms import MEDICINE, medicine

import lexterm

URL = "https://example.org/CodeSystem/sample"


def sample() -> Package:
    return Package(url=URL, version="1", title="Sample", language="de", concepts=[
        Concept("K51", "Colitis ulcerosa", "disorder", "", [Term("Colitis ulcerosa", "de")]),
        Concept("E1", "Babinski-Zeichen", "sign", "", [Term("Babinski-Zeichen", "de")]),
        Concept("X1", "fast", "other", "", [Term("fast", "en")]),
        Concept("M1", "Ramipril", "drug", "", [Term("Ramipril", "de")])])


def test_lexterm_brings_no_terminology(tmp_path: Path) -> None:
    assert not resources.files("lexterm").joinpath("data").is_dir()
    with lexterm.open_store(tmp_path / "empty.sqlite") as store:
        assert lexterm.tag("Bekannte arterielle Hypertonie.", store) == []
        assert lexterm.listing(store) == []


def test_a_text_is_tagged_with_the_packages_of_a_store(tmp_path: Path) -> None:
    text = "Bekannte arterielle Hypertonie, Ramipril seit 2019."
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(medicine())
        found = lexterm.tag(text, store)
        assert [m.text for m in found] == ["arterielle Hypertonie", "Ramipril"]
        assert [(m.start, m.end) for m in found] == [(9, 30), (32, 40)]
        assignment = found[1].assignments[0]
        assert (assignment.system, assignment.version, assignment.code, assignment.cls,
                assignment.kind) == (MEDICINE, "1", "C2", "drug", Kind.AS_WRITTEN)
        assert [m.text for m in lexterm.tag(text, store, classes=["drug"])] == ["Ramipril"]
        assert lexterm.tag(text, store, packages=["https://example.org/none"]) == []
        assert lexterm.recogniser(store) is lexterm.recogniser(store)  # built once


def test_with_a_store_its_packages_decide(tmp_path: Path) -> None:
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(sample())
        text = "Kolitis ulzerosa, Ramiprils Wirkung fast aufgehoben, Hypertonie."
        found = lexterm.tag(text, store)
        # lexterm's table of spellings; German terms only
        assert [(m.text, m.assignments[0].code, m.assignments[0].kind) for m in found] == [
            ("Kolitis ulzerosa", "K51", Kind.VARIANT), ("Ramiprils", "M1", Kind.INFLECTED)]
        assert [m.text for m in lexterm.tag(text, store, language="en")] == ["fast"]
        store.add_package(medicine())
        assert "Hypertonie" in [m.text for m in lexterm.tag(text, store)]
        store.hide(URL, "M1")
        assert "Ramiprils" not in [m.text for m in lexterm.tag(text, store, packages=[URL])]
    with lexterm.open_store(tmp_path / "lexterm.sqlite", readonly=True) as store:
        assert "Hypertonie" in [m.text for m in lexterm.tag("Hypertonie", store)]


def test_the_generous_question(tmp_path: Path) -> None:
    text = "Babinski positiv, Parkinson-Syndrom bei Herrn Flantz."
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(sample())
        store.add_package(medicine())
        assert lexterm.covers(text, 0, 8, store)            # an eponym, by lexterm's heads
        assert lexterm.covers(text, text.index("Parkinson"), text.index("bei") - 1, store,
                              whole=True)
        start = text.index("Flantz")
        assert not lexterm.covers(text, start, start + 6, store)
        assert lexterm.cover(store).is_term("Hypertonien")
        only = lexterm.cover(store, packages=[URL])
        assert not only.covers(text, text.index("Parkinson"), text.index("bei") - 1)


def test_tagging_with_a_store_opened_for_reading_writes_nothing(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with lexterm.open_store(tmp_path / "given" / "lexterm.sqlite") as store:
        store.add_package(medicine())
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    for name in ("HOME", "LEXCOR_DATA", "XDG_DATA_HOME", "APPDATA", "TMPDIR"):
        monkeypatch.setenv(name, str(elsewhere))
    before = sorted(p.name for p in (tmp_path / "given").iterdir())
    with lexterm.open_store(tmp_path / "given" / "lexterm.sqlite", readonly=True) as store:
        assert lexterm.tag("Diabetes mellitus", store) and lexterm.covers(
            "Hypertonie", 0, 10, store)
    assert list(elsewhere.iterdir()) == []
    assert sorted(p.name for p in (tmp_path / "given").iterdir()) == before


def test_importing_lexterm_loads_no_window() -> None:
    script = "import lexterm, sys; sys.exit('PySide6' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", script], check=False).returncode == 0


def test_the_annotation_document_keeps_a_persons_decisions(tmp_path: Path) -> None:
    from lexcor import load_annotation

    text = "Bekannte arterielle Hypertonie, Ramipril seit 2019."
    store = lexterm.open_store(tmp_path / "lexterm.sqlite")
    store.add_package(medicine())
    document = lexterm.annotate(text, store)
    assert document.made_with == f"lexterm {lexterm.__version__}"
    assert document.packages == [{"url": MEDICINE, "version": "1",
                                  "sha256": medicine().sha256(), "title": "Invented medicine"}]
    assert document.settings == {"packages": [], "classes": [], "language": "de",
                                 "nested": False}
    assert [(n.id, n.exact) for n in document.mentions] == [("m1", "arterielle Hypertonie"),
                                                            ("m2", "Ramipril")]
    document.reject("m2")
    document.confirm("m1")
    document.save(tmp_path / "letter.lexterm.json")
    again = lexterm.annotate(text, store,
                             annotation=load_annotation(tmp_path / "letter.lexterm.json"))
    assert [(n.id, a.status) for n, a in again.assignments(None)] == [
        ("m1", "confirmed"), ("m2", "rejected")]
    assert again.dumps() == document.dumps()  # the same text and decisions: the same bytes
    longer = "Neu: Diabetes mellitus. " + text
    moved = lexterm.annotate(longer, store, annotation=again)
    store.close()
    assert [(n.exact, a.status) for n, a in moved.assignments(None)] == [
        ("Diabetes mellitus", "proposed"), ("arterielle Hypertonie", "confirmed"),
        ("Ramipril", "rejected")]


def test_one_wording_is_coded_in_every_code_system_that_knows_it(tmp_path: Path) -> None:
    from lexterm.export import codeable_concepts

    icd = Package(url="http://fhir.de/CodeSystem/bfarm/icd-10-gm", version="2026", language="de",
                  concepts=[Concept("I10", "Essentielle Hypertonie", "disorder", "",
                                    [Term("Hypertonie", "de")])])
    own = Package(url="https://example.org/CodeSystem/own", version="3", language="de",
                  concepts=[Concept("HT", "Hypertonien", "note", "", [Term("Hypertonien", "de")])])
    text = "Bekannte Hypertonien."
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(icd)
        store.add_package(own)
        store.add_package(medicine())
        document = lexterm.annotate(text, store)
    mention, = document.mentions
    systems = [(a.system, a.code, a.kind) for a in mention.assignments]
    assert ("http://fhir.de/CodeSystem/bfarm/icd-10-gm", "I10", "inflected") in systems
    assert ("https://example.org/CodeSystem/own", "HT", "as written") in systems
    assert (MEDICINE, "C1", "inflected") in systems  # three code systems
    assert codeable_concepts(document) == []  # nothing confirmed yet
    document.confirm(mention.id, system=icd.url)
    document.confirm(mention.id, system=MEDICINE)
    document.reject(mention.id, system=own.url)
    concept, = codeable_concepts(document)
    assert (concept["mention"], concept["start"], concept["end"]) == (mention.id, 9, 20)
    codings = concept["codeableConcept"]["coding"]
    assert concept["codeableConcept"]["text"] == "Hypertonien"
    assert [c["system"] for c in codings] == [
        "http://fhir.de/CodeSystem/bfarm/icd-10-gm", MEDICINE]
    assert codings[0] == {"system": "http://fhir.de/CodeSystem/bfarm/icd-10-gm",
                          "version": "2026", "code": "I10",
                          "display": "Essentielle Hypertonie", "userSelected": True}
    assert len(codeable_concepts(document, together=False)) == 2
    every, = codeable_concepts(document, ("proposed", "confirmed", "rejected"))
    assert len(every["codeableConcept"]["coding"]) == 3
    assert "userSelected" not in every["codeableConcept"]["coding"][-1]  # the rejected one


def test_a_package_codes_the_shorter_wording_it_knows_inside_a_longer_mention(
        tmp_path: Path) -> None:
    icd = Package(url="https://example.org/icd", language="de", concepts=[
        Concept("G20", "Morbus Parkinson", "disorder", "", [Term("Morbus Parkinson", "de")]),
        Concept("G20.9", "Parkinson", "disorder", "", [Term("Parkinson", "de")])])
    names = Package(url="https://example.org/eponyms", language="de", concepts=[
        Concept("P1", "Parkinson", "eponym", "", [Term("Parkinson", "de")])])
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(icd)
        store.add_package(names)
        text = "Bekannter Morbus Parkinson."
        found = [(m.text, [a.code for a in m.assignments]) for m in lexterm.tag(text, store)]
        assert found == [("Morbus Parkinson", ["G20"]), ("Parkinson", ["P1"])]
        nested = [(m.text, [a.code for a in m.assignments])
                  for m in lexterm.tag(text, store, nested=True)]
        assert nested == [("Morbus Parkinson", ["G20"]), ("Parkinson", ["P1", "G20.9"])]


def test_terms_of_a_package_marked_with_a_region_are_found(tmp_path: Path) -> None:
    """The BfArM marks its CodeSystems "de-DE"; a German text asks for "de"."""
    icd = Package(url="http://fhir.de/CodeSystem/bfarm/icd-10-gm", version="2026",
                  language="de-DE", concepts=[Concept("R18", "Aszites")])
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(icd)
        mention, = lexterm.tag("Kein Aszites.", store)
        assert [(a.code, a.system) for a in mention.assignments] == [("R18", icd.url)]
