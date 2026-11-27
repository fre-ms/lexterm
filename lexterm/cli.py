# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line of lexterm: the core's commands under lexterm's name.

    lexterm packages list | import FILE | export PACKAGE FILE | remove PACKAGE
    lexterm packages on PACKAGE... | off PACKAGE... | window
    lexterm tag FILE [--package PACKAGE]... [--without PACKAGE]... [--class CLASS]... [--nested]
                     [--annotation FILE [--repeat]]
    lexterm export fhir ANNOTATION [--all] [--apart] [--terminal-codes]
    lexterm snomed RELEASE [--term-language LANGUAGE]... [--store FILE] [--off]
    lexterm alpha-id FILE [--store FILE] [--off]
    lexterm sources [--json]

The store is lexterm's in the user's data folder unless ``--store`` names another.  lexterm
brings no terminology: a store that holds none yet says so when a text is to be tagged, and
``lexterm sources`` says where terminologies come from.  What is taken in is ticked, so that
it is applied, unless it is taken in with ``--off``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path

import lexcor.cli
from lexcor import LexError, Mention, Store, load_annotation, say, set_language
from lexcor.annotation import STATUSES

import lexterm
from lexterm.export import codeable_concepts


def _tag(text: str, store: Store, packages: Iterable[str] | None,
         classes: Iterable[str] | None, nested: bool) -> list[Mention]:
    if not store.packages():
        raise LexError(
            "no-terminology",
            "Die Ablage enthält noch keine Terminologie. lexterm bringt keine mit; woher man"
            " sie bekommt, sagt „lexterm sources“.",
            "The store holds no terminology yet. lexterm brings none; \"lexterm sources\""
            " says where to get them.")
    return lexterm.tag(text, store, packages, classes, nested=nested)


def _window(store: Store) -> int:
    from lexterm.window import open_window

    return open_window(store)


def _export(arguments: list[str]) -> int:
    """``lexterm export fhir ANNOTATION``: the CodeableConcepts of an annotation document as
    one JSON document on standard output."""
    parser = argparse.ArgumentParser(prog="lexterm export", description=say(
        "Ein Annotationsdokument in der Form ausgeben, die andere Programme übernehmen.",
        "Give an annotation document in the form other programs take."))
    parser.add_argument("form", choices=("fhir",))
    parser.add_argument("annotation", type=Path)
    parser.add_argument("--all", action="store_true", help=say(
        "auch Vorschläge und Verworfenes, nicht nur Bestätigtes",
        "proposals and rejections as well, not only what was confirmed"))
    parser.add_argument("--apart", action="store_true", help=say(
        "je Zuordnung ein eigenes CodeableConcept statt eines je Fundstelle",
        "a CodeableConcept for every assignment instead of one for every mention"))
    parser.add_argument("--terminal-codes", action="store_true", help=say(
        "nur endständige Kodes einer Klassifikation (bei der ICD-10-GM die Kodes, mit denen"
        " verschlüsselt wird); Kodes eines Systems ohne Hierarchie bleiben",
        "terminal codes of a classification only (for the ICD-10-GM the codes one codes"
        " with); codes of a system without a hierarchy stay"))
    args = parser.parse_args(arguments)
    try:
        document = load_annotation(args.annotation)
    except (LexError, OSError, UnicodeDecodeError) as error:
        if not isinstance(error, LexError):
            error = LexError("unreadable", str(error), str(error))
        print(json.dumps({"error": error.kind, "message": error.messages}, ensure_ascii=False))
        return 1
    statuses = STATUSES if args.all else ("confirmed",)
    print(json.dumps({"concepts": codeable_concepts(document, statuses, not args.apart,
                                                    args.terminal_codes)},
                     ensure_ascii=False, indent=1))
    return 0


