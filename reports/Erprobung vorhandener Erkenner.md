<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# Erprobung vorhandener Erkenner auf deutschem Text

Stand 26. November 2026. Die [Bestandsaufnahme](Bestandsaufnahme%20quelloffener%20Werkzeuge.md) hatte die
Werkzeuge nur gelesen. Hier sind sie installiert und mit demselben deutschen Wörterbuch auf denselben Texten
gemessen: zuerst auf einer Testmenge mit konstruierter Wahrheit (Abschnitte 1 bis 4), dann auf echten deutschen
Texten (Abschnitt 5). Zwei Ausschlusskriterien gelten: keine Grafikkarte oder andere besondere Hardware, und das
Ergebnis muss sich als Programm paketieren lassen.

## Ergebnis

1. **Keine der Bibliotheken erkennt deutschen Text ohne Zutun so gut wie die Regeln aus PseudonyMed.** Alle
   reinen Wörterbuch-Sucher finden 64 % der Teststellen: Sie scheitern an Beugungsendungen („Blutdrucks“,
   „Diagnosen“) und an umschriebenen Umlauten („Haematurie“). Der Prototyp nach dem Entwurf von lexterm findet
   89 % ohne einen Fehlalarm.
2. **Auf der konstruierten Testmenge ist eine Bibliothek besser als der Prototyp: iamsystem** mit einer
   deutschen Endungsregel und Toleranz für einen Schreibfehler (98 %, vier Fehlalarme). **Auf echten Briefen
   kehrt sich das um:** Dieselbe Toleranz macht aus „Papille“ „Pupille“, aus „Gewicht“ „Gesicht“ und aus
   „Kollegen“ „Kollagen“ (Abschnitt 5.2). Die konstruierte Testmenge hat das Verfahren geschönt.
3. **MedCAT bringt ohne trainiertes Modell nichts für Deutsch.** Es findet 63 %, kennt keine Endungen und ist
   rund 240-mal langsamer als der Prototyp. Seine Stärke, Mehrdeutigkeiten aus dem Zusammenhang aufzulösen,
   setzt ein Training auf deutschen Texten voraus, das es nicht fertig gibt.
4. **QuickUMLS und xMEN scheiden nach den Kriterien aus.** QuickUMLS lässt sich im Original hier nicht
   installieren, braucht ein Sprachmodell und lädt beim Start Daten aus dem Netz nach. xMEN belegt 1,1 GB und
   lässt sich nach frischer Installation nicht einmal laden.
5. **Auf echtem deutschem Fachtext findet jedes Wörterbuch-Verfahren weniger als die Hälfte.** Im
   Mantra-Korpus (von Menschen annotiert) findet der Prototyp mit dem freien Wörterbuch 38 % der Stellen und
   ordnet 20 % der richtigen Kennung zu; das beste Verfahren kommt auf 43 % und 23 %. Die Decke ist das
   Wörterbuch, nicht das Suchverfahren: Nur jede fünfte annotierte Stelle steht wörtlich darin (Abschnitt 5.1).
6. **Folgerung:** Der eigene Erkenner bleibt der Kern, weil nichts Fertiges besser ist und er klein, schnell
   und ohne Fehlalarme arbeitet. Über die Güte entscheiden aber die Pakete, nicht der Erkenner. Eine
   Schreibfehlertoleranz gehört höchstens als ausdrücklich gekennzeichneter Vorschlag hinein, nie als
   Zuordnung. Eine Schnittstelle für weitere Erkenner hält den Weg zu lernenden Verfahren offen.

## 1 Aufbau

- **Maschine:** Apple M1 Max, 64 GB, nur Prozessor. Python 3.12.
- **Wörterbuch:** 45.489 deutsche Begriffe aus Wikidata mit Wikidata-Kennung als Code (CC0), die Liste aus
  PseudonyMed. Jedes Werkzeug bekommt genau dieses Wörterbuch.
- **Testmenge mit bekannter Wahrheit:** 947 Begriffe aus dem Wörterbuch, in Trägersätze gesetzt, deren Wörter
  nachweislich nicht im Wörterbuch stehen. Jeder Begriff steht in einer von acht Formen:

  | Form | Beispiel | Anzahl |
  |---|---|---:|
  | wie gelistet | „Polyarthritis“ | 150 |
  | mit Umlaut | „Hyperurikämie“ | 100 |
  | mehrere Wörter | „Psychosomatische Medizin“ | 150 |
  | in Großbuchstaben | „NATRIUMSULFAT“ | 100 |
  | mit Beugungsendung | „Samenblasen“ | 147 |
  | Umlaut umschrieben | „Hueftumfang“ | 100 |
  | Abkürzung | „IBD“ | 100 |
  | ein Buchstabe vertauscht | „Kontaktvarfolgung“ | 100 |

