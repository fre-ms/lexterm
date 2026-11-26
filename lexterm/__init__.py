# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm: medical terms in German clinical text, with the codes of their terminologies.

    import lexterm

    for mention in lexterm.tag("Bekannte arterielle Hypertonie, Ramipril seit 2019."):
        print(mention.text, [(a.system, a.code, a.cls) for a in mention.assignments])

Without a store lexterm recognises with the free packages it brings, in memory, and writes
nothing anywhere.  With a store (:func:`open_store`) it recognises with the packages of that
store: the ones a user imported, edited or built from a source they hold a licence for;
:func:`install` puts the free packages into a store as well.

Two questions are kept apart (design, section 5.3): :func:`tag` says which concepts a text
mentions and gives codes; :func:`covers` says whether a span is medical vocabulary at all,
generously, for a program that guesses at names and must leave such words alone.

lexterm is thin over lexcor, the core it shares with lexident: the packages, the store and
the matcher are the core's; the medical rules (``rules``) and the packages are lexterm's.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import cache
from pathlib import Path

import lexcor
from lexcor import Cover, Mention, PackageInfo, Recogniser, Store, entries_of

from lexterm import bundled
from lexterm.rules import EPONYM_HEADS, VARIANTS

__version__ = "0.1.0"

__all__ = ["EPONYM_HEADS", "VARIANTS", "bundled", "cover", "covers", "install", "open_store",
           "recogniser", "tag"]

Choice = tuple[str, ...] | None


def open_store(path: str | Path | None = None, readonly: bool = False) -> Store:
    """Open lexterm's store: the file at ``path``, else the one in the user's data folder.
    ``readonly`` opens a store that exists and writes nothing."""
    return lexcor.open_store(path, "lexterm", readonly)


def install(store: Store) -> list[PackageInfo]:
    """Put the packages that come with lexterm into a store, where a user can edit them; one
    that is there already in the same version is left as it is."""
    held = {info.url: info for info in store.packages()}
    taken = []
    for package in bundled.packages():
        known = held.get(package.url)
        if known is None or known.sha256 != package.sha256():
            taken.append(store.add_package(package))
    return taken


def _chosen(choice: Iterable[str] | None) -> Choice:
    return None if choice is None else tuple(sorted(choice))


@cache
def _bundled_recogniser(packages: Choice, classes: Choice, language: str) -> Recogniser:
    chosen = [p for p in bundled.packages() if packages is None or p.url in packages]
    return Recogniser(entries_of(chosen, classes, (language,)), VARIANTS, language)


@cache
def _bundled_cover(packages: Choice, classes: Choice, language: str) -> Cover:
    chosen = [p for p in bundled.packages() if packages is None or p.url in packages]
    return Cover((e.term for e in entries_of(chosen, classes, (language,))), EPONYM_HEADS)


def recogniser(store: Store | None = None, packages: Iterable[str] | None = None,
               classes: Iterable[str] | None = None, language: str = "de") -> Recogniser:
    """The recogniser for a choice of packages (their URLs) and classes: over the packages of
    a store, or without one over those that come with lexterm.  It is built once.  Only terms
    in the language of the text are looked for: English names in a German letter tag "gut"
    and "fast"."""
    if store is None:
        return _bundled_recogniser(_chosen(packages), _chosen(classes), language)
    return lexcor.recogniser(store, packages, classes, VARIANTS, language, (language,))


def tag(text: str, store: Store | None = None, packages: Iterable[str] | None = None,
        classes: Iterable[str] | None = None, language: str = "de") -> list[Mention]:
    """Which concepts does this text mention?  Every mention has its place in the text (in
    code points) and one assignment for each concept its words may mean, each with the
    package, the code, the class and the kind of the match."""
    return recogniser(store, packages, classes, language).tag(text)


def cover(store: Store | None = None, packages: Iterable[str] | None = None,
          classes: Iterable[str] | None = None, language: str = "de") -> Cover:
    """The medical vocabulary as one set of words and phrases, for the generous question;
    over the packages of a store, or without one over those that come with lexterm."""
    if store is None:
        return _bundled_cover(_chosen(packages), _chosen(classes), language)
    return lexcor.cover(store, packages, classes, EPONYM_HEADS, (language,))


def covers(text: str, start: int, end: int, store: Store | None = None,
           whole: bool = False) -> bool:
    """Is ``text[start:end]`` medical vocabulary?  A part of a hyphenated word counts
    ("Parkinson-Syndrom"), as does an eponym on its own ("Babinski").  With ``whole`` every
    word of the span must be vocabulary."""
    return cover(store).covers(text, start, end, whole=whole)