def _snomed(arguments: list[str]) -> int:
    """``lexterm snomed RELEASE``: take a release of SNOMED CT (RF2) into lexterm's store."""
    from lexterm.snomed import read_rf2

    parser = argparse.ArgumentParser(prog="lexterm snomed", description=say(
        "Eine SNOMED-CT-Ausgabe (RF2: die ZIP-Datei, wie sie geladen wurde, oder der Ordner,"
        " zu dem sie entpackt wurde) in die eigene Ablage aufnehmen. SNOMED CT ist"
        " lizenzpflichtig; das Paket bleibt bei Ihnen. Woher die Ausgabe kommt, sagt"
        " „lexterm sources“.",
        "Take a release of SNOMED CT (RF2: the ZIP file as it was downloaded, or the folder it"
        " was unpacked to) into your own store. SNOMED CT needs a licence; the package stays"
        " with you. \"lexterm sources\" says where the release comes from."))
    parser.add_argument("release", type=Path)
    parser.add_argument("--off", action="store_true", help=say(
        "aufnehmen, aber noch nicht anwenden (nicht angekreuzt)",
        "take in, but do not apply yet (unticked)"))
    parser.add_argument("--term-language", action="append", metavar="LANGUAGE", help=say(
        "Sprache der Begriffe (mehrfach möglich; Standard: de)",
        "language of the terms (may be given several times; default: de)"))
    parser.add_argument("--store", type=Path, help=say(
        "Datei der Ablage (sonst lexterms Ablage im Datenordner)",
        "file of the store (else lexterm's store in the data folder)"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    try:
        package = read_rf2(args.release, tuple(args.term_language or ["de"]))
        with lexterm.open_store(args.store) as store:
            info = store.add_package(package, False if args.off else None)
    except (LexError, OSError, UnicodeDecodeError) as error:
        if not isinstance(error, LexError):
            error = LexError("unreadable", str(error), str(error))
        print(json.dumps({"error": error.kind, "message": error.messages}, ensure_ascii=False)
              if args.json else str(error), file=sys.stdout if args.json else sys.stderr)
        return 1
    print(json.dumps({"package": vars(info)}, ensure_ascii=False, indent=1) if args.json else say(
        f"Aufgenommen: {info.title}, Fassung {info.version}, mit {info.concepts} Begriffen in"
        f" {info.terms} Schreibweisen. Nicht weitergebbar.",
        f"Taken in: {info.title}, version {info.version}, with {info.concepts} concepts in"
        f" {info.terms} wordings. Not to be passed on."))
    return 0


def _alpha_id(arguments: list[str]) -> int:
    """``lexterm alpha-id FILE``: take the Alpha-ID-SE of the BfArM into lexterm's store."""
    from lexterm.alphaid import read_alpha_id

    parser = argparse.ArgumentParser(prog="lexterm alpha-id", description=say(
        "Die Alpha-ID-SE des BfArM in die eigene Ablage aufnehmen: die Datei, wie sie geladen"
        " wurde (ZIP), oder die Datendatei darin. Es entstehen die Alpha-ID als CodeSystem und"
        " ihre Bezeichnungen als Ergänzung zur ICD-10-GM und zu den ORPHAcodes. Woher die Datei"
        " kommt, sagt „lexterm sources“.",
        "Take the Alpha-ID-SE of the BfArM into your own store: the file as downloaded (ZIP)"
        " or the data file in it. The Alpha-ID comes as a code system, and its wordings as a"
        " supplement to the ICD-10-GM and to the ORPHAcodes. \"lexterm sources\" says where"
        " the file comes from."))
    parser.add_argument("file", type=Path)
    parser.add_argument("--off", action="store_true", help=say(
        "aufnehmen, aber noch nicht anwenden (nicht angekreuzt)",
        "take in, but do not apply yet (unticked)"))
    parser.add_argument("--store", type=Path, help=say(
        "Datei der Ablage (sonst lexterms Ablage im Datenordner)",
        "file of the store (else lexterm's store in the data folder)"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    try:
        packages, retired = read_alpha_id(args.file)
        with lexterm.open_store(args.store) as store:
            infos = [store.add_package(package, False if args.off else None)
                     for package in packages]
            fits = [lexcor.cli.fit_notes(store, info) for info in infos]
    except (LexError, OSError) as error:
        if not isinstance(error, LexError):
            error = LexError("unreadable", str(error), str(error))
        print(json.dumps({"error": error.kind, "message": error.messages}, ensure_ascii=False)
              if args.json else str(error), file=sys.stdout if args.json else sys.stderr)
        return 1
    lines = []
    for info, (_fit, notes) in zip(infos, fits, strict=True):
        lines.append(say(
            f"Aufgenommen: {info.title}, Fassung {info.version}, mit {info.concepts} Kodes in"
            f" {info.terms} Bezeichnungen.",
            f"Taken in: {info.title}, version {info.version}, with {info.concepts} codes in"
            f" {info.terms} wordings."))
        lines += [f"  {note}" for note in notes]
    lines.append(say(f"Ausgelassen: {retired} Einträge, die die Datei als nicht mehr gültig"
                     " kennzeichnet.",
                     f"Left out: {retired} entries the file marks as no longer valid."))
    document = {"packages": [vars(info) for info in infos], "retired": retired,
                "fit": {info.url: fit for info, (fit, _notes) in zip(infos, fits, strict=True)
                        if fit is not None}}
    print(json.dumps(document, ensure_ascii=False, indent=1) if args.json else "\n".join(lines))
    return 0


def _sources(arguments: list[str]) -> int:
    """``lexterm sources``: where terminologies come from and how they are taken in."""
    from lexterm import sources

    parser = argparse.ArgumentParser(prog="lexterm sources", description=say(
        "Woher Terminologien kommen: was es gibt, unter welchen Bedingungen, und wie lexterm"
        " es aufnimmt. lexterm lädt nichts selbst.",
        "Where terminologies come from: what there is, under which conditions, and how"
        " lexterm takes it in. lexterm downloads nothing itself."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    print(json.dumps({"sources": sources.sources()}, ensure_ascii=False, indent=1)
          if args.json else sources.text())
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Run one command; returns the exit code."""
    given = list(sys.argv[1:] if arguments is None else arguments)
    for i, word in enumerate(given[:-1]):
        if word == "--language" and given[i + 1] in ("de", "en"):
            set_language(given[i + 1])
    own = {"export": _export, "snomed": _snomed, "alpha-id": _alpha_id, "sources": _sources}
    for word, command in own.items():
        if word in given and (given.index(word) == 0 or given[0].startswith("--")):
            return command(given[given.index(word) + 1:])
    arguments = given
    return lexcor.cli.main(arguments, program="lexterm", library="lexterm", tagger=_tag,
                           version=lexterm.__version__, window=_window)


if __name__ == "__main__":
    raise SystemExit(main())
