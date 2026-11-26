# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line of lexterm: the core's commands under lexterm's name.

    lexterm packages list | import FILE | export PACKAGE FILE | remove PACKAGE
    lexterm tag FILE [--package PACKAGE]... [--class CLASS]... [--nested] [--annotation FILE]
    lexterm export fhir ANNOTATION [--all] [--apart]

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


def main(arguments: Sequence[str] | None = None) -> int:
    """Run one command; returns the exit code."""
    given = list(sys.argv[1:] if arguments is None else arguments)
    for i, word in enumerate(given[:-1]):
        if word == "--language" and given[i + 1] in ("de", "en"):
            set_language(given[i + 1])
    if "export" in given and (given.index("export") == 0 or given[0].startswith("--")):
        return _export(given[given.index("export") + 1:])
    arguments = given
    return lexcor.cli.main(arguments, program="lexterm", library="lexterm", tagger=_tag,
                           version=lexterm.__version__)


if __name__ == "__main__":
    raise SystemExit(main())
