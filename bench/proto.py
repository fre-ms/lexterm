# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""A prototype of lexterm's matcher, for the bench only.

It follows the rules of the design (section 5.2), which are those of PseudonyMed's matcher
with one difference: it says *which* terms matched, so that every match carries its codes.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

TOKEN = re.compile(r"[^\W\d_][\w\-]*|\d+[\w\-]*")
SUFFIXES = ("ern", "en", "es", "er", "em", "e", "n", "s")
TRANSLITERATION = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
MAX_WORDS = 5
MIN_STEM = 4

Match = tuple[int, int, frozenset[str]]


def only_as_written(term: str) -> bool:
    """Abbreviations and words of up to three letters match only in their own spelling."""
    if len(term) <= 3:
        return True
    capitals = sum(1 for c in term if c.isupper())
    return len(term) <= 6 and " " not in term and (capitals >= 2 or any(c.isdigit() for c in term))


def norm(word: str) -> str:
    """The word as the index holds it: case-folded, without the punctuation around it."""
    return word.casefold().strip(" .,;:!?\"'()[]")


class Matcher:
    """Whole terms, regardless of case and umlaut spelling, with German inflection endings."""

    def __init__(self, entries: Iterable[tuple[str, str]]) -> None:
        """Build the index from pairs of term and code."""
        self.single: dict[str, set[str]] = {}
        self.written: dict[str, set[str]] = {}
        self.phrases: dict[str, list[tuple[tuple[str, ...], set[str]]]] = {}
        phrases: dict[tuple[str, ...], set[str]] = {}
        for term, code in entries:
            term = term.strip()
            words = [w for w in re.split(r"[\s/]+", term) if w]
            if not words:
                continue
            if len(words) == 1:
                if only_as_written(term):
                    self.written.setdefault(term, set()).add(code)
                else:
                    for form in {norm(term), norm(term).translate(TRANSLITERATION)} - {""}:
                        self.single.setdefault(form, set()).add(code)
            elif len(words) <= MAX_WORDS:
                phrases.setdefault(tuple(norm(w) for w in words), set()).add(code)
        for sequence, codes in phrases.items():
            self.phrases.setdefault(sequence[0], []).append((sequence, codes))
            folded = sequence[0].translate(TRANSLITERATION)
            if folded != sequence[0]:
                self.phrases.setdefault(folded, []).append((sequence, codes))
        for candidates in self.phrases.values():
            candidates.sort(key=lambda entry: len(entry[0]), reverse=True)

    def _word(self, form: str) -> set[str]:
        """The codes of one normalised word: as listed, or a listed stem with an ending."""
        for candidate in (form, form.translate(TRANSLITERATION)):
            if candidate in self.single:
                return self.single[candidate]
        for suffix in SUFFIXES:
            if form.endswith(suffix) and len(form) - len(suffix) >= MIN_STEM:
                stem = form[: -len(suffix)]
                for candidate in (stem, stem.translate(TRANSLITERATION)):
                    if candidate in self.single:
                        return self.single[candidate]
        return set()

    def _same(self, form: str, listed: str, last: bool) -> bool:
        """Does a word of the text spell a word of a phrase (the last one may be inflected)?"""
        if form == listed or form.translate(TRANSLITERATION) == listed.translate(TRANSLITERATION):
            return True
        return last and any(form.endswith(s) and len(form) - len(s) >= MIN_STEM
                            and form[: -len(s)] == listed for s in SUFFIXES)

    def _phrase(self, forms: list[str], i: int) -> tuple[int, set[str]]:
        """Length and codes of the longest phrase that starts at word ``i`` (0 when none)."""
        candidates = self.phrases.get(forms[i]) or self.phrases.get(
            forms[i].translate(TRANSLITERATION)) or []
        for sequence, codes in candidates:
            n = len(sequence)
            if i + n <= len(forms) and all(
                    self._same(forms[i + k], sequence[k], k == n - 1) for k in range(n)):
                return n, codes
        return 0, set()

    def tag(self, text: str) -> list[Match]:
        """Every mention of a term with the codes of the concepts it may mean."""
        tokens = [(m.start(), m.end(), m.group(0)) for m in TOKEN.finditer(text)]
        forms = [norm(word) for _a, _b, word in tokens]
        taken = [False] * len(tokens)
        found: list[Match] = []
        for i, (a, _b, _word) in enumerate(tokens):
            if taken[i]:
                continue
            n, codes = self._phrase(forms, i)
            if n:
                found.append((a, tokens[i + n - 1][1], frozenset(codes)))
                taken[i:i + n] = [True] * n
        for i, (a, b, word) in enumerate(tokens):
            if taken[i]:
                continue
            codes = self.written.get(word) or self._word(forms[i])
            if codes:
                found.append((a, b, frozenset(codes)))
        return sorted(found)
