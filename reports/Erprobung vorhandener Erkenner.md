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
4. **QuickUMLS und xMEN sind kein Ersatz für den Kern.** QuickUMLS läuft (unter Python 3.11; unter 3.12
   scheitert nur eine veraltete Abhängigkeit), findet auf Deutsch aber weniger als der Prototyp, braucht ein
   Sprachmodell und lädt beim Start Daten aus dem Netz nach. xMEN belegt 1,1 GB und lässt sich nach frischer
   Installation nicht einmal laden. Was sich aus QuickUMLS lernen lässt, steht in Abschnitt 6.
5. **Auf echtem deutschem Fachtext findet jedes Wörterbuch-Verfahren weniger als die Hälfte.** Im
   Mantra-Korpus (von Menschen annotiert) findet der Prototyp mit dem freien Wörterbuch 38 % der Stellen und
   ordnet 20 % der richtigen Kennung zu; das beste Verfahren kommt auf 43 % und 23 %. Die Decke ist das
   Wörterbuch, nicht das Suchverfahren: Nur jede fünfte annotierte Stelle steht wörtlich darin (Abschnitt 5.1).
6. **Folgerung:** Der eigene Erkenner bleibt der Kern, weil nichts Fertiges besser ist und er klein, schnell
   und ohne Fehlalarme arbeitet. Über die Güte entscheiden aber die Pakete, nicht der Erkenner. Eine
   Schreibfehlertoleranz gehört höchstens als ausdrücklich gekennzeichneter Vorschlag hinein, nie als
   Zuordnung. Eine Schnittstelle für weitere Erkenner hält den Weg zu lernenden Verfahren offen.
7. **Das erste lernende Verfahren ist gemessen: die Suche nach Bedeutung** mit einem mehrsprachigen Modell,
   ohne Grafikkarte (Abschnitt 7). Als selbsttätige Zuordnung taugt sie nicht: Unterhalb einer sehr hohen
   Nähe verwechselt sie „Schilddrüsenkarzinom“ mit „Schilddrüsenadenom“. Als Vorschlag für einen Menschen ist
   sie stark, und sie arbeitet über Sprachgrenzen so gut wie innerhalb des Deutschen: Mit einem englischen
   Paket steigt die Zuordnung im Mantra-Korpus von 32 % auf 41 % der Stellen, weil mehr Konzepte überhaupt im
   Paket stehen.

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
| QuickUMLS (Original und Ableger von medspaCy, gleiches Ergebnis) | 150 | 100 | 150 | 100 | 62 | 7 | 100 | 0 | 71 % |
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
| QuickUMLS 1.4.2 (Original) | MIT | unter Python 3.11 ohne Weiteres; unter Python 3.12 scheitert der Bau der Abhängigkeit `leveldb` (Stand 2019), die eine dort entfernte Funktion benutzt, obwohl QuickUMLS sie in der Voreinstellung gar nicht braucht | nein | nicht gebaut; verlangt wie der Ableger ein Sprachmodell und lädt NLTK-Daten nach |
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

## 6 QuickUMLS, SimString und MedCAT genauer

Nachtrag vom selben Tag, auf die Frage, was sich aus den Verfahren lernen lässt. Beide Aufsätze sind im Volltext
gelesen: Soldaini und Goharian, „QuickUMLS: a fast, unsupervised approach for medical concept extraction“
(MedIR 2016), und Okazaki und Tsujii, „Simple and Efficient Algorithm for Approximate Dictionary Matching“
(Coling 2010).

### 6.1 Was die Aufsätze sagen

- **QuickUMLS** bildet zu jedem Wort alle Wortfolgen bis fünf Wörter, verwirft ungültige (Beginn oder Ende mit
  Artikel, Präposition oder Konjunktion; ein einzelnes Stoppwort; eine Zahl allein; über eine Satzgrenze
  hinweg), sucht zu jeder gültigen Folge ähnliche Wörterbucheinträge und behält am Ende die besten, die sich
  nicht überlappen (höchste Ähnlichkeit, bei Gleichstand die längere Folge).