- **Text, in dem nichts gefunden werden darf:** gewöhnliche Wörter, die großgeschrieben eine Abkürzung wären
  („hat“ und HAT, „ass“ und ASS), 39 Zusammensetzungen, die einen Begriff nur enthalten („Handschuh“,
  „Herzlich“, „Zahnrad“), und 14 Sätze Alltagsprosa.
- **Ein erfundener Entlassbrief** (1.700 Zeichen) für den Vergleich an zusammenhängendem Text und, hundertfach
  wiederholt, für das Tempo.
- **Gezählt wird:** eine Stelle gilt als zugeordnet, wenn das Werkzeug sie findet und ihr den richtigen Code
  gibt. Jedes Werkzeug läuft in einem eigenen Prozess.

Der Prüfstand liegt in [`bench/`](../bench/) und lässt sich wiederholen.

## 2 Zuordnung je Form

Richtig zugeordnete Stellen; die letzte Spalte über alle 947.

| Werkzeug | gelistet | Umlaut | mehrere Wörter | Großbuchst. | Endung | umschrieben | Abkürzung | Tippfehler | alle |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Prototyp lexterm** | 150 | 100 | 150 | 100 | **147** | **100** | 100 | 0 | **89 %** |
| iamsystem, Endungen + ein Schreibfehler | 150 | 100 | 150 | 100 | 132 | 93 | 100 | **100** | **98 %** |
| iamsystem, Endungen | 150 | 100 | 150 | 100 | 111 | 7 | 100 | 0 | 76 % |
| EDS-NLP, unscharf (SimString) | 150 | 100 | 150 | 100 | 32 | 42 | 100 | 7 | 72 % |
| QuickUMLS (Ableger von medspaCy) | 150 | 100 | 150 | 100 | 62 | 7 | 100 | 0 | 71 % |
| iamsystem, wie geliefert | 150 | 100 | 150 | 100 | 0 | 7 | 100 | 0 | 64 % |
| EDS-NLP, genau | 150 | 100 | 150 | 100 | 0 | 7 | 100 | 0 | 64 % |
| spaCy PhraseMatcher | 150 | 100 | 150 | 100 | 0 | 7 | 100 | 0 | 64 % |
| pyahocorasick mit Wortgrenzen | 150 | 100 | 150 | 100 | 0 | 7 | 100 | 0 | 64 % |
| FlashText | 150 | 100 | 150 | 100 | 0 | 7 | 100 | 0 | 64 % |
| MedCAT, Wörterbuch-Erkenner | 106 | 73 | 147 | 72 | 120 | 9 | 79 | 0 | 64 % |
| MedCAT, Standard-Erkenner | 150 | 99 | 149 | 100 | 0 | 7 | 89 | 0 | 63 % |

Die sieben Treffer bei „umschrieben“ sind Begriffe, die das Wörterbuch zufällig in beiden Schreibweisen führt.

## 3 Fehlalarme, Tempo, Speicher

| Werkzeug | gewöhnl. Wort | Zusammensetzung | Prosa | Aufbau (s) | Speicher (MB) | Tausend Zeichen je s |
|---|---:|---:|---:|---:|---:|---:|
| **Prototyp lexterm** | 0 | 0 | 0 | 0,1 | 14 | 2.385 |
| iamsystem, Endungen + ein Schreibfehler | 2 | 0 | 2 | 0,7 | 88 | 471 |
| iamsystem, Endungen | 2 | 0 | 1 | 0,4 | 33 | 1.446 |
| iamsystem, wie geliefert | 2 | 0 | 0 | 0,3 | 21 | 1.305 |
| EDS-NLP, unscharf | 2 | 0 | 0 | 5,1 | 76 | 44 |
| EDS-NLP, genau | 2 | 0 | 0 | 4,5 | 97 | 242 |
| QuickUMLS (Ableger) | 1 | 0 | 0 | 3,8 | nicht vergleichbar | 83 |
| spaCy PhraseMatcher | 2 | 0 | 0 | 7,8 | 175 | 298 |
| pyahocorasick mit Wortgrenzen | 2 | 0 | 0 | 0,04 | 26 | 399 |
| FlashText | 2 | 0 | 0 | 0,2 | 70 | 9.000 |
| MedCAT, Wörterbuch-Erkenner | 0 | 26 | 2 | 1,5 | 123 | 8 |
| MedCAT, Standard-Erkenner | 0 | 0 | 0 | 2,1 | 108 | 10 |

