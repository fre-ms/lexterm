# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line of lexterm: the core's commands under lexterm's name.

    lexterm packages list | import FILE | export PACKAGE FILE | remove PACKAGE
    lexterm tag FILE [--package PACKAGE]... [--class CLASS]... [--nested] [--annotation FILE]
    lexterm export fhir ANNOTATION [--all] [--apart]
    lexterm snomed FOLDER [--term-language LANGUAGE]... [--store FILE]
    lexterm sources [--json]

The store is lexterm's in the user's data folder unless ``--store`` names another.  A store
that holds no package yet is answered from the packages that come with lexterm, so that
``lexterm tag`` works from the first call.
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
    return lexterm.tag(text, store if store.packages() else None, packages, classes,
                       nested=nested)


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
    args = parser.parse_args(arguments)
    try:
        document = load_annotation(args.annotation)
    except (LexError, OSError, UnicodeDecodeError) as error:
        if not isinstance(error, LexError):
            error = LexError("unreadable", str(error), str(error))
        print(json.dumps({"error": error.kind, "message": error.messages}, ensure_ascii=False))
        return 1
    statuses = STATUSES if args.all else ("confirmed",)
    print(json.dumps({"concepts": codeable_concepts(document, statuses, not args.apart)},
                     ensure_ascii=False, indent=1))
    return 0


def _snomed(arguments: list[str]) -> int:
    """``lexterm snomed FOLDER``: take a release of SNOMED CT (RF2) into lexterm's store."""
    from lexterm.snomed import read_rf2

    parser = argparse.ArgumentParser(prog="lexterm snomed", description=say(
        "Eine SNOMED-CT-Ausgabe (RF2, Ordner der entpackten Ausgabe) in die eigene Ablage"
        " aufnehmen. SNOMED CT ist lizenzpflichtig; das Paket bleibt bei Ihnen. Woher die"
        " Ausgabe kommt, sagt „lexterm sources“.",
        "Take a release of SNOMED CT (RF2, the folder of the unpacked release) into your own"
        " store. SNOMED CT needs a licence; the package stays with you. \"lexterm sources\""
        " says where the release comes from."))
    parser.add_argument("folder", type=Path)
    parser.add_argument("--term-language", action="append", metavar="LANGUAGE", help=say(
        "Sprache der Begriffe (mehrfach möglich; Standard: de)",
        "language of the terms (may be given several times; default: de)"))
    parser.add_argument("--store", type=Path, help=say(
        "Datei der Ablage (sonst lexterms Ablage im Datenordner)",
        "file of the store (else lexterm's store in the data folder)"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(arguments)
    try:
        package = read_rf2(args.folder, tuple(args.term_language or ["de"]))
        with lexterm.open_store(args.store) as store:
            info = store.add_package(package)
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
    own = {"export": _export, "snomed": _snomed, "sources": _sources}
    for word, command in own.items():
        if word in given and (given.index(word) == 0 or given[0].startswith("--")):
            return command(given[given.index(word) + 1:])
    arguments = given
    return lexcor.cli.main(arguments, program="lexterm", library="lexterm", tagger=_tag,
                           version=lexterm.__version__)


if __name__ == "__main__":
    raise SystemExit(main())