- **SimString** liefert dafür die Suche: Jeder Eintrag wird in Buchstaben-Dreiergruppen zerlegt, und das
  Verfahren CPMerge findet exakt alle Einträge, deren Ähnlichkeit (Jaccard, Kosinus, Dice) über einer Schwelle
  liegt, ohne das ganze Wörterbuch durchzugehen: 1 ms je Anfrage bei 13,6 Millionen Einträgen, 20 ms beim UMLS.
- **Die Zahlen des QuickUMLS-Aufsatzes, englische klinische Notizen, vollständiges UMLS** (6 Millionen
  Einträge): mit genauer Übereinstimmung Genauigkeit 0,67 und Trefferquote 0,54 (Korpus i2b2) bzw. 0,87 und
  0,55 (THYME); mit Schwelle 0,7 steigt die Trefferquote auf 0,66 bzw. 0,67, die Genauigkeit fällt auf 0,60
  bzw. 0,78. cTAKES liegt bei Trefferquote 0,53 bis 0,55. **Auch mit einem vollständigen Wörterbuch findet ein
  Wörterbuch-Verfahren also nur gut die Hälfte bis zwei Drittel.** Unsere 38 bis 48 % mit 45.000 freien
  Begriffen sind daran gemessen nicht aus der Art.
- **Der Rat des SimString-Aufsatzes:** Kandidaten schnell und großzügig sammeln, dann jeden mit einem
  strengeren, fachlichen Maß prüfen.

### 6.2 Nachgemessen: SimString auf deutschem Text

Im Prüfstand nachgebaut (`simstring-0.9`, `-0.8`, `-0.7`: Wortfolgen bis fünf Wörter nach den Regeln von
QuickUMLS, Suche mit `pysimstring`, Kosinus über Dreiergruppen), dazu eine feste Schreibregel
(`proto-fold`: c mit k und z, ph mit f, th mit t).

| Verfahren | konstruiert: zugeordnet | dort Fehlalarme | Mantra: gefunden | Mantra: zugeordnet | Mantra: an annotierter Stelle |
|---|---:|---:|---:|---:|---:|
| Prototyp | 89 % | 0 | 38 % | 20 % | 79 % |
| Prototyp mit Schreibregel | 89 % | 0 | 38 % | 20 % | 79 % |
| SimString, Schwelle 0,9 | 77 % | 0 | 35 % | 19 % | 80 % |
| SimString, Schwelle 0,8 | 83 % | 0 | 47 % | 22 % | 68 % |
| SimString, Schwelle 0,7 | 90 % | 253 | 62 % | 23 % | 56 % |

- **Die unscharfe Suche findet mehr Stellen, aber nicht mehr richtige Kennungen.** Bei Schwelle 0,7 sind 62 %
  der annotierten Stellen markiert, zugeordnet aber nur 23 % (Prototyp 20 %). Was hinzukommt, hängt fast immer
  am falschen Begriff.
- **Auf den GraSCCo-Briefen** bringt schon Schwelle 0,9 Zuordnungen wie „Mobilisation“ zu „Immobilisation“,
  „brauchen“ zu „Rauchen“, „Einbruch“ zu „Armbruch“; Schwelle 0,8 bringt 809 zusätzliche Stellen, darunter
  39-mal „Chemotherapie“ als „Photochemotherapie“, „Zeichen“ als „Eiche“, „Klaus“ als „Laus“.
- **Warum es im Aufsatz gelingt und hier nicht:** Mit einem vollständigen Wörterbuch gewinnt meist der genaue
  Eintrag, die unscharfe Suche füllt nur Lücken. Mit einem dünnen Wörterbuch bekommt jedes unbekannte Wort
  seinen nächsten Nachbarn. Dazu kommt das Deutsche: Vorsilben und Zusammensetzungen ändern die Bedeutung bei
  hoher Ähnlichkeit der Zeichen.
- **Die feste Schreibregel** bringt auf den Briefen 17 zusätzliche Stellen, fast alle richtig („Colitis“,
  „Lactulose“, „Vasculitis“, „Zytokeratin“, „Metoklopramid“).

