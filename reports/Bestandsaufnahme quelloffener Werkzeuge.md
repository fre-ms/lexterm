<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# Bestandsaufnahme: quelloffene Werkzeuge für Fachbegriff-Erkennung und Terminologie

Stand 26. November 2026. Anlass: Die Erkennung medizinischer Fachbegriffe soll aus PseudonyMed in eine eigene
Bibliothek (Arbeitsname lexterm) ausgekoppelt werden. Die Frage ist, was es quelloffen schon gibt und was davon
sich nutzen lässt, statt es neu zu bauen.

## Kurzfassung

1. **Einen Terminologieserver muss lexterm nicht bauen.** Es gibt mehrere quelloffene, aktive Server. Für SNOMED CT
   auf einem einzelnen Rechner passen Hermes (mit hades als FHIR-Schicht) und Snowstorm Lite. lexterm sollte sich
   als Client mit einem FHIR-Terminologieserver verbinden können.
2. **Für die Lizenzfrage ist der Server ein guter Weg, aber kein Freibrief.** SNOMED CT ist in Deutschland
   kostenfrei, braucht aber eine Affiliate-Lizenz beim BfArM. Wer den Server betreibt, braucht sie; lexterm selbst
   liefert dann nichts Lizenzpflichtiges aus. Einzelheiten in Abschnitt 2.
3. **Einen fertigen deutschen Erkenner habe ich nicht gefunden.** Die großen Werkzeuge (MedCAT, QuickUMLS,
   scispaCy, cTAKES) sind auf Englisch und UMLS ausgerichtet; medspaCy führt Deutsch ausdrücklich als Sprache ohne
   Regeln. Der Erkenner aus PseudonyMed bleibt deshalb die Grundlage.
4. **Für die Prüfoberfläche gibt es ein starkes Vorbild: INCEpTION.** Es ist für Forschungsteams gebaut und als
   Java-Webanwendung zu schwer für ein kleines Arbeitsplatzwerkzeug. lexterm sollte aber dessen Austauschformat
   (UIMA CAS) schreiben und lesen können, damit niemand eingesperrt ist.
5. **Es gibt mehr frei nutzbare deutsche Begriffsquellen als gedacht:** den Deutschen MeSH (ZB MED, CC BY 4.0),
   ICD-10-GM, OPS und ATC als FHIR-Pakete des BfArM und die deutsche SNOMED-CT-Ausgabe mit inzwischen über
   130.000 übersetzten Konzepten.
6. **Neu zu bauen bleibt ein überschaubarer Kern:** der deutsche Wörterbuch-Erkenner mit Mehrfachzuordnung je
   Paket, der Prüfstatus (maschinell, bestätigt, verworfen), das kleine Fenster und die Ausgabe nach FHIR und
   medDAV. Dafür habe ich nichts Fertiges gefunden.

## 1 Vorgehen und Grenzen

- Kandidaten habe ich aus eigener Kenntnis des Feldes zusammengestellt und dann einzeln nachgeprüft.
- **Lizenz, Aktivität und Sprache** stammen direkt aus den Repositorien (GitHub-Schnittstelle, Abruf am
  26.11.2026) und aus deren README-Dateien. „Letzte Änderung“ ist der letzte Push.
- **Lizenz- und Zugangsfragen** (SNOMED CT, MII-Server, BfArM-Pakete) stammen von den Seiten des BfArM und der
  Service Unit der Medizininformatik-Initiative.
- **Fachaufsätze habe ich nicht im Volltext gelesen.** Wo ich einen Aufsatz nenne, ist es ein Hinweis aus der
  Suche, keine geprüfte Aussage. Solche Stellen sind gekennzeichnet.
- Ausprobiert habe ich keines der Werkzeuge. Aussagen zur Erkennungsgüte auf deutschen Texten fehlen deshalb; das
  wäre der nächste Schritt (Abschnitt 7).
