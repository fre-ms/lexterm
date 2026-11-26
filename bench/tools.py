# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The recognisers under test, each behind the same two calls.

``build(entries)`` takes the dictionary as pairs of term and code; ``tag(text)`` returns the
mentions as ``(start, end, codes)`` with positions in code points.  A recogniser whose
library is not installed is left out of ``TOOLS``; a recogniser that needs an environment
of its own (QuickUMLS) is run from that environment with ``--tools``.
"""

from __future__ import annotations

import re
import tempfile
from collections.abc import Callable
from pathlib import Path

Entries = list[tuple[str, str]]
Match = tuple[int, int, frozenset[str]]
GERMAN_LETTERS = "äöüÄÖÜß"
SUFFIXES = ("ern", "en", "es", "er", "em", "e", "n", "s")


def codes_by_term(entries: Entries) -> dict[str, set[str]]:
    """The codes of every term, by its lower-case spelling."""
    by_term: dict[str, set[str]] = {}
    for term, code in entries:
        by_term.setdefault(term.lower(), set()).add(code)
    return by_term


def longest(matches: list[Match]) -> list[Match]:
    """Drop every match that lies inside a longer one or overlaps an earlier, longer one."""
    kept: list[Match] = []
    for match in sorted(matches, key=lambda m: (-(m[1] - m[0]), m[0])):
        if all(match[1] <= other[0] or match[0] >= other[1] for other in kept):
            kept.append(match)
    return sorted(kept)


class Prototype:
    """lexterm's own rules (``proto.py``)."""

    name = "lexterm prototype"

    def build(self, entries: Entries) -> None:
        from proto import Matcher
        self.matcher = Matcher(entries)

    def tag(self, text: str) -> list[Match]:
        return self.matcher.tag(text)


class FlashText:
    """FlashText as it comes: letters outside ASCII end a word."""

    name = "FlashText (as shipped)"
    german = False

    def build(self, entries: Entries) -> None:
        from flashtext import KeywordProcessor
        self.codes = codes_by_term(entries)
        self.processor = KeywordProcessor(case_sensitive=False)
        if self.german:
            for letter in GERMAN_LETTERS:
                self.processor.add_non_word_boundary(letter)
        for term in self.codes:
            self.processor.add_keyword(term, term)

    def tag(self, text: str) -> list[Match]:
        found = self.processor.extract_keywords(text, span_info=True)
        return [(a, b, frozenset(self.codes[term])) for term, a, b in found]


class FlashTextGerman(FlashText):
    """FlashText told that umlauts and ß are letters."""

    name = "FlashText (umlauts as letters)"
    german = True


class AhoCorasick:
    """pyahocorasick over the lower-case text, with a check of the word boundaries."""

    name = "pyahocorasick + boundaries"

    def build(self, entries: Entries) -> None:
        import ahocorasick
        self.codes = codes_by_term(entries)
        self.automaton = ahocorasick.Automaton()
        for term in self.codes:
            self.automaton.add_word(term, term)
        self.automaton.make_automaton()

    def tag(self, text: str) -> list[Match]:
        lower = text.lower()
        if len(lower) != len(text):  # a letter whose lower case is longer would shift positions
            lower = "".join(c.lower() if len(c.lower()) == 1 else c for c in text)
        found = []
        for end, term in self.automaton.iter(lower):
            a, b = end - len(term) + 1, end + 1
            before = lower[a - 1] if a else " "
            after = lower[b] if b < len(lower) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                found.append((a, b, frozenset(self.codes[term])))
        return longest(found)


class SpacyPhrase:
    """spaCy's PhraseMatcher on the German tokeniser, comparing lower-case words."""

    name = "spaCy PhraseMatcher (LOWER)"

    def build(self, entries: Entries) -> None:
        import spacy
        from spacy.matcher import PhraseMatcher
        self.nlp = spacy.blank("de")
        self.codes = codes_by_term(entries)
        self.terms = sorted(self.codes)
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        for i, doc in enumerate(self.nlp.tokenizer.pipe(self.terms)):
            if len(doc):
                self.matcher.add(str(i), [doc])

    def tag(self, text: str) -> list[Match]:
        doc = self.nlp.make_doc(text)
        found = []
        for match_id, a, b in self.matcher(doc):
            span = doc[a:b]
            term = self.terms[int(self.nlp.vocab.strings[match_id])]
            found.append((span.start_char, span.end_char, frozenset(self.codes[term])))
        return longest(found)