### 6.3 MedCAT

Gemessen wurde MedCAT 2.10.1 aus dem neuen Sammel-Repo `CogStack/cogstack-nlp` (so nennt es die Paketangabe);
das alte Repo `CogStack/MedCAT` ist archiviert. Ohne trainiertes Modell ist es ein Wörterbuch-Erkenner ohne
deutsche Regeln. Seine Besonderheit ist das Lernen, und zwar ohne PyTorch im Kern:

- **selbstüberwacht** aus unbeschrifteten Texten: Aus eindeutigen Namen lernt es, in welcher Umgebung ein
  Konzept steht, und löst damit mehrdeutige Namen auf;
- **aus den Bestätigungen und Korrekturen eines Menschen**, wie sie seine Prüfoberfläche ausgibt.

Beides braucht Wortvektoren für die Sprache der Texte; fertige deutsche habe ich nicht gefunden, man müsste sie
aus deutschen Fachtexten rechnen. Das Lernen hebt die Genauigkeit bei mehrdeutigen Namen, nicht die Trefferquote:
Finden kann MedCAT nur, was im Wörterbuch steht. Gemessen ist das hier nicht.

### 6.4 Wie oft ein Begriff mehrere Bedeutungen hat

Ein lernender Erkenner wie MedCAT wählt unter mehreren Bedeutungen. Wie oft das bei uns vorkommt, mit dem freien
Wörterbuch:

- In den 62 GraSCCo-Briefen haben 24 von 2.898 erkannten Stellen mehrere Bedeutungen, also 1 % („PET“, „ASS“).
- Im Mantra-Korpus sind von 407 gefundenen Stellen 191 nicht der gewählten Kennung zugeordnet. Bei 73 kennt
  Wikidata keine UMLS-Kennung zum Begriff, bei 110 hat der Begriff eine einzige Bedeutung, die Annotatoren haben
  aber eine andere, verwandte Kennung gewählt, und nur bei 8 standen mehrere Bedeutungen zur Wahl.
- Dagegen werden 675 der 1.082 annotierten Stellen (62 %) gar nicht gefunden.

Die Lücke liegt also beim Finden, nicht beim Auswählen. Mit mehr Paketen wird die Mehrdeutigkeit zunehmen;
heute ist sie das kleinere Problem.

### 6.5 Was daraus für den Entwurf folgt

1. **Erkennung in vier austauschbaren Stufen:** gültige Wortfolgen bilden, Kandidaten holen, jeden Kandidaten
   prüfen und bewerten, Überlappungen auflösen. Das ist der Aufbau von QuickUMLS und zugleich die Schnittstelle,
   an der ein anderer oder lernender Erkenner einsteigt.
2. **Die Regeln für gültige Wortfolgen** übernehmen: Fenster von fünf Wörtern (so groß ist es bei uns schon),
   kein Beginn oder Ende mit Funktionswort, nie ein einzelnes Stoppwort, nie eine Zahl allein, nicht über eine
   Satzgrenze. Das verhindert „hat“, „sowie“ und „als“ grundsätzlich, mit einer eigenen kleinen Stoppwortliste
   statt eines Sprachmodells.
3. **Jede Zuordnung trägt Art und Wert der Übereinstimmung** (genau, gebeugt, Schreibvariante, ungefähr mit
   Ähnlichkeit), und die Auflösung von Überlappungen ordnet danach: genau vor ungefähr, dann die längere Folge.
4. **Unscharfe Suche nur dort, wo ein Mensch auswählt:** im Prüffenster („diese Stelle wurde nicht erkannt:
   ähnliche Begriffe?“), in der Paketpflege (Dubletten) und in der Begriffssuche des Servers. SimString ist
   dafür die richtige Technik; als selbsttätige Zuordnung taugt sie mit unseren Paketen nicht.
5. **Lernen als zuschaltbares Modul**, von Anfang an mitgedacht: Die Annotationsdatei mit bestätigten und
   verworfenen Zuordnungen ist genau das, woraus MedCAT lernt. Das Modul liest Pakete und Bestätigungen, schlägt
   bei mehrdeutigen Begriffen die wahrscheinlichste Bedeutung vor und läuft ohne Grafikkarte.

