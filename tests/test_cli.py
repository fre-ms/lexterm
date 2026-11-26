# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line: the core's commands under lexterm's name, with lexterm's rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lexterm import bundled
from lexterm.cli import main


@pytest.fixture
def files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("LEXCOR_DATA", str(tmp_path / "data"))
    (tmp_path / "letter.txt").write_text("Kolitis ulzerosa, Ramipril seit 2019.", encoding="utf-8")
    (tmp_path / "own.csv").write_text("term,code,class\nColitis ulcerosa,K51,disorder\n",
                                      encoding="utf-8")
    return tmp_path


def test_a_store_without_packages_answers_from_what_lexterm_brings(
        files: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--json", "tag", str(files / "letter.txt")]) == 0
    mentions = json.loads(capsys.readouterr().out)["mentions"]
    assert "Ramipril" in [m["exact"] for m in mentions]
    assert {a["system"] for m in mentions for a in m["assignments"]} == {bundled.WIKIDATA}
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
    assert main(["tag", str(files / "letter.txt"), "--annotation", str(target)]) == 0
    capsys.readouterr()
    document = json.loads(target.read_text(encoding="utf-8"))
    assert document["lexcor"] == 1 and document["made_with"] == f"lexterm {lexterm.__version__}"
    assert "Ramipril" in [m["exact"] for m in document["mentions"]]
