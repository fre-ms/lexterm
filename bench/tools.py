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


class Lexcor:
    """The recogniser of lexcor, the core that grew out of the prototype."""

    name = "lexcor"
    variants: tuple[tuple[str, str], ...] = ()

    def build(self, entries: Entries) -> None:
        from lexcor import Entry, Recogniser
        self.recogniser = Recogniser(
            (Entry(term, None, "bench", "", code, term, "", "", "synonym")
             for term, code in entries), self.variants)

    def tag(self, text: str) -> list[Match]:
        return [(m.start, m.end, frozenset(a.code for a in m.assignments))
                for m in self.recogniser.tag(text)]


class LexcorVariants(Lexcor):
    """lexcor with lexterm's table of spellings that stand side by side."""

    name = "lexcor + spelling table"
    variants = (("ph", "f"), ("th", "t"), ("rh", "r"), ("ce", "ze"), ("ci", "zi"), ("cy", "zy"),
                ("cae", "zae"), ("c", "k"), ("y", "i"))


STOP_WORDS = frozenset("""
aber alle allem allen aller alles als also am an ander andere anderem anderen anderer anderes
auch auf aus bei beim bin bis bist da damit dann das dass dem den denn der des dessen die dies
diese diesem diesen dieser dieses doch dort du durch ein eine einem einen einer eines er es
etwas euch euer für gegen hat hatte hatten hier hin hinter ich ihm ihn ihnen ihr ihre ihrem
ihren ihrer im in indem ins ist jede jedem jeden jeder jedes jene kann kein keine keinem keinen
keiner man mit muss nach nicht nichts noch nun nur ob oder ohne sehr sein seine seinem seinen
seiner sich sie sind so solche sondern sonst sowie über um und uns unter vom von vor war waren
was weg weil weiter welche wenn wer werde werden wie wieder will wir wird wo zu zum zur zwar
zwischen bzw ca ggf sog vgl z b d h u a o g
""".split())
SPELLINGS = (("ph", "f"), ("th", "t"), ("rh", "r"), ("ae", "ä"), ("oe", "ö"), ("ue", "ü"),
             ("ß", "ss"), ("ce", "ze"), ("ci", "zi"), ("cy", "zy"), ("cä", "zä"), ("c", "k"),
             ("y", "i"))


def folded(word: str) -> str:
    """A word with the spellings German medicine has side by side made one: c with k and z,
    ph with f, th with t, umlauts written out or not."""
    word = word.casefold()
    for old, new in SPELLINGS:
        word = word.replace(old, new)
    return word


class PrototypeFolded:
    """lexterm's rules with spelling variants folded by rule ("Colitis" finds "Kolitis")."""

    name = "lexterm prototype + spelling rule"

    def build(self, entries: Entries) -> None:
        from proto import Matcher, only_as_written
        self.fold = {}
        for term, _code in entries:
            if not only_as_written(term):
                self.fold.setdefault(" ".join(folded(w) for w in term.split()), term)
        self.matcher = Matcher(entries)
        self.by_fold = Matcher([(" ".join(folded(w) for w in term.split()), code)
                                for term, code in entries if not only_as_written(term)])

    def tag(self, text: str) -> list[Match]:
        from proto import TOKEN
        found = self.matcher.tag(text)
        pieces, last = [], 0
        for m in TOKEN.finditer(text):  # fold word by word so that positions stay the same
            word = m.group(0)
            same = folded(word)
            pieces.append(text[last:m.start()] + (same if len(same) == len(word) else word))
            last = m.end()
        pieces.append(text[last:])
        extra = [m for m in self.by_fold.tag("".join(pieces))
                 if all(m[1] <= f[0] or m[0] >= f[1] for f in found)]
        return sorted(found + extra)


def trigrams(text: str) -> set[str]:
    """The letter trigrams of a string, with marks for its beginning and end."""
    padded = f"##{text}##"
    return {padded[i:i + 3] for i in range(len(padded) - 2)}


class SimString:
    """Approximate dictionary matching after QuickUMLS: every run of up to five words that
    passes its rules is looked up with SimString (letter trigrams, cosine) and the best,
    longest matches that do not overlap are kept.  Abbreviations match only as written."""

    name = "SimString 0.9"
    threshold = 0.9

    def build(self, entries: Entries) -> None:
        from pysimstring import simstring

        from proto import only_as_written
        self.simstring = simstring
        self.written: dict[str, set[str]] = {}
        self.codes: dict[str, set[str]] = {}
        for term, code in entries:
            if only_as_written(term):
                self.written.setdefault(term, set()).add(code)
            else:
                self.codes.setdefault(" ".join(term.lower().split()), set()).add(code)
        self.path = str(Path(tempfile.mkdtemp(prefix="simstring")) / "terms.db")
        writer = simstring.writer(self.path, 3, False, True)
        for term in self.codes:
            writer.insert(term)
        writer.close()
        self.reader = simstring.reader(self.path)
        self.reader.measure = simstring.cosine
        self.reader.threshold = self.threshold

    def tag(self, text: str) -> list[Match]:
        from proto import TOKEN
        tokens = [(m.start(), m.end(), m.group(0)) for m in TOKEN.finditer(text)]
        candidates = []
        for i, (a, _b, first) in enumerate(tokens):
            if first in self.written:
                candidates.append((1.0, a, tokens[i][1], frozenset(self.written[first])))
            if first.lower() in STOP_WORDS:
                continue
            for n in range(1, 6):
                if i + n > len(tokens):
                    break
                b, last = tokens[i + n - 1][1], tokens[i + n - 1][2]
                if "\n" in text[a:b] or last.lower() in STOP_WORDS:
                    continue
                query = " ".join(text[a:b].lower().split())
                if len(query) < 4 or query.isdigit():
                    continue
                grams = trigrams(query)
                best, codes = 0.0, set()
                for term in self.reader.retrieve(query):
                    other = trigrams(term)
                    score = len(grams & other) / (len(grams) * len(other)) ** 0.5
                    if score > best:
                        best, codes = score, set(self.codes[term])
                    elif score == best:
                        codes |= self.codes[term]
                if codes:
                    candidates.append((best, a, b, frozenset(codes)))
        kept: list[Match] = []
        for _score, a, b, codes in sorted(candidates, key=lambda c: (-c[0], -(c[2] - c[1]))):
            if all(b <= other[0] or a >= other[1] for other in kept):
                kept.append((a, b, codes))
        return sorted(kept)