## 7 Suche nach Bedeutung: das erste Lernmodul, gemessen

Abschnitt 6.4 hat gezeigt, dass die Lücke beim Finden liegt: 62 % der annotierten Stellen stehen in keinem
Paket in diesen Worten. Ein Verfahren, das dort ansetzt, ist die Suche nach Bedeutung: Ein Modell, das auf den
Namen von Konzepten trainiert ist, macht aus jeder Zeichenkette einen Vektor; Namen desselben Konzepts liegen
nah beieinander, gleich in welcher Schreibweise oder Sprache. Eine Wortfolge im Text bekommt den nächsten Namen
des Pakets.

### 7.1 Aufbau und Kosten

- **Modell:** `cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR` von Hugging Face (Fassung 47b6bd0), ein
  XLM-RoBERTa-Modell, nach seiner Modellkarte mit den Namen des UMLS 2020AB trainiert. Die Gewichte haben
  1,11 GB. **Die Modellkarte nennt keine Lizenz**; der Programmcode dazu steht unter MIT. Das englische
  Schwestermodell derselben Gruppe (`SapBERT-from-PubMedBERT-fulltext`) trägt bei Hugging Face die Angabe
  Apache 2.0, das mehrsprachige und seine große Fassung tragen keine (Abfrage der Modellangaben am
  26.11.2026). Das Trainingsmaterial geben die Autoren wegen der UMLS-Lizenz nicht weiter. Ob ein auf dem UMLS
  trainiertes Modell weitergegeben werden darf, ist vor jeder Auslieferung zu klären. Die Aufsätze zum Modell
  habe ich nicht gelesen; hier steht nur, was die Modellkarte sagt und was gemessen ist.
- **Umgebung:** PyTorch 2.15 und transformers 5.24, zusammen 800 MB, nur Prozessor (Apple M1 Max, acht
  Fäden). Eine Grafikkarte wird auch dort nicht benutzt, wo eine da ist.
- **Kosten:** Laden 18 Sekunden, 2,4 GB Arbeitsspeicher. 400 bis 850 Zeichenketten je Sekunde. Die 38.129
  Namen des Wörterbuchs brauchen einmal 64 Sekunden und 117 MB auf der Platte. Die 62 GraSCCo-Briefe
  (244.780 Zeichen) dauern 105 Sekunden, also 1,7 Sekunden je Brief; der Prototyp braucht für alle 0,12
  Sekunden.
- **Zwei Messungen:** `bench.py link` nimmt die 1.082 annotierten Stellen des Mantra-Korpus als gegeben und
  fragt nur, ob sie der richtigen Kennung zugeordnet werden. Die Erkenner `meaning-0.95` bis `meaning-0.8`
  messen die ganze Erkennung: Was der Prototyp findet, bleibt; jede übrige Wortfolge (nach den Regeln aus
  Abschnitt 6.5) bekommt den nächsten Namen, wenn er mindestens so nah ist wie die Schwelle.
- **Was „richtig“ heißt:** die Kennung, die die Annotatoren gewählt haben. Das ist streng: Bei 167 Stellen
  trägt der Wikidata-Eintrag mit genau dem Namen der Stelle eine andere oder keine UMLS-Kennung. Diese Fälle
  stehen in einer eigenen Spalte und zählen weder als richtig noch als falsch.

### 7.2 Gegebene Stellen, deutsches Wörterbuch

| | Stellen | Anteil |
|---|---:|---:|
| annotierte Stellen | 1.082 | |
| das Konzept steht überhaupt im Wörterbuch | 422 | 39 % |
| wörtlich gefunden | 221 | 20 % |
| nach den Regeln des Prototyps | 268 | 25 % |
| der nächste Name ist der richtige | 341 | 32 % |
| der richtige Name ist unter den fünf nächsten | 377 | 35 % |

