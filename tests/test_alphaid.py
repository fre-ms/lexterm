# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The Alpha-ID-SE becomes packages.  The file here is invented: its numbers, codes and
wordings are no content of the Alpha-ID-SE or of the ICD-10-GM."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from lexcor import Concept, Package, PackageError

import lexterm
from lexterm.alphaid import ALPHA_ID, ICD_10_GM, ORPHA, SOURCE, read_alpha_id
from lexterm.cli import main
from lexterm.export import codeable_concepts

NAME = "alphaidse2027_edvtxt_20260925.txt"
LINES = [
    "1|I900001|X01.1||||77001|Musterfieber",
    "1|I900002|X02.0+|Y03.1*||||Mustermeningitis durch Musterfieber",
    "1|I900003|||Z09.9!|||Mustererreger als Ursache",
    "1|I900004|X01.1|||X05.2|77002|Musterfieber mit Musterschwäche ",
    "0|I900005|X01.9|||||Altes Musterleiden",
]


def data_file(folder: Path, name: str = NAME, encoding: str = "utf-8") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / name
    file.write_bytes(("\r\n".join(LINES) + "\r\n").encode(encoding))
    return file


def classification() -> Package:
    """An invented classification under the URL of the ICD-10-GM, as the BfArM writes one."""
    return Package(url=ICD_10_GM, version="2027", title="Invented classification",
                   language="de-DE", concepts=[
                       Concept("X01.1", "Fieber nach Art des Musters"),
                       Concept("X02.0", "Entzündung nach Art des Musters"),
                       Concept("Y03.1", "Entzündung bei anderenorts genanntem Muster")])


def test_the_file_becomes_the_alpha_id_and_two_supplements(tmp_path: Path) -> None:
    (alpha, icd, orpha), retired = read_alpha_id(data_file(tmp_path))
    assert retired == 1  # an entry kept for decoding old numbers is not one to code with
    assert (alpha.url, alpha.version, alpha.language, alpha.redistributable, alpha.copyright) \
        == (ALPHA_ID, "2027", "de", False, SOURCE)
    assert [(c.code, c.display, c.properties) for c in alpha.concepts] == [
        ("I900001", "Musterfieber", {"icd-10-gm-primary": "X01.1", "orpha": "77001"}),
        ("I900002", "Mustermeningitis durch Musterfieber",
         {"icd-10-gm-primary": "X02.0", "icd-10-gm-star": "Y03.1"}),
        ("I900003", "Mustererreger als Ursache", {"icd-10-gm-additional": "Z09.9"}),
        ("I900004", "Musterfieber mit Musterschwäche",
         {"icd-10-gm-primary": "X01.1", "icd-10-gm-primary-2": "X05.2", "orpha": "77002"})]
    # the wordings are further terms of the codes they are classified under: a supplement,
    # so that they never take the place of the classification itself
    assert (icd.url, icd.supplements, icd.version) == ("", f"{ICD_10_GM}|2027", "2027")
    assert (icd.title, orpha.title) == ("Alpha-ID-SE: Bezeichnungen zur ICD-10-GM",
                                        "Alpha-ID-SE: Bezeichnungen zu den ORPHAcodes")
    assert {c.code: [t.value for t in c.terms] for c in icd.concepts} == {
        "X01.1": ["Musterfieber", "Musterfieber mit Musterschwäche"],
        "X02.0": ["Mustermeningitis durch Musterfieber"],
        "X05.2": ["Musterfieber mit Musterschwäche"],
        "Y03.1": ["Mustermeningitis durch Musterfieber"],
        "Z09.9": ["Mustererreger als Ursache"]}
    assert (orpha.url, orpha.supplements) == ("", ORPHA)
    assert {c.code: [t.value for t in c.terms] for c in orpha.concepts} == {
        "77001": ["Musterfieber"], "77002": ["Musterfieber mit Musterschwäche"]}


def test_the_archive_is_read_as_it_was_downloaded(tmp_path: Path) -> None:
    file = tmp_path / "alphaidse2027.zip"
    with zipfile.ZipFile(file, "w") as archive:
        archive.writestr("alphaidse2027_edvtxt_liesmich.txt", "Liesmich " * 400)
        archive.writestr("downloadbedingungen.pdf", b"%PDF")
        archive.writestr(NAME, "\r\n".join(LINES) + "\r\n")
    assert read_alpha_id(file) == read_alpha_id(data_file(tmp_path / "unpacked"))
    assert sorted(p.name for p in tmp_path.iterdir()) == ["alphaidse2027.zip", "unpacked"]
    packages, _retired = read_alpha_id(data_file(tmp_path / "old", "alphaid.txt", "cp1252"))
    assert packages[0].version == "" and packages[1].supplements == ICD_10_GM  # no year named
    assert packages[0].concepts[3].display == "Musterfieber mit Musterschwäche"