def german_stem(word: str) -> str:
    """The word without a German inflection ending, by the rule the prototype uses."""
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


class Iamsystem:
    """iamsystem as it comes: exact words after its own normalisation."""

    name = "iamsystem (exact)"
    options: Callable[[], dict] = staticmethod(lambda: {})

    def build(self, entries: Entries) -> None:
        from iamsystem import Entity, Matcher
        keywords = [Entity(label=term, kb_id=code) for term, code in entries]
        self.matcher = Matcher.build(keywords=keywords, **self.options())

    def tag(self, text: str) -> list[Match]:
        return [(a.start, a.end, frozenset(k.kb_id for k in a.keywords))
                for a in self.matcher.annot_text(text)]


class IamsystemStem(Iamsystem):
    """iamsystem with a German ending-stripper as word normaliser."""

    name = "iamsystem (endings stripped)"
    options = staticmethod(lambda: {"normalizers": [dict(name="german", norm_fun=german_stem)]})


class IamsystemFuzzy(Iamsystem):
    """iamsystem with endings stripped and one spelling error allowed in longer words."""

    name = "iamsystem (endings + Levenshtein 1)"
    options = staticmethod(lambda: {
        "normalizers": [dict(name="german", norm_fun=german_stem)],
        "spellwise": [dict(measure="Levenshtein", max_distance=1, min_nb_char=7)]})


class EdsNlp:
    """EDS-NLP's terminology matcher on a German pipeline, comparing normalised words."""

    name = "EDS-NLP terminology (NORM)"
    term_matcher = "exact"
    config: dict | None = None

    def build(self, entries: Entries) -> None:
        import edsnlp
        import edsnlp.pipes as eds
        terms: dict[str, list[str]] = {}
        for term, code in entries:
            terms.setdefault(code, []).append(term)
        self.nlp = edsnlp.blank("de")
        self.nlp.add_pipe(eds.normalizer())
        self.nlp.add_pipe(eds.terminology(label="term", terms=terms, attr="NORM",
                                          term_matcher=self.term_matcher,
                                          term_matcher_config=self.config))

    def tag(self, text: str) -> list[Match]:
        doc = self.nlp(text)
        merged: dict[tuple[int, int], set[str]] = {}
        for ent in doc.ents:
            merged.setdefault((ent.start_char, ent.end_char), set()).add(ent.kb_id_)
        return longest([(a, b, frozenset(codes)) for (a, b), codes in merged.items()])


class EdsNlpSimstring(EdsNlp):
    """EDS-NLP with its approximate matcher (SimString)."""

    name = "EDS-NLP terminology (SimString)"
    term_matcher = "simstring"
    config = {"measure": "dice", "threshold": 0.85}


class MedCat:
    """MedCAT 2 without a trained model: its vocabulary recogniser and a linker that takes a
    name only where it is unambiguous or the concept's main name."""

    name = "MedCAT (default NER)"
    ner = "default"

    def build(self, entries: Entries) -> None:
        import pandas as pd
        from medcat.cat import CAT
        from medcat.config import Config
        from medcat.model_creation.cdb_maker import CDBMaker
        config = Config()
        config.general.nlp.provider = "regex"
        config.components.ner.comp_name = self.ner
        config.components.linking.comp_name = "primary_name_only_linker"
        frame = pd.DataFrame({"cui": [code for _t, code in entries],
                              "name": [term for term, _c in entries]})
        cdb = CDBMaker(config).prepare_csvs([frame], full_build=False)
        self.cat = CAT(cdb, vocab=None, config=config)

    def tag(self, text: str) -> list[Match]:
        entities = self.cat.get_entities(text)["entities"].values()
        return longest([(e["start"], e["end"], frozenset({e["cui"]})) for e in entities])


