# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""A bench for recognisers of medical terms in German text.

    python bench.py make DICTIONARY.csv[.gz] testset.json     # the test set, from a dictionary
    python bench.py run testset.json results/ --tools proto,spacy
    python bench.py report results/
    python bench.py corpus BRAT_FOLDER QID_CUI.csv DICTIONARY results/ --tools proto
    python bench.py texts TEXT_FOLDER DICTIONARY results/ --tools proto

The dictionary is a CSV of term, class and code (PseudonyMed's ``fachklassen_de.csv.gz``,
German labels from Wikidata, CC0).  The test set is made from it, so the truth is known by
construction: terms set into carrier sentences as written and in the variations German
text brings (capitals, inflection endings, transliterated umlauts, a spelling error), and
text that must *not* be tagged (ordinary words that are an abbreviation when written in
capitals, compounds that merely contain a term, plain prose).  Every recogniser gets the
same dictionary.  Run one recogniser per call to measure its time and memory alone.

``corpus`` measures on a corpus annotated by people in brat's format, whose labels are UMLS
identifiers (the German part of the Mantra GSC); the dictionary's Wikidata codes are taken
to UMLS through a table of item and identifier (Wikidata's property P2892).  ``texts``
counts what each recogniser tags in a folder of plain texts that carry no annotation
(GraSCCo).  Neither corpus is part of this repository.
"""

from __future__ import annotations

import csv
import gzip
import json
import random
import re
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from proto import SUFFIXES, TRANSLITERATION, only_as_written  # noqa: E402

CARRIERS = [
    "Im Brief wird {} ausdrücklich genannt.",
    "Zuletzt war {} wieder Thema.",
    "Darüber hinaus fiel {} auf.",
    "Wir sprachen ausführlich über {} und das weitere Vorgehen.",
    "Vorbekannt ist {} seit vielen Jahren.",
    "Unter dem Stichwort {} steht dazu mehr.",
]
BAIT_CARRIER = "Im Satz steht {} nur als gewöhnliches Wort."
COMMON_WORDS = """als art ass bei bis das der die ein eine er es gab hat ich ihr im in ist mal man
mit nur ob rat sei sie so tag tat um und uns von vor war was wer wie wir zu zum zur alt arm bar gut
hin los neu not rot tot weg ja nie nun oft see tor ton typ uhr weh ach akt all alle amt ast bad bau
box bus dom eis elf fax fee gas hof hut jod kur lob mut nah ohr ost pol rad ruf saft tee ufer wal
zug""".split()
COMPOUNDS = """Handschuh Armband Kopfsteinpflaster Herzlich Ohrfeige Fußball Beinahe Halsband
Rückenwind Augenblick Zahnrad Blutorange Nasenbär Knieschoner Fingerhut Bauchladen Lungenflügelchen
Hautnah Magenta Lebertranflasche Nierentisch Brustton Zehnkampf Ellenlang Darmstadt Hüftgold
Wadenwickelkurs Stirnseite Zungenbrecher Nervenkitzel Venedig Arterienstraße Muskelkater
Knochenarbeit Gelenkbus Hirngespinst Schädelstätte Rippenstück Wirbelsturm Sehnenscheide""".split()
PROSE = """Am Morgen fuhr der Zug pünktlich vom Bahnhof ab.
Die Rechnung für das Fahrrad liegt noch auf dem Schreibtisch.
Wir treffen uns am Dienstag um halb neun vor dem Rathaus.
Das Fenster zum Garten klemmt seit dem letzten Winter.
Bitte schicken Sie die Unterlagen bis Freitag an die Verwaltung.
Der Vortrag begann mit einer langen Vorrede und endete ohne Fragen.
Im Urlaub las sie drei Bücher und schrieb zwei Briefe.
Der Vermieter kündigte eine Erhöhung der Nebenkosten an.
Auf dem Markt gab es Äpfel, Birnen und frisches Brot.
Die Kinder bauten am Nachmittag eine Brücke aus Holzklötzen.
Nach dem Umzug fehlten zwei Kartons mit Geschirr.
Der Bus hielt ausnahmsweise direkt vor der Schule.
Seine Schwester arbeitet als Tischlerin in einer kleinen Werkstatt.
Für die Reise nach Bremen brauchen wir noch Fahrkarten.
Das Protokoll der Sitzung wurde einstimmig angenommen.
Sie telefonierte lange mit der Bank wegen des Kontos.
Der Hund des Nachbarn bellt jeden Abend um dieselbe Zeit.
Im Keller stehen noch die alten Stühle der Großeltern.
Der Antrag muss in zweifacher Ausfertigung eingereicht werden.
Gestern regnete es ununterbrochen bis in die Nacht.""".splitlines()
LETTER = """Sehr geehrte Frau Kollegin,

wir berichten über den oben genannten Patienten, der sich vom 3. bis 12. März in unserer stationären
Behandlung befand.

Diagnosen: Ischämischer Schlaganfall im Stromgebiet der Arteria cerebri media links. Arterielle
Hypertonie. Diabetes mellitus Typ 2. Vorhofflimmern, ED aktuell. Zustand nach Myokardinfarkt 2019.
Hyperlipidämie. Chronische Niereninsuffizienz.

Anamnese: Der Patient bemerkte am Morgen eine Schwäche des rechten Arms und eine Sprachstörung.
Kopfschmerzen, Übelkeit oder Erbrechen bestanden nicht. Kein Fieber, keine Dyspnoe. Der Vater des
Patienten litt an einer Demenz; die Mutter hatte eine Epilepsie.

Befund: Wacher Patient, zu allen Qualitäten orientiert. Aphasie mit Wortfindungsstörungen.
Hemiparese rechts, armbetont. Babinski rechts positiv. Keine Nackensteifigkeit. Herztöne rein,
Lunge frei, Abdomen weich. Kein Hinweis auf eine Pneumonie. NIHSS bei Aufnahme 7 Punkte.

Diagnostik: Im CCT kein Nachweis einer Blutung. Die MRT zeigte eine frische Ischämie im
Mediastromgebiet. In der Echokardiographie fand sich kein Thrombus. Labor: Kreatinin 1,4 mg/dl,
HbA1c 7,9 %, LDL-Cholesterin 148 mg/dl, CRP unauffällig, TSH im Normbereich.

Therapie und Verlauf: Nach Ausschluss von Kontraindikationen erfolgte eine Thrombolyse. Wir
begannen eine Antikoagulation mit Apixaban 5 mg 1-0-1 und setzten Atorvastatin 40 mg 0-0-1 sowie
Ramipril 5 mg 1-0-0 an; Metformin 1000 mg 1-0-1 wurde fortgeführt. ASS wurde abgesetzt. Unter
Physiotherapie und Logopädie besserten sich die Hemiparese und die Aphasie deutlich.

Empfehlung: Kontrolle des Blutdrucks und der Nierenwerte, Fortführung der Antikoagulation.

Mit freundlichen Grüßen"""


def load_dictionary(path: Path) -> list[tuple[str, str]]:
    """Pairs of term and code from a CSV of term, class, code (comments and header skipped)."""
    opener = gzip.open if path.suffix == ".gz" else open
    entries = []
    with opener(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.reader(line for line in file if not line.startswith("#")):
            if len(row) < 3 or row[0] == "begriff":
                continue
            term = row[0].strip()
            if len(term) >= 2 and "''" not in term and '"' not in term:
                entries.append((term, row[2].strip()))
    return entries


def known_words(entries: list[tuple[str, str]]) -> set[str]:
    """Every single-word term in lower case, for keeping carriers free of terms."""
    return {term.lower() for term, _code in entries if " " not in term}


def is_listed(word: str, known: set[str]) -> bool:
    """Is a word a term, as written or with an inflection ending?"""
    lower = word.lower()
    forms = {lower, lower.translate(TRANSLITERATION)}
    forms |= {lower[: -len(s)] for s in SUFFIXES if lower.endswith(s) and len(lower) - len(s) >= 4}
    return bool(forms & known)


def with_ending(term: str) -> str:
    """The term with an inflection ending as German puts one on."""
    if term.endswith("e"):
        return term + "n"
    if term[-1] in "szxß":
        return term + "en"
    return term + "s"


def with_error(term: str) -> str:
    """The term with one letter in its middle exchanged."""
    i = len(term) // 2
    other = "e" if term[i].lower() != "e" else "a"
    return term[:i] + other + term[i + 1:]


def make(dictionary: Path, target: Path, seed: int = 20261126) -> None:
    """Write the test set: one text with the places that must be found and their codes."""
    rng = random.Random(seed)
    entries = load_dictionary(dictionary)
    known = known_words(entries)
    by_lower: dict[str, set[str]] = {}
    for term, code in entries:
        by_lower.setdefault(term.lower(), set()).add(code)
    letters = re.compile(r"[A-Za-zÄÖÜäöüß]+")
    single = sorted({t for t, _c in entries if letters.fullmatch(t) and 6 <= len(t) <= 22
                     and not only_as_written(t) and t[0].isupper()})
    phrases = sorted({t for t, _c in entries if 2 <= len(t.split()) <= 3
                      and all(letters.fullmatch(w) and len(w) >= 3 for w in t.split())})
    umlauts = [t for t in single if re.search("[äöüÄÖÜ]", t) and "ß" not in t]
    abbreviations = sorted({t for t, _c in entries if re.fullmatch(r"[A-Z][A-Za-z0-9]{1,5}", t)
                            and only_as_written(t) and sum(c.isupper() for c in t) >= 2})
    plain = [t for t in single if not re.search("[äöüÄÖÜß]", t)]
    cases = (
        [("exact", t, t) for t in rng.sample(plain, 150)]
        + [("umlaut", t, t) for t in rng.sample(umlauts, 100)]
        + [("phrase", t, t) for t in rng.sample(phrases, 150)]
        + [("capitals", t, t.upper()) for t in rng.sample(plain, 100)]
        + [("ending", t, with_ending(t)) for t in rng.sample(plain, 150)]
        + [("transliterated", t, t.translate(TRANSLITERATION)) for t in rng.sample(umlauts, 100)]
        + [("abbreviation", t, t) for t in rng.sample(abbreviations, 100)]
        + [("error", t, with_error(t)) for t in rng.sample([p for p in plain if len(p) >= 9], 100)]
    )
    cases = [c for c in cases if c[0] not in ("ending", "error") or c[2].lower() not in by_lower]
    carriers = [c for c in CARRIERS if not any(is_listed(w, known)
                                              for w in letters.findall(c.replace("{}", "")))]
    bait_case = sorted(w for w in set(COMMON_WORDS) if w.upper() in {t for t, _c in entries}
                       and w not in {t for t, _c in entries})
    bait_compound = [w for w in COMPOUNDS if w.lower() not in by_lower]
    prose = [s for s in PROSE if not any(is_listed(w, known) for w in letters.findall(s))]
    bait_ok = not any(is_listed(w, known) for w in letters.findall(BAIT_CARRIER.replace("{}", "")))
    rng.shuffle(cases)
    parts: list[str] = []
    gold: list[dict] = []
    negative: list[dict] = []
    position = 0

    def add(sentence: str) -> int:
        nonlocal position
        start = position
        parts.append(sentence + "\n")
        position += len(sentence) + 1
        return start

    for kind, term, written in cases:
        carrier = rng.choice(carriers)
        start = add(carrier.format(written))
        a = start + carrier.index("{}")
        gold.append({"kind": kind, "term": term, "start": a, "end": a + len(written),
                     "codes": sorted(by_lower[term.lower()])})
    for kind, words in (("bait: ordinary word", bait_case), ("bait: compound", bait_compound)):
        for word in words:
            start = add(BAIT_CARRIER.format(word))
            a = start + BAIT_CARRIER.index("{}")
            negative.append({"kind": kind, "start": a, "end": a + len(word)})
    for sentence in prose:
        start = add(sentence)
        negative.append({"kind": "prose", "start": start, "end": start + len(sentence)})
    target.write_text(json.dumps({
        "dictionary": str(dictionary), "entries": len(entries), "seed": seed,
        "carriers": len(carriers), "bait_carrier_clean": bait_ok, "text": "".join(parts),
        "gold": gold, "negative": negative, "letter": LETTER,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = {k: sum(1 for g in gold if g["kind"] == k)
             for k in dict.fromkeys(g["kind"] for g in gold)}
    print(f"{len(entries)} entries; gold {kinds}; negatives "
          f"{len(bait_case)} words, {len(bait_compound)} compounds, {len(prose)} sentences")


def overlap(a: tuple[int, int], b: tuple[int, int]) -> float:
    """Shared share of two spans (intersection over union)."""
    shared = min(a[1], b[1]) - max(a[0], b[0])
    return shared / (max(a[1], b[1]) - min(a[0], b[0])) if shared > 0 else 0.0


def score(testset: dict, found: list) -> dict:
    """Found and linked places per kind, and what was tagged where nothing should be."""
    kinds: dict[str, dict[str, int]] = {}
    hit = [False] * len(found)
    for item in testset["gold"]:
        row = kinds.setdefault(item["kind"], {"n": 0, "found": 0, "linked": 0})
        row["n"] += 1
        best = None
        for i, (a, b, codes) in enumerate(found):
            if overlap((a, b), (item["start"], item["end"])) >= 0.6:
                hit[i] = True
                if best is None or set(codes) & set(item["codes"]):
                    best = codes
        if best is not None:
            row["found"] += 1
            row["linked"] += bool(set(best) & set(item["codes"]))
    false: dict[str, int] = {"bait: ordinary word": 0, "bait: compound": 0, "prose": 0,
                             "carrier": 0}
    examples: dict[str, list[str]] = {k: [] for k in false}
    for i, (a, b, _codes) in enumerate(found):
        if hit[i] or any(overlap((a, b), (g["start"], g["end"])) > 0 for g in testset["gold"]):
            continue
        kind = next((n["kind"] for n in testset["negative"] if a < n["end"] and b > n["start"]),
                    "carrier")
        false[kind] += 1
        if len(examples[kind]) < 6:
            examples[kind].append(testset["text"][a:b])
    return {"kinds": kinds, "false": false, "false_examples": examples}


def run(testset_path: Path, results: Path, names: list[str]) -> None:
    """Build and run each named recogniser and write its result file."""
    from tools import available
    testset = json.loads(testset_path.read_text(encoding="utf-8"))
    entries = load_dictionary(Path(testset["dictionary"]))
    results.mkdir(parents=True, exist_ok=True)
    tools = available()
    for name in names:
        if name not in tools:
            print(f"{name}: not available here")
            continue
        tool = tools[name]()
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        started = time.perf_counter()
        try:
            tool.build(entries)
            built = time.perf_counter() - started
            memory = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - before) / 2**20
            started = time.perf_counter()
            found = [(a, b, sorted(codes)) for a, b, codes in tool.tag(testset["text"])]
            tagged = time.perf_counter() - started
            long_text = (testset["letter"] + "\n\n") * 100
            started = time.perf_counter()
            tool.tag(long_text)
            speed = len(long_text) / (time.perf_counter() - started)
            letter = [(a, b, testset["letter"][a:b]) for a, b, _c in tool.tag(testset["letter"])]
        except Exception as error:  # a recogniser that fails is a result, too
            (results / f"{name}.json").write_text(json.dumps(
                {"tool": tool.name, "error": f"{type(error).__name__}: {error}"[:600]},
                ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{tool.name}: FAILED {type(error).__name__}: {str(error)[:200]}")
            continue
        outcome = score(testset, found)
        outcome.update(tool=tool.name, build_seconds=round(built, 2),
                       memory_mb=round(memory if sys.platform == "darwin" else memory * 1024, 0),
                       test_seconds=round(tagged, 3), chars_per_second=round(speed),
                       letter=letter)
        (results / f"{name}.json").write_text(json.dumps(outcome, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
        total = sum(k["n"] for k in outcome["kinds"].values())
        linked = sum(k["linked"] for k in outcome["kinds"].values())
        print(f"{tool.name}: linked {linked}/{total}, false {sum(outcome['false'].values())}, "
              f"build {built:.1f} s, {speed / 1000:.0f} thousand chars/s, {memory:.0f} MB")


def report(results: Path) -> None:
    """Print the results as Markdown tables."""
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(results.glob("*.json"))]
    good = [r for r in rows if "error" not in r]
    kinds = list(good[0]["kinds"])
    print("| Recogniser | " + " | ".join(kinds) + " | all |")
    print("|---|" + "---:|" * (len(kinds) + 1))
    for r in good:
        cells = [f"{r['kinds'][k]['linked']}/{r['kinds'][k]['n']}" for k in kinds]
        total = sum(v["n"] for v in r["kinds"].values())
        linked = sum(v["linked"] for v in r["kinds"].values())
        print(f"| {r['tool']} | " + " | ".join(cells) + f" | {100 * linked / total:.0f} % |")
    print()
    false = list(good[0]["false"])
    print("| Recogniser | " + " | ".join(false) + " | build s | MB | thousand chars/s | letter |")
    print("|---|" + "---:|" * (len(false) + 4))
    for r in good:
        print(f"| {r['tool']} | " + " | ".join(str(r["false"][k]) for k in false)
              + f" | {r['build_seconds']} | {r['memory_mb']:.0f} | "
              f"{r['chars_per_second'] / 1000:.0f} | {len(r['letter'])} |")
    for r in rows:
        if "error" in r:
            print(f"\n{r['tool']}: {r['error']}")


def read_brat(folder: Path) -> list[tuple[str, str, list[tuple[int, int, set[str]]]]]:
    """The units of a brat folder: its part, its text and its annotations with their labels."""
    units = []
    for text_file in sorted(folder.rglob("*.txt")):
        text = text_file.read_text(encoding="utf-8")
        gold = []
        for line in text_file.with_suffix(".ann").read_text(encoding="utf-8").splitlines():
            if not line.startswith("T"):
                continue
            _id, middle, _surface = line.split("\t", 2)
            label, positions = middle.split(" ", 1)
            spans = [tuple(int(n) for n in part.split()) for part in positions.split(";")]
            gold.append((spans[0][0], spans[-1][1], set(re.split(r"[|,+]", label))))
        units.append((text_file.parent.name.split("_")[0], text, gold))
    return units


def umls_of(table: Path) -> dict[str, set[str]]:
    """UMLS identifiers of each Wikidata item, from a CSV of item and identifier."""
    mapping: dict[str, set[str]] = {}
    with table.open(encoding="utf-8", newline="") as file:
        for item, cui in csv.reader(file):
            mapping.setdefault(item.rsplit("/", 1)[-1], set()).add(cui)
    return mapping


def corpus(folder: Path, table: Path, dictionary: Path, results: Path, names: list[str]) -> None:
    """Score each named recogniser against a corpus annotated by people."""
    from tools import available
    entries = load_dictionary(dictionary)
    mapping = umls_of(table)
    units = read_brat(folder)
    listed: dict[str, set[str]] = {}
    for term, code in entries:
        listed.setdefault(term.lower(), set()).update(mapping.get(code, ()))
    results.mkdir(parents=True, exist_ok=True)
    tools = available()
    for name in names:
        tool = tools[name]()
        tool.build(entries)
        parts: dict[str, dict[str, int]] = {}
        missed: list[str] = []
        for part, text, gold in units:
            row = parts.setdefault(part, {"gold": 0, "in dictionary": 0, "found": 0, "linked": 0,
                                          "tagged": 0, "tagged at gold": 0})
            found = [(a, b, {c for code in codes for c in mapping.get(code, ())})
                     for a, b, codes in tool.tag(text)]
            row["tagged"] += len(found)
            row["tagged at gold"] += sum(
                1 for a, b, _c in found if any(overlap((a, b), (g[0], g[1])) >= 0.5 for g in gold))
            for a, b, cuis in gold:
                row["gold"] += 1
                row["in dictionary"] += bool(listed.get(text[a:b].lower(), set()) & cuis)
                hits = [f for f in found if overlap((f[0], f[1]), (a, b)) >= 0.5]
                row["found"] += bool(hits)
                linked = any(f[2] & cuis for f in hits)
                row["linked"] += linked
                if not hits and len(missed) < 40:
                    missed.append(text[a:b])
        (results / f"corpus-{name}.json").write_text(json.dumps(
            {"tool": tool.name, "parts": parts, "missed": missed}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        total = {k: sum(p[k] for p in parts.values()) for k in next(iter(parts.values()))}
        print(f"{tool.name}: gold {total['gold']}, in dictionary {total['in dictionary']}, "
              f"found {total['found']}, linked {total['linked']}, tagged {total['tagged']} "
              f"({total['tagged at gold']} at gold)")


def texts(folder: Path, dictionary: Path, results: Path, names: list[str]) -> None:
    """Count what each named recogniser tags in a folder of plain texts."""
    from tools import available
    entries = load_dictionary(dictionary)
    documents = [p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.txt"))]
    results.mkdir(parents=True, exist_ok=True)
    tools = available()
    for name in names:
        tool = tools[name]()
        tool.build(entries)
        started = time.perf_counter()
        found = [[(a, b) for a, b, _c in tool.tag(text)] for text in documents]
        seconds = time.perf_counter() - started
        words: dict[str, int] = {}
        for text, spans in zip(documents, found, strict=True):
            for a, b in spans:
                words[text[a:b]] = words.get(text[a:b], 0) + 1
        (results / f"texts-{name}.json").write_text(json.dumps(
            {"tool": tool.name, "documents": len(documents),
             "characters": sum(len(d) for d in documents), "tagged": sum(len(s) for s in found),
             "seconds": round(seconds, 2), "spans": found,
             "most": sorted(words.items(), key=lambda item: -item[1])[:60]},
            ensure_ascii=False), encoding="utf-8")
        print(f"{tool.name}: {sum(len(s) for s in found)} places in {len(documents)} texts, "
              f"{seconds:.2f} s")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "make":
        make(Path(sys.argv[2]), Path(sys.argv[3]))
    elif command == "run":
        chosen = sys.argv[sys.argv.index("--tools") + 1].split(",")
        run(Path(sys.argv[2]), Path(sys.argv[3]), chosen)
    elif command == "report":
        report(Path(sys.argv[2]))
    elif command == "corpus":
        chosen = sys.argv[sys.argv.index("--tools") + 1].split(",")
        corpus(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), Path(sys.argv[5]), chosen)
    elif command == "texts":
        chosen = sys.argv[sys.argv.index("--tools") + 1].split(",")
        texts(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), chosen)
    else:
        print(__doc__)