Von den 422 Stellen, deren Konzept das Wörterbuch kennt, ordnen die Regeln 64 % zu, der nächste Name 81 %, und
bei 89 % ist der richtige unter den fünf nächsten.

Der nächste Name allein sagt aber nicht, ob er passt. Entscheidend ist die Nähe:

| Nähe ab | zugeordnet | richtige Kennung | gleicher Name, andere Kennung | anderer Name |
|---:|---:|---:|---:|---:|
| 0,98 | 430 | 249 | 167 | 14 |
| 0,95 | 525 | 281 | 167 | 77 |
| 0,9 | 577 | 299 | 167 | 111 |
| 0,85 | 657 | 319 | 167 | 171 |
| 0,8 | 760 | 329 | 167 | 264 |
| 0,7 | 1.012 | 340 | 167 | 505 |

Die Spalte „anderer Name“ habe ich je Stufe gelesen (eigene Einschätzung, nicht fachlich geprüft):

- **ab 0,95** (40 von 44 verschiedenen Paaren gelesen) fast durchweg richtig: Beugung und Mehrzahl
  („hämorrhagischen Schock“, „Knorpelschäden“), umgestellte Wörter („eingeschränkter Nierenfunktion“ zu
  „Nierenfunktionseinschränkung“, „Entfernen von Haaren“ zu „Haarentfernung“). Die Kennung weicht meist nur
  ab, weil Wikidata sie nicht führt.
- **0,9 bis 0,95** (alle 17 Paare): zwölf richtig, fünf falsch, darunter „Absorption“ zu „Adsorption“,
  „Blutgerinnsel“ zu „Blutsenkung“, „Lupus“ zu „Lupus vulgaris“.
- **0,85 bis 0,9** (40 von 42 Paaren): gut ein Drittel richtig. Falsch sind unter anderem
  „Schilddrüsenkarzinom“ zu „Schilddrüsenadenom“, „Infektionen des unteren Respirationstrakts“ zu „Infektion
  der oberen Atemwege“, „Herzminutenvolumens“ zu „Herzschlagvolumen“, „Arzt“ zu „Medizinmann“, „Schwindel“ zu
  „Schwingel“.
- **unter 0,85** überwiegend falsch: „Absetzens“ zu „Enthauptung“, „Verfahren“ zu „Exekution“, „Sicherheit“
  zu „Unsicherheit“.

Der Grund ist derselbe wie bei SimString (Abschnitt 6.2): Fehlt der richtige Begriff im Paket, bekommt die
Stelle den nächstbesten, und der liegt oft nah.

### 7.3 Ganze Erkennung, deutsches Wörterbuch

| Verfahren | Mantra: gefunden | Mantra: zugeordnet | markiert | davon an annotierter Stelle | Briefe: Stellen |
|---|---:|---:|---:|---:|---:|
| Prototyp | 38 % | 20 % | 443 | 79 % | 2.898 |
| dazu Bedeutung ab 0,95 | 41 % | 22 % | 487 | 79 % | 3.013 |
| dazu Bedeutung ab 0,9 | 45 % | 23 % | 562 | 74 % | 3.378 |
| dazu Bedeutung ab 0,85 | 52 % | 24 % | 717 | 67 % | 4.381 |
| dazu Bedeutung ab 0,8 | 60 % | 24 % | 1.039 | 54 % | 6.263 |

- **Ab 0,95 kommt wenig hinzu, und fast nur Richtiges.** Im Mantra-Korpus 44 Stellen, 36 davon an annotierter
  Stelle. In den Briefen 115 Stellen in 84 verschiedenen Paaren, die ich alle gelesen habe: rund 90 sind
  richtig. Es sind Schreibvarianten („Hepatische Encephalopathie“, „Lactulose“, „Hysterectomie“), gebeugte
  Mehrwortbegriffe („stationären Aufenthaltes“, „klinischen Untersuchung“), abgekürzte und abgeschnittene
  Wörter („resp. Insuffizienz“, „Echokardiogr“) und Tippfehler („Ramiprilil“, „Konjunktivits“). 13 sind klar
  falsch („hoch“ zu „High“, „wach“ zu „Wachs“, „Abschluss“ zu „Ausschluss“, „Ausstrahlung“ zu „Bestrahlung“),
  dazu siebenmal „L-Thyroxin“ zu „DL-Thyroxin“, nach der Kennung ein anderer Stoff; fünf sind strittig
  („ergotherapeutische“ zu „Ergotherapeut“).