def test_one_wording_is_coded_in_every_system_the_file_names(tmp_path: Path) -> None:
    packages, _retired = read_alpha_id(data_file(tmp_path))
    with lexterm.open_store(tmp_path / "store.sqlite") as store:
        store.add_package(classification())
        for package in packages:
            store.add_package(package)
        text = "Seit Jahren Musterfieber, zuletzt Mustermeningitis durch Musterfieber."
        fever, meningitis, inside = lexterm.tag(text, store)
        assert [(a.system, a.version, a.code, a.display) for a in fever.assignments] == [
            (ALPHA_ID, "2027", "I900001", "Musterfieber"),
            (ICD_10_GM, "2027", "X01.1", "Fieber nach Art des Musters"),
            (ORPHA, "", "77001", "")]
        assert [(a.system, a.code) for a in meningitis.assignments] == [  # dagger and star
            (ALPHA_ID, "I900002"), (ICD_10_GM, "X02.0"), (ICD_10_GM, "Y03.1")]
        # a system that knows only a shorter wording inside the longer one codes that
        assert (inside.text, [(a.system, a.code) for a in inside.assignments]) == (
            "Musterfieber", [(ORPHA, "77001")])
        document = lexterm.annotate(text, store)
        assert [document.confirm_all(system) for system in (ALPHA_ID, ICD_10_GM, ORPHA)] == [
            2, 3, 2]
        first = codeable_concepts(document)[0]["codeableConcept"]
        assert first["text"] == "Musterfieber"
        assert [(c["system"], c["code"]) for c in first["coding"]] == [
            (ALPHA_ID, "I900001"), (ICD_10_GM, "X01.1"), (ORPHA, "77001")]
        assert "display" not in first["coding"][2]  # no name is made up for a code


def test_the_command_takes_the_file_into_the_store(tmp_path: Path,
                                                   capsys: pytest.CaptureFixture[str]) -> None:
    store = str(tmp_path / "store.sqlite")
    assert main(["--language", "en", "alpha-id", str(data_file(tmp_path)), "--store",
                 store]) == 0
    said = capsys.readouterr().out
    assert "Taken in: Alpha-ID-SE, version 2027, with 4 codes in 4 wordings." in said
    assert f"Supplements {ICD_10_GM}." in said and "does not hold that code system" in said
    assert "Left out: 1 entries the file marks as no longer valid." in said
    with lexterm.open_store(store) as opened:
        opened.add_package(classification())
    assert main(["alpha-id", str(tmp_path / NAME), "--store", store, "--json"]) == 0
    answer = json.loads(capsys.readouterr().out)
    assert [p["concepts"] for p in answer["packages"]] == [4, 5, 2] and answer["retired"] == 1
    fits = {fit["system"]: fit for fit in answer["fit"].values()}
    assert fits[ICD_10_GM] == {"system": ICD_10_GM, "wanted": "2027", "held": "2027",
                               "unknown": 2}
    assert fits[ORPHA]["held"] is None
    with lexterm.open_store(store) as opened:  # read again, the file replaces itself
        assert len(opened.packages()) == 4


def test_what_is_no_file_of_the_alpha_id_is_refused(tmp_path: Path,
                                                    capsys: pytest.CaptureFixture[str]) -> None:
    other = tmp_path / "other.txt"
    other.write_text("1|I900001|X01.1||||77001|Musterfieber\nKein Eintrag\n", encoding="utf-8")
    with pytest.raises(PackageError) as refused:
        read_alpha_id(other)
    assert refused.value.kind == "not-alpha-id"
    assert "line 2" in refused.value.message("en") and "Kein Eintrag" not in str(refused.value)
    other.write_text("0|I900005|X01.9|||||Altes Musterleiden\n", encoding="utf-8")
    with pytest.raises(PackageError) as empty:
        read_alpha_id(other)
    assert empty.value.kind == "not-alpha-id"
    with zipfile.ZipFile(tmp_path / "empty.zip", "w") as archive:
        archive.writestr("liesmich.txt", "nothing else")
    with pytest.raises(PackageError) as hollow:
        read_alpha_id(tmp_path / "empty.zip")
    assert hollow.value.kind == "not-alpha-id"
    assert main(["alpha-id", str(tmp_path / "missing.zip"), "--store",
                 str(tmp_path / "store.sqlite"), "--json"]) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "unreadable"
    assert not (tmp_path / "store.sqlite").exists()  # nothing is opened for a file that fails


def test_the_file_can_be_taken_in_without_being_applied_yet(tmp_path: Path) -> None:
    store = str(tmp_path / "store.sqlite")
    assert main(["alpha-id", str(data_file(tmp_path)), "--store", store, "--off"]) == 0
    with lexterm.open_store(store) as opened:
        assert opened.chosen() == [] and len(opened.switched_off()) == 3
        assert lexterm.tag("Musterfieber", opened, opened.chosen()) == []
