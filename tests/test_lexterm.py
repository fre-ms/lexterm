# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm as a library: the packages it brings, tagging with and without a store, the cover."""

from __future__ import annotations

import gzip
import subprocess
import sys
from importlib import resources
from pathlib import Path

import pytest
from lexcor import Concept, Kind, Package, Term

import lexterm
from lexterm import bundled

URL = "https://example.org/CodeSystem/sample"


def sample() -> Package:
    return Package(url=URL, version="1", title="Sample", language="de", concepts=[
        Concept("K51", "Colitis ulcerosa", "disorder", "", [Term("Colitis ulcerosa", "de")]),
        Concept("E1", "Babinski-Zeichen", "sign", "", [Term("Babinski-Zeichen", "de")]),
        Concept("X1", "fast", "other", "", [Term("fast", "en")]),
        Concept("M1", "Ramipril", "drug", "", [Term("Ramipril", "de")])])


def test_the_package_that_comes_with_lexterm_is_wikidatas() -> None:
    package = bundled.wikidata()
    assert bundled.packages() == (package,)
    assert (package.url, package.version) == (bundled.WIKIDATA, bundled.WIKIDATA_VERSION)
    assert package.redistributable and package.copyright.startswith("CC0 1.0")
    assert len(package.concepts) > 17_000 and package.term_count > 39_000
    assert {c.cls for c in package.concepts} <= set(bundled.PRIORITY)
    assert all(c.code[0] == "Q" and c.code[1:].isdigit() for c in package.concepts)
    source = resources.files("lexterm").joinpath("data", "wikidata_medical_de.csv.gz")
    with source.open("rb") as raw, gzip.open(raw, "rt", encoding="utf-8") as file:
        first = file.readline()
    assert f"fetched {bundled.WIKIDATA_VERSION}" in first and "CC0 1.0" in first
    ramipril = next(c for c in package.concepts if c.display == "Ramipril")
    assert ramipril.cls == "drug"  # Wikidata lists it as a drug and as a substance


def test_a_text_is_tagged_with_nothing_but_what_lexterm_brings() -> None:
    text = "Bekannte arterielle Hypertonie, Ramipril seit 2019."
    found = lexterm.tag(text)
    assert [m.text for m in found] == ["arterielle Hypertonie", "Ramipril"]
    assert [(m.start, m.end) for m in found] == [(9, 30), (32, 40)]
    assignment = found[1].assignments[0]
    assert (assignment.system, assignment.version, assignment.cls, assignment.kind) == (
        bundled.WIKIDATA, bundled.WIKIDATA_VERSION, "drug", Kind.AS_WRITTEN)
    assert assignment.code.startswith("Q")
    assert [m.text for m in lexterm.tag(text, classes=["drug"])] == ["Ramipril"]
    assert lexterm.tag(text, packages=["https://example.org/none"]) == []
    assert lexterm.recogniser() is lexterm.recogniser()  # built once


def test_with_a_store_its_packages_decide(tmp_path: Path) -> None:
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(sample())
        text = "Kolitis ulzerosa, Ramiprils Wirkung fast aufgehoben, Hypertonie."
        found = lexterm.tag(text, store)
        # lexterm's table of spellings; German terms only; nothing from the bundled package
        assert [(m.text, m.assignments[0].code, m.assignments[0].kind) for m in found] == [
            ("Kolitis ulzerosa", "K51", Kind.VARIANT), ("Ramiprils", "M1", Kind.INFLECTED)]
        assert [m.text for m in lexterm.tag(text, store, language="en")] == ["fast"]
        taken = lexterm.install(store)
        assert [info.url for info in taken] == [bundled.WIKIDATA]
        assert lexterm.install(store) == []  # there already, in this version
        assert "Hypertonie" in [m.text for m in lexterm.tag(text, store)]
        store.hide(URL, "M1")
        assert "Ramiprils" not in [m.text for m in lexterm.tag(text, store, packages=[URL])]
    with lexterm.open_store(tmp_path / "lexterm.sqlite", readonly=True) as store:
        assert "Hypertonie" in [m.text for m in lexterm.tag("Hypertonie", store)]


def test_the_generous_question(tmp_path: Path) -> None:
    text = "Babinski positiv, Parkinson-Syndrom bei Herrn Flantz."
    assert lexterm.covers(text, 0, 8)                       # an eponym on its own
    assert lexterm.covers(text, text.index("Parkinson"), text.index("bei") - 1, whole=True)
    start = text.index("Flantz")
    assert not lexterm.covers(text, start, start + 6)
    assert lexterm.cover().is_term("Hypertonien")
    with lexterm.open_store(tmp_path / "lexterm.sqlite") as store:
        store.add_package(sample())
        assert lexterm.covers(text, 0, 8, store)            # by lexterm's head nouns
        assert not lexterm.covers(text, text.index("Parkinson"), text.index("bei") - 1, store)


def test_tagging_without_a_store_writes_nothing(tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("HOME", "LEXCOR_DATA", "XDG_DATA_HOME", "APPDATA", "TMPDIR"):
        monkeypatch.setenv(name, str(tmp_path))
    assert lexterm.tag("Diabetes mellitus") and lexterm.covers("Hypertonie", 0, 10)
    assert list(tmp_path.iterdir()) == []


def test_importing_lexterm_loads_no_package() -> None:
    script = ("import lexterm, sys; from lexterm import bundled;"
              "sys.exit(bundled.wikidata.cache_info().currsize)")
    assert subprocess.run([sys.executable, "-c", script], check=False).returncode == 0