Was hinter den Zahlen steht:

- **„hat“ und „ass“:** Jeder Sucher, der Groß- und Kleinschreibung gleichsetzt, macht aus dem Hilfsverb „hat“
  die Erkrankung HAT und aus „ass“ das Medikament ASS. Die Regel „Abkürzungen nur wie geschrieben“ verhindert
  das.
- **FlashText in der Lieferfassung** hält Umlaute für Wortgrenzen und findet im Brief „ten“ in „Qualitäten“ und
  „hrt“ in „fortgeführt“. Mit der Angabe, dass Umlaute Buchstaben sind, verschwindet das.
- **MedCATs Wörterbuch-Erkenner** prüft keine Wortgrenzen: „Handschuh“, „Herzlich“, „Dienstag“ werden zu
  Körperteilen und Zeitangaben.
- **Die Endungsregel und die Fehlertoleranz von iamsystem** erzeugen im Brief „Wacher“, „sowie“ und „Herztöne“,
  in der Prosa „Bücher“ und „Verwaltung“ als Treffer. Der Prototyp verlangt einen Wortstamm von vier Buchstaben
  und vermeidet das, findet dafür keine Tippfehler.
- **Im Entlassbrief** findet der Prototyp 47 Stellen, die genauen Sucher 44: Es fehlen ihnen „Diagnosen“,
  „Kontraindikationen“ und „Blutdrucks“.
- **Bei zehnfachem Wörterbuch** (455.000 Einträge, die Größenordnung von SNOMED CT) bleiben die schlanken
  Kandidaten brauchbar: Prototyp 1,8 s Aufbau, 232 MB, 577.000 Zeichen je Sekunde; iamsystem 6,4 s, 259 MB,
  550.000; pyahocorasick 0,5 s, 187 MB, 409.000.

## 4 Installation, Hardware, Paketieren

| Werkzeug | Lizenz | Installation | Besondere Hardware | Als Programm paketiert (PyInstaller) |
|---|---|---|---|---|
| Prototyp lexterm | MIT | nur Python | nein | 17 MB, läuft |
| iamsystem 0.6.1 | MIT | 5 Pakete | nein | 23 MB, läuft, wenn die Daten von `anyascii` mitgepackt werden |
| pyahocorasick 2.3.1 | BSD-3 | 1 Paket (C-Erweiterung) | nein | nicht gebaut; unkritisch |
| FlashText 2.7 | MIT | 1 Paket | nein | nicht gebaut; unkritisch |
| spaCy 3.8 (PhraseMatcher) | MIT | 44 Pakete | nein | PseudonyMed paketiert spaCy bereits |
| EDS-NLP 0.24 | BSD-3 | 72 Pakete, darunter pandas und pyarrow | nein | nicht gebaut; schwer |
| MedCAT 2.10 | Apache-2.0 | 29 Pakete (mit spaCy 53); das Zusatzmodul für Verneinung zieht PyTorch nach | nein für den Kern | 227 MB, läuft, wenn alle Teile von MedCAT ausdrücklich mitgepackt werden |
| QuickUMLS 1.4 (Original) | MIT | **scheitert**: die Abhängigkeit `leveldb` lässt sich auf Apple Silicon mit Python 3.12 nicht bauen | nein | entfällt |
| QuickUMLS (Ableger `medspacy-quickumls`) | MIT | geht; verlangt das spaCy-Modell für Deutsch und lädt beim Start die NLTK-Stoppwörter aus dem Netz in den Benutzerordner | nein | nicht gebaut; das Nachladen widerspricht dem Betrieb ohne Netz |
| xMEN 1.0.8 | Apache-2.0 | 94 Pakete, 1,1 GB mit PyTorch und FAISS; **lässt sich danach nicht laden** (NumPy 1.26 gegen pyarrow, das NumPy 2 verlangt) | läuft laut Anleitung auch ohne Grafikkarte, voreingestellt mit | scheidet aus |

Nicht gemessen, weil sie Englisch voraussetzen oder nur andere Werkzeuge einhüllen: scispaCy, cTAKES, medspaCy
(für Deutsch ohne Regeln), medkit.

## 5 Echte deutsche Texte

### 5.1 Mantra GSC: von Menschen annotiert

Der deutsche Teil des Mantra-Korpus (Erasmus MC, GPL-3.0): 100 Medline-Titel, 100 Abschnitte aus
Arzneimittelinformationen, 50 Patentansprüche, darin 1.082 Stellen mit UMLS-Kennung. Die Wikidata-Codes des
Wörterbuchs sind über Wikidatas Verweis auf UMLS umgerechnet. „Gefunden“ heißt: Die Stelle ist markiert.
„Zugeordnet“ heißt: mit der Kennung, die die Annotatoren gewählt haben.