- **Zwischen 0,9 und 0,95** kommen in den Briefen rund 360 Stellen hinzu, überwiegend falsch: „Kontrolle“ zu
  „Kontrollbedingung“ (30-mal), „Vorstellung“ zu „Darstellung“ (12-mal), „Unterschenkel“ zu „Oberschenkel“
  (fünfmal), „Metamizol“ zu „Methimazol“ (dreimal). Richtig und wertvoll sind einzelne, etwa „Pantozol“ zu
  „Pantoprazol“ (achtmal, Handelsname zum Wirkstoff) und „Nierenvene“ zu „Vena renalis“.
- **Darunter** fast nur Unsinn: „Aufnahme“ zu „Photographie“ (59-mal), „Chemotherapie“ zu
  „Chemoradiotherapie“ (39-mal), „rein“ zu „Niere“ (13-mal).
- **Was ab 0,95 hinzukommt, kann zum guten Teil auch eine Regel:** Die Schreibtabelle c, k und z gibt es
  schon (Abschnitt 6.2). Neu ist der Hinweis auf gebeugte Adjektive im Mehrwortbegriff („chronischer
  Bronchitis“ für „chronische Bronchitis“): Die Regel erlaubt eine Endung bisher nur am letzten Wort.

### 7.4 Über Sprachgrenzen: deutscher Text, englisches Paket

Deutsche Namen sind in freien Quellen dünn, englische reichlich. Für dieselben Wikidata-Einträge habe ich
deshalb die englischen Namen geholt (Bezeichnungen und Aliasse, CC0) und drei Pakete gebildet.

| Paket | Namen | Konzept im Paket | wörtlich | Regeln | nächster Name richtig | unter den fünf nächsten |
|---|---:|---:|---:|---:|---:|---:|
| deutsch (17.631 Konzepte) | 38.129 | 422 | 221 | 268 | 341 | 377 |
| englisch, dieselben Konzepte | 73.087 | 422 | 82 | 87 | 336 | 393 |
| englisch, dazu alle annotierten Konzepte, die Wikidata kennt | 73.498 | 636 | 94 | 101 | 441 | 563 |
| deutsch und englisch zusammen | 106.922 | 636 | 255 | 303 | 441 | 539 |

- **Die Sprache des Pakets spielt für die Suche nach Bedeutung keine Rolle.** Mit den englischen Namen
  derselben Konzepte ist der nächste Name bei 336 Stellen der richtige, mit den deutschen bei 341; die Regeln
  finden im englischen Paket nur 87 (gemeinsame lateinische und gleich geschriebene Wörter). Beispiele:
  „Körpergewicht“ zu „body weight“, „Sportverletzungen“ zu „sports injuries“, „Arzneimitteln gegen Krebs“ zu
  „anticancer drug“, „Krankenhausaufenthalt“ zu „hospitalization“.
- **Mit einem breiteren englischen Paket steigt die Zuordnung mit der Abdeckung:** 441 Stellen (41 %) statt
  341, weil 636 statt 422 Stellen überhaupt ein Konzept im Paket haben. Das ist die erste Maßnahme in diesem
  Bericht, die die Decke des Wörterbuchs hebt.
- **Die Nähe ist über Sprachgrenzen kleiner:** Richtige Paare liegen oft zwischen 0,8 und 0,9. Ab 0,9 sind
  im breiten englischen Paket 289 von 459 Zuordnungen nach der Kennung richtig, ab 0,8 sind es 407 von 741;
  unter den übrigen sind viele richtige Übersetzungen mit anderer Kennung („Blut“ zu „blood“, „Knie“ zu
  „knee“), aber auch „Salz“ zu „saliva“ und „chemisch“ zu „chemist“.

