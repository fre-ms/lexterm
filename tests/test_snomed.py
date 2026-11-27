# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""A release of SNOMED CT (RF2) becomes a package.  The release here is invented: its
numbers and terms are no content of SNOMED CT."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from lexcor import PackageError

import lexterm
from lexterm.cli import main
from lexterm.snomed import SNOMED, read_rf2

FSN, SYNONYM = "900000000000003001", "900000000000013009"
PREFERRED, ACCEPTABLE = "900000000000548007", "900000000000549004"


def release(folder: Path) -> Path:
    """An invented release in the layout of a national edition."""
    def write(path: str, header: str, rows: list[tuple[str, ...]]) -> None:
        file = folder / "Snapshot" / path
        file.parent.mkdir(parents=True, exist_ok=True)
        lines = [header.replace(" ", "\t")] + ["\t".join(row) for row in rows]
        file.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8", newline="")

    write("Terminology/sct2_Concept_Snapshot_XX1000999_20261115.txt",
          "id effectiveTime active moduleId definitionStatusId",
          [("9001", "20260101", "1", "77", "x"), ("9002", "20260101", "1", "77", "x"),
           ("9003", "20260101", "0", "77", "x"), ("9004", "20260101", "1", "77", "x")])
    head = "id effectiveTime active moduleId conceptId languageCode typeId term caseSignificanceId"
    write("Terminology/sct2_Description_Snapshot-en_XX1000999_20261115.txt", head, [
        ("1", "20260101", "1", "77", "9001", "en", FSN, "Sample disease (disorder)", "c"),
        ("2", "20260101", "1", "77", "9001", "en", SYNONYM, "Sample disease", "c"),
        ("3", "20260101", "1", "77", "9002", "en", FSN, "Sample cut (procedure)", "c"),
        ("4", "20260101", "1", "77", "9004", "en", FSN, "Sample thing (substance)", "c"),
        ("5", "20260101", "1", "77", "9004", "en", SYNONYM, "Sample thing", "c")])
    write("Terminology/sct2_Description_Snapshot-de_XX1000999_20261115.txt", head, [
        ("11", "20260101", "1", "88", "9001", "de", SYNONYM, "Mustersyndrom", "c"),
        ("12", "20260101", "1", "88", "9001", "de", SYNONYM, "Musterkrankheit", "c"),
        ("13", "20260101", "0", "88", "9001", "de", SYNONYM, "Altes Musterleiden", "c"),
        ("14", "20260101", "1", "88", "9002", "de", SYNONYM, "Musterschnitt", "c"),
        ("15", "20260101", "1", "88", "9003", "de", SYNONYM, "Stillgelegtes Muster", "c")])
    write("Refset/Language/der2_cRefset_LanguageSnapshot-de_XX1000999_20261115.txt",
          "id effectiveTime active moduleId refsetId referencedComponentId acceptabilityId",
          [("a", "20260101", "1", "88", "r", "12", PREFERRED),
           ("b", "20260101", "1", "88", "r", "11", ACCEPTABLE),
           ("c", "20260101", "1", "88", "r", "14", PREFERRED)])
    return folder


def test_a_release_becomes_a_package_of_the_german_terms(tmp_path: Path) -> None:
    package = read_rf2(release(tmp_path / "edition"))
    assert (package.url, package.redistributable, package.language) == (SNOMED, False, "de")
    assert package.version == f"{SNOMED}/88/version/20261115"
    assert [(c.code, c.display, c.cls, [(t.value, t.kind) for t in c.terms])
            for c in package.concepts] == [
        ("9001", "Musterkrankheit", "disorder",
         [("Musterkrankheit", "preferred"), ("Mustersyndrom", "synonym")]),
        ("9002", "Musterschnitt", "procedure", [("Musterschnitt", "preferred")])]
    # the retired concept, the retired description and the concept without a German term are out
    both = read_rf2(tmp_path / "edition", ("de", "en"))
    assert [c.code for c in both.concepts] == ["9001", "9002", "9004"]
    assert [(t.value, t.language) for t in both.concepts[0].terms] == [
        ("Musterkrankheit", "de"), ("Mustersyndrom", "de"), ("Sample disease", "en")]
    assert both.concepts[2].display == "Sample thing"
    with pytest.raises(PackageError) as none:
        read_rf2(tmp_path / "nothing here")
    assert none.value.kind == "not-a-release"


def test_the_command_takes_a_release_into_the_store(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    store = tmp_path / "lexterm.sqlite"
    assert main(["snomed", str(release(tmp_path / "edition")), "--store", str(store),
                 "--json"]) == 0
    info = json.loads(capsys.readouterr().out)["package"]
    assert (info["url"], info["concepts"], info["terms"], info["redistributable"]) == (
        SNOMED, 2, 3, False)
    with lexterm.open_store(store, readonly=True) as opened:
        mention, = lexterm.tag("Bekanntes Mustersyndrom.", opened)
        assert [(a.system, a.code, a.cls) for a in mention.assignments] == [
            (SNOMED, "9001", "disorder")]
    assert main(["--language", "en", "snomed", str(tmp_path / "empty"), "--store",
                 str(store)]) == 1
    assert "no SNOMED CT release" in capsys.readouterr().err