| Werkzeug | gefunden | zugeordnet | selbst markiert | davon an annotierter Stelle |
|---|---:|---:|---:|---:|
| iamsystem, Endungen + ein Schreibfehler | 43 % | 23 % | 690 | 70 % |
| iamsystem, Endungen | 41 % | 22 % | 543 | 78 % |
| **Prototyp lexterm** | **38 %** | **20 %** | 443 | 79 % |
| EDS-NLP, unscharf | 32 % | 17 % | 377 | 81 % |
| pyahocorasick mit Wortgrenzen | 31 % | 17 % | 375 | 79 % |
| MedCAT, Standard-Erkenner | 29 % | 16 % | 353 | 80 % |

Nach Art des Begriffs (Prototyp, freies Wörterbuch):

| Art | Stellen | gefunden | zugeordnet |
|---|---:|---:|---:|
| Erkrankungen und Symptome | 330 | 48 % | 26 % |
| Substanzen und Arzneien | 301 | 35 % | 19 % |
| Verfahren | 151 | 25 % | 9 % |
| Anatomie | 117 | 45 % | 26 % |
| Lebewesen (auch „Patienten“, „Ärzte“) | 75 | 27 % | 7 % |
| Physiologie | 49 | 45 % | 37 % |

Was das bedeutet:

- **Das Wörterbuch ist die Decke.** Nur 221 der 1.082 Stellen (20 %) stehen wörtlich mit passender Kennung im
  Wörterbuch. Von den 729 annotierten Konzepten kennt Wikidata 430, mit deutschem Namen 350.
- **Auch das bestmögliche freie Wörterbuch hilft wenig.** Nimmt man alle deutschen Namen hinzu, die Wikidata zu
  den annotierten Konzepten führt (1.135 Namen), steigt der Prototyp von 38 auf 41 % gefunden und von 20 auf
  24 % zugeordnet.
- **Was fehlt,** sind Handelsnamen („Remicade“, „ReFacto“), allgemeine Wörter des Fachs („Schwindel“,
  „Überdosierung“, „Krankheit“) und Umschreibungen aus mehreren Wörtern („niedriger Blutdruck“, „verschwommenes
  Sehen“, „Lupus-ähnliche Syndrome“). Die ersten beiden sind eine Frage besserer Pakete, das dritte kann ein
  Wörterbuch-Verfahren grundsätzlich nicht.
- **„Zugeordnet“ ist eine Untergrenze.** Wo UMLS mehrere fast gleichbedeutende Konzepte führt, zählt nur das
  von den Annotatoren gewählte, und die Umrechnung über Wikidata ist lückenhaft.
- **Das Korpus ist kein Arztbrief.** Es annotiert auch Allgemeines („Patienten“, „Maschinen“, „planen“), das in
  einer Akte niemand markiert haben will.

### 5.2 GraSCCo: erfundene Arztbriefe ohne Annotation

62 deutsche Arztbriefe (Zenodo 6539131, 245.000 Zeichen). Hier gibt es keine geprüfte Wahrheit, nur den
Vergleich, wer was markiert.

| Werkzeug | markierte Stellen | Zeit für alle Briefe |
|---|---:|---:|
| Prototyp lexterm | 2.898 | 0,13 s |
| pyahocorasick mit Wortgrenzen | 2.649 | 0,02 s |
| MedCAT, Standard-Erkenner | 2.580 | 1,8 s |
| iamsystem, Endungen + ein Schreibfehler | 4.102 | 13,3 s |

Die 1.200 Stellen, die iamsystem mehr markiert, habe ich mit dem jeweils zugeordneten Begriff ausgezählt:

- **Seine Endungsregel** (zusammen mit seiner eigenen Vereinheitlichung der Schreibung) bringt 481 Stellen,
  die häufigsten sind falsch: „sowie“ als „SoWi“ (65-mal), „Kopf“ als „köpfen“ (21-mal), „hat“ als „HAT“
  (12-mal), „fast“ als „Fasten“, „starke“ als „Stärke“.
- **Die Toleranz für einen Schreibfehler** bringt weitere 245, überwiegend falsch: „Zeichen“ als „Seichen“,
  „vertragen“ als „Vertrauen“, „Kollegen“ als „Kollagen“, „Papille“ als „Pupille“, „Gewicht“ als „Gesicht“,
  „Schwindel“ als das Gras „Schwingel“, „Serologie“ als „Sexologie“.
