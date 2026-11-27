# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line: the core's commands under lexterm's name, with lexterm's rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lexterm.cli import main

OWN = "https://example.org/CodeSystem/own"


@pytest.fixture
def files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LEXCOR_DATA", str(tmp_path / "data"))
    (tmp_path / "letter.txt").write_text("Kolitis ulzerosa, Ramipril seit 2019.", encoding="utf-8")
    (tmp_path / "own.csv").write_text("term,code,class\nColitis ulcerosa,K51,disorder\n",
                                      encoding="utf-8")
    return tmp_path


def test_a_store_without_a_terminology_says_where_to_get_one(
        files: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "tag", str(files / "letter.txt")]) == 1
    refused = json.loads(capsys.readouterr().out)
    assert refused["error"] == "no-terminology" and "lexterm sources" in refused["message"]["en"]
    assert (files / "data" / "lexterm.sqlite").exists()  # lexterm's own store, not the core's


def test_a_users_package_is_tagged_with_lexterms_spellings(
        files: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["packages", "import", str(files / "own.csv"), "--term-language", "de"]) == 0
    capsys.readouterr()
    assert main(["--json", "tag", str(files / "letter.txt")]) == 0
    mention, = json.loads(capsys.readouterr().out)["mentions"]
    assert (mention["exact"], mention["assignments"][0]["code"],
            mention["assignments"][0]["match"]) == ("Kolitis ulzerosa", "K51",
                                                    {"kind": "spelling variant"})
    with pytest.raises(SystemExit):
        main(["--help"])
    assert "usage: lexterm" in capsys.readouterr().out


def test_the_command_line_writes_the_annotation_document(
        files: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import lexterm

    target = files / "letter.lexterm.json"
    assert main(["packages", "import", str(files / "own.csv"), "--term-language", "de"]) == 0
    assert main(["tag", str(files / "letter.txt"), "--annotation", str(target)]) == 0
    capsys.readouterr()
    document = json.loads(target.read_text(encoding="utf-8"))
    assert document["lexcor"] == 1 and document["made_with"] == f"lexterm {lexterm.__version__}"
    assert "Kolitis ulzerosa" in [m["exact"] for m in document["mentions"]]


def test_the_command_line_gives_codeable_concepts(
        files: Path, capsys: pytest.CaptureFixture[str]) -> None:
    from lexcor import load_annotation

    target = files / "letter.lexterm.json"
    assert main(["packages", "import", str(files / "own.csv"), "--url", OWN,
                 "--term-language", "de"]) == 0
    assert main(["tag", str(files / "letter.txt"), "--annotation", str(target)]) == 0
    capsys.readouterr()
    assert main(["export", "fhir", str(target)]) == 0
    assert json.loads(capsys.readouterr().out) == {"concepts": []}  # nothing confirmed yet
    document = load_annotation(target)
    document.confirm_all(OWN)
    document.save(target)
    assert main(["export", "fhir", str(target)]) == 0
    concepts = json.loads(capsys.readouterr().out)["concepts"]
    assert "Kolitis ulzerosa" in [c["codeableConcept"]["text"] for c in concepts]
    assert all(c["codeableConcept"]["coding"][0]["userSelected"] for c in concepts)
    assert main(["--language", "en", "export", "fhir", str(files / "missing.json")]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "unreadable"


def test_the_command_line_says_where_terminologies_come_from(
        capsys: pytest.CaptureFixture[str]) -> None:
    from lexterm import sources

    assert main(["--language", "de", "sources"]) == 0
    german = capsys.readouterr().out
    assert "SNOMED CT, deutsche National Edition" in german and "Affiliate-Lizenz" in german
    assert "https://mlds.ihtsdotools.org/" in german
    assert "lexterm snomed SnomedCT_Germany-EditionRelease" in german
    assert main(["--language", "en", "sources", "--json"]) == 0
    listed = json.loads(capsys.readouterr().out)["sources"]
    assert [s["key"] for s in listed] == ["bfarm", "alpha-id", "snomed"]
    assert listed[0]["name"] == "Coding systems of the BfArM"
    for source in sources.SOURCES:  # both languages everywhere, and real addresses
        assert all(source.name) and all(source.what) and all(source.conditions)
        assert source.steps and all(all(step) for step in source.steps)
        assert all(all(label) and url.startswith("https://") for label, url in source.links)


def test_the_documentation_names_every_source_the_program_names() -> None:
    from pathlib import Path as Folder

    from lexterm import sources

    page = (Folder(__file__).parent.parent / "docs" / "terminologies.md").read_text("utf-8")
    for source in sources.sources("en"):
        assert source["name"] in page and source["command"] in page
        assert all(link["url"] in page for link in source["links"])