class MedCatDict(MedCat):
    """MedCAT 2 with its dictionary recogniser (pyahocorasick)."""

    name = "MedCAT (dict NER)"
    ner = "dict"


class QuickUmls:
    """QuickUMLS (the fork kept by medspaCy) over a UMLS folder written from the dictionary."""

    name = "QuickUMLS (medspaCy fork)"

    def build(self, entries: Entries) -> None:
        import subprocess
        import sys

        from quickumls import QuickUMLS
        root = Path(tempfile.mkdtemp(prefix="quickumls"))
        umls, data = root / "umls", root / "data"
        umls.mkdir()
        self.codes = {}
        with (umls / "MRCONSO.RRF").open("w", encoding="utf-8") as conso:
            for n, (term, code) in enumerate(entries):
                if "|" in term:
                    continue
                cui = self.codes.setdefault(code, f"C{len(self.codes):07d}")
                conso.write(f"{cui}|GER|P|L{n:07d}|PF|S{n:07d}|Y|A{n:07d}||||X|PT|{code}|{term}"
                            "|0|N|256|\n")
        with (umls / "MRSTY.RRF").open("w", encoding="utf-8") as sty:
            for cui in sorted(set(self.codes.values())):
                sty.write(f"{cui}|T047|B2.2.1.2.1|Disease or Syndrome|AT00000000|256|\n")
        subprocess.run([sys.executable, "-m", "quickumls.install", str(umls), str(data),
                        "-E", "GER", "-L"], check=True, capture_output=True, text=True,
                       input="y\n")  # the installer asks before it creates the folder
        self.back = {cui: code for code, cui in self.codes.items()}
        import spacy

        def tokeniser(*_args: object, **_settings: object) -> object:
            """QuickUMLS asks for the model de_core_news_sm; the bench gives it the German
            tokeniser with sentence splitting instead, so that no model has to be fetched."""
            nlp = spacy.blank("de")
            nlp.add_pipe("sentencizer")
            return nlp

        load, spacy.load = spacy.load, tokeniser
        try:
            self.matcher = QuickUMLS(str(data), overlapping_criteria="length", threshold=0.9,
                                     similarity_name="jaccard", window=5,
                                     accepted_semtypes={"T047"})
        finally:
            spacy.load = load

    def tag(self, text: str) -> list[Match]:
        found = []
        for candidates in self.matcher.match(text, best_match=True, ignore_syntax=True):
            best = max(candidates, key=lambda c: c["similarity"])
            codes = {self.back[c["cui"]] for c in candidates
                     if c["similarity"] == best["similarity"]}
            found.append((best["start"], best["end"], frozenset(codes)))
        return longest(found)


def available() -> dict[str, type]:
    """The recognisers whose libraries can be imported here."""
    wanted = {
        "proto": (Prototype, None), "flashtext": (FlashText, "flashtext"),
        "flashtext-de": (FlashTextGerman, "flashtext"), "aho": (AhoCorasick, "ahocorasick"),
        "spacy": (SpacyPhrase, "spacy"), "iamsystem": (Iamsystem, "iamsystem"),
        "iamsystem-stem": (IamsystemStem, "iamsystem"),
        "iamsystem-fuzzy": (IamsystemFuzzy, "iamsystem"), "edsnlp": (EdsNlp, "edsnlp"),
        "edsnlp-simstring": (EdsNlpSimstring, "edsnlp"), "medcat": (MedCat, "medcat"),
        "medcat-dict": (MedCatDict, "medcat"), "quickumls": (QuickUmls, "quickumls"),
    }
    found = {}
    for key, (cls, module) in wanted.items():
        try:
            if module:
                __import__(module)
            found[key] = cls
        except ImportError:
            pass
    return found


WORD = re.compile(r"[^\W\d_][\w\-]*")
