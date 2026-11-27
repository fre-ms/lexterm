# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm: medical terms in German clinical text, with the codes of their terminologies.

    import lexterm

    with lexterm.open_store() as store:
        for mention in lexterm.tag("Bekannte arterielle Hypertonie, Ramipril seit 2019.", store):
            print(mention.text, [(a.system, a.code, a.cls) for a in mention.assignments])

lexterm brings no terminology of its own.  It recognises with the packages of a store
(:func:`open_store`): terminologies a person downloaded under their conditions and took in
(the ICD-10-GM, the Alpha-ID-SE, SNOMED CT, :mod:`lexterm.sources` says where they come
from), and lists of their own.  A program hands lexterm the store it means, so that what it
recognises with is never a store it did not name.

One wording is coded in every code system that knows it: a mention carries an assignment
from each package that lists its words.  What was found and what a person decided about it
is kept in an annotation document (:func:`annotate`), which a later run updates without
touching a decision; :mod:`lexterm.export` gives it as FHIR CodeableConcepts, one concept of
the text with a coding from every system.

Two questions are kept apart (design, section 5.3): :func:`tag` says which concepts a text
mentions and gives codes; :func:`covers` says whether a span is medical vocabulary at all,
generously, for a program that guesses at names and must leave such words alone.

lexterm is thin over lexcor, the core it shares with lexident: the packages, the store and
the matcher are the core's; the medical rules (``rules``) and the readers of terminologies
are lexterm's.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import lexcor
from lexcor import Annotation, Cover, Mention, Recogniser, Store
from lexcor.annotation import packages_of

from lexterm import export
from lexterm.rules import EPONYM_HEADS, VARIANTS

__version__ = "0.2.8"

__all__ = ["EPONYM_HEADS", "VARIANTS", "annotate", "cover", "covers", "export", "listing",
           "open_store", "recogniser", "tag"]


def open_store(path: str | Path | None = None, readonly: bool = False) -> Store:
    """Open lexterm's store: the file at ``path``, else the one in the user's data folder.
    ``readonly`` opens a store that exists and writes nothing."""
    return lexcor.open_store(path, "lexterm", readonly)


def _chosen(choice: Iterable[str] | None) -> tuple[str, ...] | None:
    return None if choice is None else tuple(sorted(choice))


def recogniser(store: Store, packages: Iterable[str] | None = None,
               classes: Iterable[str] | None = None, language: str = "de") -> Recogniser:
    """The recogniser over a choice of the packages of a store (their URLs; all when None)
    and of classes, built once and again only when the store has changed.  Only terms in
    the language of the text are looked for: English names in a German letter tag "gut"
    and "fast"."""
    return lexcor.recogniser(store, packages, classes, VARIANTS, language, (language,))


def tag(text: str, store: Store, packages: Iterable[str] | None = None,
        classes: Iterable[str] | None = None, language: str = "de",
        nested: bool = False) -> list[Mention]:
    """Which concepts does this text mention?  Every mention has its place in the text (in
    code points) and one assignment for each concept its words may mean, each with the
    package, the code, the class and the kind of the match.  Every package answers for
    itself: a mention carries an assignment from each package that lists its words, and a
    package that knows only a shorter wording inside a longer mention codes that, so that
    mentions may overlap.  ``nested`` asks for a package's own shorter terms inside its
    longer ones as well.  A store without packages finds nothing."""
    return recogniser(store, packages, classes, language).tag(text, nested)


def listing(store: Store, packages: Iterable[str] | None = None) -> list[dict[str, str]]:
    """The packages a run applies, as an annotation document names them: each with its
    version and the fingerprints of its content and of the user's changes to it.  A program
    that keeps a record of its own (a step of a pipeline, a configuration document) takes it
    from here."""
    return packages_of(store, _chosen(packages))


def annotate(text: str, store: Store, packages: Iterable[str] | None = None,
             classes: Iterable[str] | None = None, language: str = "de",
             annotation: Annotation | None = None, nested: bool = False) -> Annotation:
    """Tag a text and give its annotation document: a new one, or the one handed in brought
    up to date.  What a person confirmed, rejected or marked in it stays; only what lexterm
    proposed before and nobody has decided is replaced.  The document names the packages
    the run applied (:func:`listing`), so that it says what it was made from."""
    found = tag(text, store, packages, classes, language, nested)
    wanted = _chosen(packages)
    name = f"lexterm {__version__}"
    settings = {"packages": list(wanted or ()), "classes": list(_chosen(classes) or ()),
                "language": language, "nested": nested}
    return (annotation or Annotation()).update(text, found, name, name,
                                               listing(store, wanted), settings)


def cover(store: Store, packages: Iterable[str] | None = None,
          classes: Iterable[str] | None = None, language: str = "de") -> Cover:
    """The medical vocabulary of a store as one set of words and phrases, for the generous
    question."""
    return lexcor.cover(store, packages, classes, EPONYM_HEADS, (language,))


def covers(text: str, start: int, end: int, store: Store, whole: bool = False) -> bool:
    """Is ``text[start:end]`` medical vocabulary of a store?  A part of a hyphenated word
    counts ("Parkinson-Syndrom"), as does an eponym on its own ("Babinski").  With ``whole``
    every word of the span must be vocabulary."""
    return cover(store).covers(text, start, end, whole=whole)