- Kommerzielle Produkte (etwa Averbis Health Discovery oder die Werkzeuge von ID Berlin) sind nicht quelloffen und
  hier nicht untersucht.

## 2 Terminologieserver

Ein Terminologieserver hält Codesysteme vor und beantwortet Fragen dazu über eine genormte Schnittstelle. Bei
FHIR sind das vor allem vier Operationen: `$lookup` (was bedeutet dieser Code?), `$validate-code` (gibt es ihn?),
`$expand` (welche Codes gehören zu dieser Werteliste?) und `$translate` (welcher Code entspricht ihm in einem
anderen System?).

| Werkzeug | Lizenz | Letzte Änderung | Was es ist | Für lexterm |
|---|---|---|---|---|
| [Hermes](https://github.com/wardle/hermes) | EPL-2.0 | 09/2026 | SNOMED-CT-Server, Kommandozeile und Bibliothek. Liest eine heruntergeladene Ausgabe in eine einzige Datenbankdatei; braucht weder Elasticsearch noch PostgreSQL. Volltextsuche, Abfragesprache ECL. Lädt Ausgaben für Mitgliedsländer selbst über MLDS. | Erste Wahl für SNOMED CT auf einem Einzelrechner. Läuft auf der Java-Laufzeit. |
| [hades](https://github.com/wardle/hades) | EPL-2.0 | 06/2026 | FHIR-R4-Terminologieserver, der auf Hermes aufsetzt. | Macht Hermes über FHIR ansprechbar. |
| [Snowstorm Lite](https://github.com/IHTSDO/snowstorm-lite) | Apache-2.0 | 11/2026 | Kleiner FHIR-Terminologieserver für SNOMED CT von SNOMED International. Läuft nach dem Indexieren mit etwa 500 MB Arbeitsspeicher. Mehrere Sprachen. | Gleichwertige Alternative zu Hermes mit hades. |
| [Snowstorm](https://github.com/IHTSDO/snowstorm) | Apache-2.0 | 11/2026 | Der große Server von SNOMED International, auch für das Pflegen von Ausgaben. Braucht Elasticsearch. Kennt neben SNOMED CT auch LOINC und ICD-10. | Für einen Arbeitsplatz zu schwer. |
| [HAPI FHIR JPA Server](https://github.com/hapifhir/hapi-fhir-jpaserver-starter) | Apache-2.0 | 11/2026 | Allgemeiner FHIR-Server mit Terminologiediensten. | Möglich, aber schwer; nur wenn ohnehin ein FHIR-Server läuft. |
| [TermX](https://github.com/termx-health/termx-server) | MIT | 11/2026 | Terminologieserver mit Pflegeoberfläche; kleine Gemeinde (7 Sterne). | Beobachten. |
| Snow Owl | Apache-2.0 | archiviert 07/2026 | Früher verbreiteter Server. | Scheidet aus. |
| Ontoserver (CSIRO) | nicht quelloffen | | Der Server, den die Medizininformatik-Initiative betreibt. | Nur über deren Dienst nutzbar. |

**Öffentliche und zentrale Dienste in Deutschland**

- **Zentraler Terminologieserver des BfArM** ([terminologien.bfarm.de](https://terminologien.bfarm.de/release-notes.html)):
  stellt ICD-10-GM, OPS und ATC als FHIR-Pakete bereit (`bfarm.terminologien.icd10gm` 2026.0.0 vom 1.12.2025,
  `bfarm.terminologien.atcgm` 2026.0.0 vom 19.12.2025). Kostenfrei; vor dem Herunterladen sind
  Nutzungsbedingungen zu bestätigen. Alpha-ID-SE gibt es dort nur als Textdatei.
- **Service Unit Terminological Services der Medizininformatik-Initiative** ([mii-termserv.de](https://mii-termserv.de/)):
  betreibt einen Ontoserver. Der Zugang ist **nicht öffentlich**: Er setzt einen Vertrag und ein
  Client-Zertifikat voraus. Für eine einzelne Sprechstunde ist das kein gangbarer Weg.
- **tx.fhir.org** von HL7: öffentlich, für Werkzeuge und Nachschlagen gedacht. medRDS hat dort schon LOINC-Codes
  nachgeschlagen. Für den laufenden Betrieb und für alles, was Rückschlüsse auf Patienten zulässt, ungeeignet.

**Lizenzlage SNOMED CT in Deutschland** (nach den
[Fragen und Antworten des BfArM](https://www.bfarm.de/DE/Kodiersysteme/_FAQ/SNOMED-CT/SNOMED-CT-Lizenzvergabe/faq-liste.html))

- Deutschland ist seit 1. Januar 2021 Mitglied; das BfArM führt das National Release Center.
- Nötig ist eine Affiliate-Lizenz, beantragt über das Portal MLDS. Sie ist für Lizenznehmer und Endanwender auf
  dem Gebiet der Bundesrepublik kostenfrei.
- „Üblicherweise beantragt die Betreiberin oder der Betreiber einer Software eine Affiliate-Lizenz.“ Endanwender
  brauchen keine eigene.
- Wer ein Produkt vertreibt, das SNOMED CT enthält, braucht eine Affiliate-Lizenz und führt Sublizenzen für
  seine Endanwender.
- Jährlich bis 15. Januar ist eine Nutzungserklärung abzugeben.
- Die deutsche Ausgabe (National Edition Germany) erscheint zweimal im Jahr. Im Mai 2026 waren über 118.000
  Konzepte übersetzt, nach einer Zwischenausgabe im August 2026 über 130.000. Die Übersetzung ist bewusst
  unvollständig und folgt Anwendungsfällen.

**Was das für lexterm heißt**

- Die Annahme „über einen Terminologieserver lässt sich SNOMED CT leichter einbinden“ stimmt im Kern: lexterm
  liefert dann keine SNOMED-Inhalte aus, sondern spricht mit einem Server, den der Anwender mit seiner eigenen
  Lizenz betreibt. Das ist meine Schlussfolgerung aus den Regeln oben; die Seite des BfArM behandelt
  Terminologieserver nicht ausdrücklich, und das hier ist keine Rechtsberatung.
- Die Lizenz entfällt dadurch nicht. Wer den Server betreibt, braucht sie. Für Sie als Betreiber Ihrer eigenen
  Software ist das ein kostenfreier Antrag und eine jährliche Erklärung.
- Ein Server ersetzt das Paket nicht ganz. Um Begriffe in einem Text zu finden, muss die Begriffsliste lokal als
  Index vorliegen; man kann nicht jedes Wort einzeln beim Server erfragen. lexterm baut diesen Index auf dem
  Rechner des Anwenders aus dessen lizenzierter Quelle (über den Server oder aus den Ausgabedateien). Der Server
  bleibt wertvoll für alles danach: Bedeutung nachschlagen, Codes prüfen, in andere Systeme übersetzen.
- Texte mit Patientenbezug gehen nie an einen fremden Server. Der Server läuft lokal.

## 3 Erkenner

Gemeint sind Programme, die Begriffe in Text finden und einem Konzept zuordnen (im Englischen „entity linking“
oder „concept normalisation“).

| Werkzeug | Lizenz | Letzte Änderung | Was es tut | Für lexterm |
|---|---|---|---|---|
| [MedCAT](https://github.com/CogStack/cogstack-nlp) (King's College London) | Apache-2.0 | 11/2026 | Findet Konzepte und verknüpft sie mit SNOMED CT, UMLS oder anderen Vokabularen; lernt aus unbeschrifteten Texten, Mehrdeutigkeiten aufzulösen. Zusatzmodul für Verneinung und Ähnliches (braucht PyTorch). Das alte Repo `CogStack/MedCAT` ist seit 2025 archiviert; die Entwicklung läuft im Sammel-Repo weiter. | Nächster Verwandter. Kein fertiges deutsches Modell gefunden; öffentliche Modelle setzen eine UMLS-Lizenz voraus. Als wählbare zweite Quelle denkbar, nicht als Kern. |
| [QuickUMLS](https://github.com/Georgetown-IR-Lab/QuickUMLS) | MIT | 11/2026 | Schnelle, unscharfe Wörterbuchsuche über eine lokale UMLS-Installation; Sprache wählbar. | An das UMLS und dessen Lizenz gebunden; eigene Pakete passen nicht hinein. |
| [scispaCy](https://github.com/allenai/scispacy) | Apache-2.0 | 12/2025 | spaCy-Modelle und Verknüpfung mit UMLS, MeSH und anderen. | Englisch. |
| [medspaCy](https://github.com/medspacy/medspacy) | MIT | 06/2026 | Klinische Bausteine für spaCy: Kontext (Verneinung, Unsicherheit), Abschnitte, Zielregeln. | Laut eigener Sprachtabelle für Deutsch weder Kontext- noch Abschnittsregeln. Aufbau als Vorbild brauchbar. |
| [Apache cTAKES](https://github.com/apache/ctakes) | Apache-2.0 | 11/2026 | Großes klinisches Analysesystem in Java. | Englisch, schwer. |
| [xMEN](https://github.com/hpi-dhc/xmen) (Hasso-Plattner-Institut) | Apache-2.0 | 12/2024 | Ordnet schon gefundene Begriffe sprachübergreifend Konzepten zu, auch wenn kein deutscher Name im Vokabular steht (Zeichen-n-Gramme, SapBERT-Einbettungen, Nachsortierung). Beispiel für Deutsch liegt bei. | Der Stand der Forschung für Deutsch. Braucht PyTorch, einen Vektorindex und in der Voreinstellung eine Grafikkarte. Denkbar als spätere Quelle von Vorschlägen. |
| [GERNERMED](https://github.com/frankkramer-lab/GERNERMED) | MIT | 10/2023 | Neuronales Modell, das in deutschen Texten medizinische Angaben findet. | Findet nur, ordnet keinen Code zu; ruht. |
| [EDS-NLP](https://github.com/aphp/edsnlp) (Pariser Kliniken) | BSD-3 | 11/2026 | Regelbasierte Bausteine für französische Arztbriefe: Wörterbuch-Erkenner, Verneinung, Hypothese, Familienanamnese. | Französisch. Der Zuschnitt ist dem von lexterm am ähnlichsten und ein gutes Vorbild. |
| [medkit](https://github.com/medkit-lib/medkit) | MIT | 08/2026 | Werkzeugkasten mit Erkennern, Verneinung und Umwandlern (etwa brat). | Französische Herkunft; Vorbild für das Mitführen der Herkunft jeder Annotation. |
| [iamsystem](https://github.com/scossin/iamsystem_python) | MIT | 04/2024 | Schlanker Wörterbuch-Erkenner für große Listen (über 300.000 Einträge) mit Abkürzungen und unscharfer Suche. | Dem eigenen Erkenner am nächsten; kleine Gemeinde, ruht. Ideen übernehmen. |
| [OAK](https://github.com/INCATools/ontology-access-kit) | Apache-2.0 | 11/2026 | Einheitlicher Zugriff auf Ontologien (lokal oder über Dienste), mit einfacher Textannotation. | Nützlich als Importweg für Ontologien wie HPO. |
| [OntoGPT](https://github.com/monarch-initiative/ontogpt) | BSD-3 | 11/2026 | Zieht Konzepte mit einem Sprachmodell aus Text. | Nicht wiederholbar und nur mit lokalem Modell datenschutzgerecht; widerspricht dem Ziel „gleiche Eingabe, gleiches Ergebnis“. |
| NLP2FHIR | keine Lizenzangabe | 07/2022 | Wandelte Erkennungsergebnisse in FHIR um. | Ruht; für die FHIR-Ausgabe gibt es nichts Fertiges. |

**Bausteine für einen eigenen Erkenner:** spaCy (MIT), pyahocorasick (BSD-3, schnelle Suche vieler Zeichenketten
zugleich), FlashText (MIT), spaczz (MIT, unscharfe Suche für spaCy).

**Einordnung**

- Keines der Werkzeuge bringt deutsche Regeln oder ein deutsches Modell mit, das ohne UMLS-Lizenz nutzbar wäre.
- Die leistungsfähigsten (MedCAT, xMEN) brauchen Modelle und PyTorch. Das passt schlecht zu einem kleinen
  Programm, das als Begleitprogramm von medorello mitgeliefert wird.
- Hinweis aus der Suche, nicht im Volltext gelesen: Mehrere Arbeiten zu deutschem Text übersetzen ihn erst ins
  Englische und lassen dann MedCAT laufen, mit mäßigem Ergebnis. Das spricht nicht für einen fertigen deutschen
  Weg.
- Der Erkenner aus PseudonyMed ist klein, läuft ohne Netz, liefert wiederholbare Ergebnisse und ist an deutschen
  Texten erprobt (Flexion, Bindestrichteile, Umlaute, Mehrwortbegriffe). Er findet nur, was wörtlich in einem
  Paket steht. Diese Grenze teilt er mit allen Wörterbuch-Erkennern; sie lässt sich durch gute deutsche Pakete
  (Abschnitt 6) am wirksamsten verschieben.

## 4 Kontext: Verneinung, Verdacht, Familienanamnese

Ein gefundener Begriff sagt noch nicht, dass er für den Patienten gilt („kein Hinweis auf“, „Mutter mit“).

- Das verbreitete Verfahren heißt ConText (als NegEx begonnen): feste Auslösewörter mit einer Reichweite im Satz.
  medspaCy und EDS-NLP setzen es um, aber nicht für Deutsch.
- Für Deutsch gibt es eine Liste von 506 Auslösern des DFKI
  ([Negex für deutsche klinische Texte](http://macss.dfki.de/german_trigger_set.html), Cotik und andere 2016).
  Die Lizenz der Liste habe ich nicht gefunden; den Aufsatz habe ich nicht im Volltext gelesen.
- Für lexterm ist das eine spätere, abschaltbare Stufe: Kontextmerkmale als Vorschlag an der Annotation, über die
  ein Mensch entscheidet.

## 5 Prüfoberflächen und Austauschformate

| Werkzeug | Lizenz | Letzte Änderung | Was es tut | Für lexterm |
|---|---|---|---|---|
| [INCEpTION](https://github.com/eclipse-inception/inception) (TU Darmstadt, jetzt Eclipse) | Apache-2.0 | 11/2026 | Annotationsplattform mit Verknüpfung zu Wissensbasen und Vorschlägen, die man annimmt oder verwirft. Liest Text, PDF, HTML; schreibt UIMA CAS (XMI und JSON). Fremde Programme können über eine [Schnittstelle](https://github.com/inception-project/inception-external-recommender) Vorschläge liefern. | Das Vorbild für „maschinell vorgeschlagen, menschlich bestätigt“. Java-Webanwendung für Teams und Korpora. |
| MedCATtrainer (im [MedCAT-Repo](https://github.com/CogStack/cogstack-nlp)) | Apache-2.0 | 11/2026 | Weboberfläche, in der Fachleute MedCATs Zuordnungen bestätigen, verwerfen und ergänzen. | Genau der gewünschte Ablauf, aber fest an MedCAT gebunden. |
| [Label Studio](https://github.com/HumanSignal/label-studio) | Apache-2.0 | 11/2026 | Allgemeine Beschriftungsplattform. | Kennt keine Mehrfachzuordnung zu Codesystemen. |
| [doccano](https://github.com/doccano/doccano) | MIT | 04/2026 | Einfache Textbeschriftung. | Wie oben. |
| [brat](https://github.com/nlplab/brat) | eigene Lizenzdatei | 07/2024 | Der Klassiker; sein Dateiformat ist weit verbreitet. | Ruht; das Format lohnt als Export. |
| [dkpro-cassis](https://github.com/dkpro/dkpro-cassis) | Apache-2.0 | 10/2026 | Liest und schreibt UIMA CAS in Python. | Der Weg, um mit INCEpTION Dateien auszutauschen. |

**Formate, an die sich lexterm halten kann**

- **UIMA CAS (JSON oder XMI):** das Austauschformat von INCEpTION und der deutschen Forschungsprojekte.
- **W3C Web Annotation:** beschreibt eine Textstelle über Position und Wortlaut samt Umgebung, sodass sie auch nach
  kleinen Textänderungen wiedergefunden wird. Gut für die eigene Annotationsdatei.
- **FHIR:** `CodeableConcept` für die Zuordnung, `Provenance` für „wer hat wann bestätigt“, `CodeSystem` und
  FHIR-Pakete für den Austausch der Begriffspakete.

## 6 Deutsche Begriffsquellen

| Quelle | Bedingungen | Umfang | In lexterm |
|---|---|---|---|
| Wikidata | CC0 | rund 39.000 deutsche Begriffe, schon in PseudonyMed | mitliefern |
| [Deutscher MeSH](https://www.zbmed.de/open-science/terminologien/deutscher-mesh/) (ZB MED) | CC BY 4.0, dazu Nutzungsbedingungen | 107.299 Begriffe in der Ausgabe 2026 (Angabe aus einer Pressemeldung, Seite von ZB MED nicht selbst gelesen); XML und CSV | mitliefern, wenn die Nutzungsbedingungen es zulassen; sonst Bauanleitung |
| Orphanet | CC BY 4.0 (wie in PseudonyMed genutzt) | 6.400 seltene Erkrankungen mit Synonymen | mitliefern |
| ICD-10-GM, OPS, ATC | Bedingungen des BfArM; amtliche Texte dürfen nicht verändert werden | FHIR-Pakete des BfArM | Bauanleitung oder Abruf auf Wunsch |
| Alpha-ID-SE | Bedingungen des BfArM | Diagnosebezeichnungen der Alltagssprache mit ICD-10-GM-Code; nur Textdatei | Bauanleitung |
| SNOMED CT, deutsche Ausgabe | Affiliate-Lizenz, kostenfrei in Deutschland | über 130.000 übersetzte Konzepte | über lokalen Server oder Import der Ausgabedateien |
| LOINC, UMLS | eigene Lizenzen mit Anmeldung | | Bauanleitung |
| Roche Lexikon, AMDP | Verlagswerke | | nur lokaler Import aus der eigenen lizenzierten Quelle |

Für die Erkennung in deutschen Arztbriefen dürften die Alpha-ID-SE und der Deutsche MeSH den größten Zugewinn
bringen, weil sie viele Bezeichnungen je Konzept enthalten. Das ist eine Einschätzung, keine Messung.

## 7 Folgerungen für lexterm

**Übernehmen statt bauen**

- Terminologieserver: Hermes mit hades oder Snowstorm Lite für SNOMED CT; lexterm spricht FHIR als Client.
- Paketaustausch: FHIR `CodeSystem` und FHIR-Pakete (so veröffentlicht das BfArM seine Klassifikationen), daneben
  CSV.
- Austausch der Annotationen: UIMA CAS über dkpro-cassis, damit INCEpTION dieselben Dateien öffnet.
- Suchtechnik: pyahocorasick oder spaCys Wortgruppen-Suche, falls der eigene Erkenner bei mehreren hunderttausend
  Begriffen zu langsam wird.

**Selbst bauen**

- Den deutschen Wörterbuch-Erkenner (aus PseudonyMed), erweitert um Mehrfachzuordnung je Paket.
- Paketverwaltung mit Lizenzangabe und der Regel „nicht weitergebbar heißt: nicht mitliefern“.
- Annotationsdatei mit Herkunft und Prüfstatus; das kleine Fenster.
- Ausgabe nach FHIR und medDAV.

**Offen halten**

- Eine Schnittstelle für weitere Vorschlagsquellen. Jede Zuordnung nennt, woher sie stammt (eigener Erkenner,
  MedCAT, xMEN, Mensch). So lässt sich später ein lernendes Verfahren zuschalten, ohne den Kern umzubauen.
- lexterm als Vorschlagsquelle für INCEpTION, falls einmal ein Team oder ein Forschungskorpus annotiert.

**Vor weiterem Ausbau messen**

Ein kleiner Prüfstand wie bei optdoc: eigener Erkenner gegen MedCAT mit denselben Paketen gegen xMEN, auf frei
zugänglichen deutschen Texten. Als Daten kommen nach den Suchtreffern GraSCCo (erfundene deutsche Arztbriefe) und
BRONCO150 (onkologische Entlassbriefe mit ICD-, OPS- und ATC-Codes, nur mit Nutzungsvereinbarung) in Frage.
Beide habe ich nicht geprüft.

## 8 Nicht geprüft

- Güte der Werkzeuge auf deutschen Texten (nichts ausprobiert).
- Volltexte der genannten Aufsätze.
- Genaue Nutzungsbedingungen des Deutschen MeSH und der BfArM-Pakete im Hinblick auf das Mitliefern.
- Lizenz der deutschen NegEx-Auslöserliste.
- Ob das BfArM SNOMED CT künftig über seinen zentralen Terminologieserver anbietet (in einer Kommentierung von
  2024 wurde das gewünscht).
- Inhalt und Umfang deutscher Begriffe im UMLS.

## Quellen

Repositorien (Lizenz und Stand am 26.11.2026 über die GitHub-Schnittstelle abgerufen): siehe die Verweise in den
Tabellen.

- BfArM: [Eine SNOMED-CT-Lizenz beantragen und MLDS nutzen](https://www.bfarm.de/DE/Kodiersysteme/Terminologien/SNOMED-CT/Lizenz/_node.html)
- BfArM: [Fragen und Antworten zur SNOMED-CT-Lizenzvergabe](https://www.bfarm.de/DE/Kodiersysteme/_FAQ/SNOMED-CT/SNOMED-CT-Lizenzvergabe/faq-liste.html)
- BfArM: [6. National Edition Germany für SNOMED CT](https://www.bfarm.de/DE/Kodiersysteme/News/SNOMED_Deutsche_National_Edition_Mai_2026.html)
- BfArM: [Zentraler Terminologieserver, Release Notes](https://terminologien.bfarm.de/release-notes.html)
- BfArM: [Downloads der Klassifikationen](https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html)
- MII SU-TermServ: [Startseite](https://mii-termserv.de/), [Lizenzen](https://mii-termserv.de/licenses), [Produktionsserver](https://mii-termserv.de/blogs/2024-11-12-production-ontoserver/)
- ZB MED: [Deutscher MeSH](https://www.zbmed.de/open-science/terminologien/deutscher-mesh/); Meldung zur Ausgabe 2026: [MedLabPortal](https://medlabportal.de/zb-med-veroeffentlicht-deutschen-mesh-2026/)
- DFKI: [Negex für deutsche klinische Texte](http://macss.dfki.de/german_trigger_set.html)
- Hinweise aus der Suche, nicht im Volltext gelesen: xMEN ([JAMIA Open 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC11671143)), MedCAT ([arXiv 2010.01165](https://arxiv.org/pdf/2010.01165)), Herzinsuffizienz-Pipeline mit MedCAT auf übersetzten deutschen Briefen ([Scientific Reports 2026](https://www.nature.com/articles/s41598-026-48771-1)), Übersicht deutscher klinischer Korpora ([arXiv 2412.00230](https://arxiv.org/pdf/2412.00230))