class SimString08(SimString):
    name = "SimString 0.8"
    threshold = 0.8


class SimString07(SimString):
    name = "SimString 0.7"
    threshold = 0.7


def word_runs(text: str) -> list[tuple[int, int]]:
    """Runs of up to five words in a line that neither begin nor end with a function word:
    the rules QuickUMLS gives for what may be a term."""
    from proto import TOKEN
    tokens = [(m.start(), m.end(), m.group(0).lower()) for m in TOKEN.finditer(text)]
    runs = []
    for i, (a, _b, first) in enumerate(tokens):
        if first in STOP_WORDS:
            continue
        for b, last in ((t[1], t[2]) for t in tokens[i:i + 5]):
            if "\n" in text[a:b]:
                break
            if last not in STOP_WORDS and b - a >= 4 and not text[a:b].isdigit():
                runs.append((a, b))
    return runs


class Meaning:
    """Search by meaning behind the prototype: what the prototype finds stands; every other
    run of words is turned into a vector by a model trained on the names of concepts
    (``semantic.py``) and takes the nearest name of the dictionary when it is near enough.
    Abbreviations match only as written, so they are no targets of the search."""

    name = "prototype + meaning 0.9"
    threshold = 0.9
    lower = True  # names and runs in small letters: a little better on German text

    def build(self, entries: Entries) -> None:
        import semantic
        from proto import Matcher, only_as_written
        self.matcher = Matcher(entries)
        codes: dict[str, set[str]] = {}
        for term, code in entries:
            if not only_as_written(term):
                codes.setdefault(" ".join(term.split()), set()).add(code)
        self.names = sorted(codes)
        self.codes = [frozenset(codes[name]) for name in self.names]
        self.index = semantic.index(self.names, self.lower)
        self.matched: list[tuple[str, str, float]] = []

    def tag(self, text: str) -> list[Match]:
        found = self.matcher.tag(text)
        runs = [(a, b) for a, b in word_runs(text)
                if all(b <= f[0] or a >= f[1] for f in found)]
        nearest = self.index.best([" ".join(text[a:b].split()) for a, b in runs])
        candidates = []
        for a, b in runs:
            score, number = nearest[" ".join(text[a:b].split())]
            if score >= self.threshold:
                candidates.append((score, a, b, number))
        kept: list[tuple[int, int, int, float]] = []
        for score, a, b, number in sorted(candidates, key=lambda c: (-c[0], -(c[2] - c[1]))):
            if all(b <= other[0] or a >= other[1] for other in kept):
                kept.append((a, b, number, score))
        self.matched += [(text[a:b], self.names[n], round(score, 3)) for a, b, n, score in kept]
        return sorted(found + [(a, b, self.codes[n]) for a, b, n, _score in kept])


class Meaning095(Meaning):
    name = "prototype + meaning 0.95"
    threshold = 0.95


class Meaning085(Meaning):
    name = "prototype + meaning 0.85"
    threshold = 0.85


class Meaning08(Meaning):
    name = "prototype + meaning 0.8"
    threshold = 0.8


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
    """QuickUMLS (the original under Python 3.11, or medspaCy's fork) over a UMLS folder written
    from the dictionary."""

    name = "QuickUMLS 1.4"

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
        "proto": (Prototype, None), "proto-fold": (PrototypeFolded, None),
        "lexcor": (Lexcor, "lexcor"), "lexcor-variants": (LexcorVariants, "lexcor"),
        "simstring-0.9": (SimString, "pysimstring"), "simstring-0.8": (SimString08, "pysimstring"),
        "simstring-0.7": (SimString07, "pysimstring"), "flashtext": (FlashText, "flashtext"),
        "flashtext-de": (FlashTextGerman, "flashtext"), "aho": (AhoCorasick, "ahocorasick"),
        "spacy": (SpacyPhrase, "spacy"), "iamsystem": (Iamsystem, "iamsystem"),
        "iamsystem-stem": (IamsystemStem, "iamsystem"),
        "iamsystem-fuzzy": (IamsystemFuzzy, "iamsystem"), "edsnlp": (EdsNlp, "edsnlp"),
        "edsnlp-simstring": (EdsNlpSimstring, "edsnlp"), "medcat": (MedCat, "medcat"),
        "medcat-dict": (MedCatDict, "medcat"), "quickumls": (QuickUmls, "quickumls"),
        "meaning-0.95": (Meaning095, "transformers"), "meaning-0.9": (Meaning, "transformers"),
        "meaning-0.85": (Meaning085, "transformers"), "meaning-0.8": (Meaning08, "transformers"),
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