Ganze Erkennung im Mantra-Korpus:

| Paket und Verfahren | gefunden | zugeordnet | markiert | davon an annotierter Stelle |
|---|---:|---:|---:|---:|
| deutsch, Prototyp | 38 % | 20 % | 443 | 79 % |
| nur englisch, Prototyp | 10 % | 7 % | 175 | 53 % |
| nur englisch, dazu Bedeutung ab 0,9 | 34 % | 21 % | 495 | 65 % |
| nur englisch, dazu Bedeutung ab 0,85 | 46 % | 26 % | 719 | 60 % |
| deutsch und englisch, Prototyp | 40 % | 22 % | 515 | 72 % |
| deutsch und englisch, dazu Bedeutung ab 0,95 | 44 % | 24 % | 563 | 73 % |
| deutsch und englisch, dazu Bedeutung ab 0,9 | 50 % | 27 % | 689 | 68 % |
| deutsch und englisch, dazu Bedeutung ab 0,85 | 57 % | 29 % | 882 | 60 % |

Mit einem rein englischen Paket und der Suche nach Bedeutung wird ein deutscher Text so gut zugeordnet wie mit
dem deutschen Wörterbuch und den Regeln (21 % gegen 20 %).

**Eine Warnung aus derselben Messung:** Englische Namen gehören nicht in die Regelsuche eines deutschen
Textes. Mit dem zweisprachigen Paket markieren die Regeln in den Briefen 3.692 statt 2.898 Stellen, und das
meiste davon ist falsch: „gut“ (englisch für Darm, 31-mal), „Es“ und „In“ (Elementzeichen, 70-mal), „14“,
„fast“, „Ferner“, „Probleme“, „Berlin“ (achtmal), dazu Abkürzungen mit anderer deutscher Bedeutung („AZ“,
„ED“, „PE“, „OA“). Für die Schutzprüfung in PseudonyMed wäre „Berlin“ als Fachwort ein Schaden. Jeder Begriff
trägt deshalb seine Sprache, und die Regeln suchen nur Begriffe in der Sprache des Textes.

### 7.5 Was daraus folgt

1. **Nicht als selbsttätige Zuordnung.** Unter einer Nähe von 0,95 ist jede zweite bis dritte Zuordnung
   falsch, darunter gefährliche (Karzinom und Adenom, untere und obere Atemwege, Metamizol und Methimazol).
   Ab 0,95 ist sie verlässlich genug, bringt aber wenig und zum guten Teil, was Regeln billiger können.
2. **Als Vorschlag für einen Menschen ist sie stark.** Steht das Konzept im Paket, ist der richtige Name in
   neun von zehn Fällen unter den fünf nächsten. Für die Frage im Prüffenster „diese Stelle wurde nicht
   erkannt: welche Begriffe kommen in Frage?“ ist das besser als die Ähnlichkeit der Zeichen aus Abschnitt 6.
3. **Sie öffnet englische Pakete für deutsche Texte.** Das ist der eigentliche Gewinn, weil die Decke bisher
   das dünne deutsche Wörterbuch war. Gemessen ist das mit Wikidata-Namen und höchstens 18.000 Konzepten;
   wie es sich mit einem Paket von Millionen Namen verhält (mehr Abdeckung, mehr Verwechslungen), ist offen.
4. **Sie ersetzt keinen Menschen:** Was in keinem Paket steht, bekommt den nächstbesten Namen.
5. **Kosten und Lizenz** sprechen für ein zuschaltbares Modul: 1,9 GB für Modell und Laufzeit, 2,4 GB
   Arbeitsspeicher, knapp zwei Sekunden je Brief, und ein Modell, das der Anwender selbst laden muss, solange
   seine Lizenz nicht geklärt ist. Der Kern bleibt ohne.

   **Entschieden am 26.11.2026:** Die Suche nach Bedeutung wird mit `lexcor` 0.3 als zuschaltbares Modul
   gebaut, das im Prüffenster vorschlägt und nichts selbst zuordnet.