- **Richtig sind darunter die Schreibvarianten** mit c, k und z („Colitis“ und „Kolitis“, „Lactulose“ und
  „Laktulose“, „Kreatinin“ und „Creatinin“) und echte Tippfehler („Medilkation“). Für die Varianten ist eine
  feste Regel der bessere Weg als eine allgemeine Fehlertoleranz.

Auch der Prototyp markiert Unerwünschtes: „Zeit“, „Luft“, „stehen“ und „Mutter“ gehören zu seinen häufigsten
Treffern, weil das Wörterbuch sie als Konzepte führt. Das ist keine Frage des Erkenners, sondern der Auswahl
und Pflege der Pakete.

## 6 Was sich übernehmen lässt

- **Aus iamsystem die Abkürzungsliste** („BB“ steht für „Blutbild“) als Idee für die Pakete, und die
  Schreibvarianten mit c, k und z als feste Regel. **Die allgemeine Schreibfehlertoleranz nicht** als
  Zuordnung; allenfalls als gekennzeichneter Vorschlag für Text aus der Texterkennung, den ein Mensch bestätigt.
- **pyahocorasick** als Suchtechnik, falls die Wortsuche des Prototyps bei sehr großen Paketen nicht mehr reicht.
  Die Messung zeigt, dass das bei 455.000 Einträgen nicht nötig ist.
- **Von MedCAT und INCEpTION die Arbeitsweise**, nicht den Code: maschinell vorschlagen, menschlich bestätigen,
  aus den Bestätigungen lernen.
- **Eine Schnittstelle für weitere Erkenner** („Plugin“): Jeder Erkenner bekommt Text und Pakete und liefert
  Stellen mit Codes; die Annotationsdatei vermerkt, von wem eine Zuordnung stammt. So lässt sich MedCAT mit
  einem selbst trainierten deutschen Modell später zuschalten, ohne dass lexterm es mitliefert. Der Prüfstand
  ist schon so gebaut: jedes Werkzeug hinter denselben zwei Aufrufen.

## 7 Was diese Erprobung nicht zeigt

- **Wie gut die Erkennung auf echten Arztbriefen mit besseren Paketen wäre.** Gemessen ist nur das freie
  Wikidata-Wörterbuch. Der Deutsche MeSH, die deutsche SNOMED-CT-Ausgabe, die Alpha-ID-SE und eine Liste von
  Handelsnamen sollten die Trefferquote deutlich heben; wie weit, ist nicht gemessen. Ein von Menschen
  annotiertes Korpus deutscher Arztbriefe mit Konzeptkennungen habe ich frei zugänglich nicht gefunden.
- **Was lernende Verfahren hier erreichen.** Veröffentlichte Systeme mit Sprachmodellen berichten für dieses
  Korpus höhere Zuordnungsraten; das habe ich weder nachgelesen noch nachgemessen, und sie fallen unter die
  Ausschlusskriterien.
- **Mehrdeutigkeit.** Wo ein Begriff mehrere Bedeutungen hat, liefert der Prototyp alle. MedCATs Auflösung aus
  dem Zusammenhang konnte mangels deutschem Modell nicht gemessen werden.
- **Terminologieserver.** Hermes und Snowstorm Lite brauchen eine SNOMED-CT-Ausgabe, die nur mit Ihrer
  Affiliate-Lizenz über MLDS zu laden ist.

## 8 Wiederholen

```
python bench/bench.py make  <fachklassen_de.csv.gz>  testset.json
python bench/bench.py run   testset.json results/ --tools proto
python bench/bench.py run   testset.json results/ --tools iamsystem-fuzzy
python bench/bench.py report results/
python bench/bench.py corpus <Mantra/German> <qid_cui.csv> <fachklassen_de.csv.gz> results/ --tools proto
python bench/bench.py texts  <GraSCCo>  <fachklassen_de.csv.gz> results/ --tools proto
```

Die Korpora sind nicht Teil des Repos: Mantra GSC von
[github.com/mi-erasmusmc/Mantra-Gold-Standard-Corpus](https://github.com/mi-erasmusmc/Mantra-Gold-Standard-Corpus),
GraSCCo von [Zenodo 6539131](https://zenodo.org/records/6539131). `qid_cui.csv` ist die Wikidata-Abfrage
`SELECT ?item ?cui WHERE { ?item wdt:P2892 ?cui }` als CSV.

Jeder Erkenner einzeln, damit Zeit und Speicher ihm allein gehören. Installiert waren für diese Messung:
spaCy 3.8.18, MedCAT 2.10.1, iamsystem 0.6.1, FlashText 2.7, pyahocorasick 2.3.1, EDS-NLP 0.24.0,
`medspacy-quickumls` in einer eigenen Umgebung.