6. **Zwei Regeln sind zu prüfen**, bevor ein Modell für sie bemüht wird: Endungen auch an den vorderen
   Wörtern eines Mehrwortbegriffs, und die Sprache eines Begriffs als Bedingung der Regelsuche.

## 8 Was sich übernehmen lässt

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

## 9 Was diese Erprobung nicht zeigt

- **Wie gut die Erkennung auf echten Arztbriefen mit besseren Paketen wäre.** Gemessen ist nur das freie
  Wikidata-Wörterbuch. Der Deutsche MeSH, die deutsche SNOMED-CT-Ausgabe, die Alpha-ID-SE und eine Liste von
  Handelsnamen sollten die Trefferquote deutlich heben; wie weit, ist nicht gemessen. Ein von Menschen
  annotiertes Korpus deutscher Arztbriefe mit Konzeptkennungen habe ich frei zugänglich nicht gefunden.
- **Was andere lernende Verfahren hier erreichen.** Gemessen ist eines, die Suche nach Bedeutung
  (Abschnitt 7). Veröffentlichte Systeme mit Sprachmodellen berichten für dieses Korpus höhere
  Zuordnungsraten; das habe ich weder nachgelesen noch nachgemessen. Nicht gemessen ist auch, wie sich die
  Suche nach Bedeutung mit einem Paket von Millionen Namen verhält und was ein kleineres Modell kostet.
- **Mehrdeutigkeit.** Wo ein Begriff mehrere Bedeutungen hat, liefert der Prototyp alle. MedCATs Auflösung aus
  dem Zusammenhang konnte mangels deutschem Modell nicht gemessen werden.
- **Terminologieserver.** Hermes und Snowstorm Lite brauchen eine SNOMED-CT-Ausgabe, die nur mit Ihrer
  Affiliate-Lizenz über MLDS zu laden ist.

## 10 Wiederholen

```
python bench/bench.py make  <fachklassen_de.csv.gz>  testset.json
python bench/bench.py run   testset.json results/ --tools proto
python bench/bench.py run   testset.json results/ --tools iamsystem-fuzzy
python bench/bench.py report results/
python bench/bench.py corpus <Mantra/German> <qid_cui.csv> <fachklassen_de.csv.gz> results/ --tools proto
python bench/bench.py texts  <GraSCCo>  <fachklassen_de.csv.gz> results/ --tools proto
python bench/bench.py link   <Mantra/German> <qid_cui.csv> <fachklassen_de.csv.gz> results/ --lower
python bench/bench.py corpus <Mantra/German> <qid_cui.csv> <fachklassen_de.csv.gz> results/ --tools meaning-0.95
```

Die Korpora sind nicht Teil des Repos: Mantra GSC von
[github.com/mi-erasmusmc/Mantra-Gold-Standard-Corpus](https://github.com/mi-erasmusmc/Mantra-Gold-Standard-Corpus),
GraSCCo von [Zenodo 6539131](https://zenodo.org/records/6539131). `qid_cui.csv` ist die Wikidata-Abfrage
`SELECT ?item ?cui WHERE { ?item wdt:P2892 ?cui }` als CSV.

Für die Suche nach Bedeutung (`link`, `meaning-*`) braucht es `torch`, `transformers`, `sentencepiece` und
`protobuf`, den Ordner des Modells in `LEXTERM_BENCH_MODEL` und, um die Vektoren eines Wörterbuchs zu behalten,
einen Ordner in `LEXTERM_BENCH_CACHE` (Einzelheiten in `bench/README.md`). Die englischen Namen stammen aus
Wikidatas Schnittstelle `wbgetentities` (Bezeichnungen und Aliasse der Einträge des Wörterbuchs und der
annotierten Konzepte), als CSV in der Form des Wörterbuchs.

Jeder Erkenner einzeln, damit Zeit und Speicher ihm allein gehören. Installiert waren für diese Messung:
spaCy 3.8.18, MedCAT 2.10.1, iamsystem 0.6.1, FlashText 2.7, pyahocorasick 2.3.1, EDS-NLP 0.24.0,
`medspacy-quickumls` in einer eigenen Umgebung.
