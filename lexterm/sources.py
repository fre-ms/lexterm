# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""Where the terminologies come from: what to get, where, under which conditions, and how
lexterm takes it in.

lexterm never fetches anything itself.  Terminologies are given out under conditions a
person has to accept, some under a licence, so a person downloads the file and lexterm reads
it.  This module says how, in German and English, for the command line (``lexterm
sources``), for the documentation and for any window that offers the import: one text, kept
in one place.  The addresses were read on 27 November 2026.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lexcor.language import language as current

Words = tuple[str, str]  # German, English


@dataclass(frozen=True)
class Source:
    """One place terminologies come from."""

    key: str
    name: Words
    what: Words
    conditions: Words
    steps: tuple[Words, ...]
    links: tuple[tuple[Words, str], ...]
    command: str


SOURCES: tuple[Source, ...] = (
    Source(
        "bfarm",
        ("Kodiersysteme des BfArM", "Coding systems of the BfArM"),
        ("ICD-10-GM, OPS, ATC mit DDD, ICD-O-3, ICF, KDL, ORPHAcodes, die deutsche Variante von"
         " LOINC und weitere, jeweils als FHIR CodeSystem.",
         "ICD-10-GM, OPS, ATC with DDD, ICD-O-3, ICF, KDL, ORPHAcodes, the German variant of"
         " LOINC and more, each as a FHIR CodeSystem."),
        ("Kostenfrei. Vor dem Download ist den Downloadbedingungen ausdrücklich zuzustimmen;"
         " mit dem Download kommt ein Nutzungsvertrag mit dem BfArM zustande.",
         "Free of charge. Before a download its conditions must be accepted expressly; the"
         " download makes a usage agreement with the BfArM."),
        (("Auf der Übersicht das Kodiersystem wählen und dort den Reiter „Download“ öffnen.",
          "Choose the coding system in the overview and open its tab \"Download\"."),
         ("Die Downloadbedingungen lesen und das Häkchen zur Zustimmung setzen.",
          "Read the download conditions and tick the box to accept them."),
         ("„FHIR/JSON“ laden (ICD-10-GM 2026: 40 MB) oder das kleinere FHIR-Paket (TGZ,"
          " 1,2 MB); für Pakete aus der Paket-Registry nennt die Seite ein Zugangstoken.",
          "Download \"FHIR/JSON\" (ICD-10-GM 2026: 40 MB) or the smaller FHIR package (TGZ,"
          " 1.2 MB); for packages from the package registry the page names an access token."),
         ("Die amtlichen Titel stehen selten wörtlich in einem Arztbrief. Mehr Fundstellen"
          " bringen Listen mit Alltagsbezeichnungen wie die Alpha-ID-SE.",
          "The official titles seldom stand in a letter in so many words. Lists of everyday"
          " wordings such as the Alpha-ID-SE find more.")),
        ((("Übersicht der Kodiersysteme", "Overview of the coding systems"),
          "https://terminologien.bfarm.de/kodiersysteme.html"),
         (("Downloadbedingungen", "Download conditions"),
          "https://terminologien.bfarm.de/download-conditions.html"),
         (("Beispiel: Download der ICD-10-GM 2026", "Example: download of ICD-10-GM 2026"),
          "https://terminologien.bfarm.de/CodeSystem-icd10gm-2026.download.html")),
        "lexterm packages import CodeSystem-icd10gm-2026.json"),
    Source(
        "alpha-id",
        ("Alpha-ID-SE des BfArM", "Alpha-ID-SE of the BfArM"),
        ("Über 89.000 Diagnosebezeichnungen aus dem Alphabetischen Verzeichnis, jede mit ihrem"
         " ICD-10-GM-Kode und bei Seltenen Erkrankungen der Orpha-Kennnummer; jährlich neu.",
         "More than 89,000 diagnosis wordings from the alphabetical index, each with its"
         " ICD-10-GM code and for rare diseases the Orpha number; new every year."),
        ("Kostenfrei, unter den Downloadbedingungen des BfArM.",
         "Free of charge, under the download conditions of the BfArM."),
        (("Die Datei von der Download-Seite des BfArM laden.",
          "Download the file from the BfArM's download page."),
         ("lexterm hat für ihren Aufbau noch keinen eigenen Leser: die Datei in eine CSV-Datei"
          " mit den Spalten „term“ (Bezeichnung) und „code“ (ICD-10-GM-Kode) bringen.",
          "lexterm has no reader of its own for its layout yet: bring the file into a CSV"
          " file with the columns \"term\" (wording) and \"code\" (ICD-10-GM code).")),
        ((("Alpha-ID-SE beim BfArM", "Alpha-ID-SE at the BfArM"),
          "https://www.bfarm.de/DE/Kodiersysteme/Terminologien/Alpha-ID-SE/_node.html"),
         (("Downloads Alpha-ID-SE", "Downloads of the Alpha-ID-SE"),
          "https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html"
          "#anker-alpha-id-downloads")),
        "lexterm packages import alpha-id.csv --url http://fhir.de/CodeSystem/bfarm/icd-10-gm"
        " --term-language de"),
    Source(
        "snomed",
        ("SNOMED CT, deutsche National Edition", "SNOMED CT, German National Edition"),
        ("Die International Edition mit der deutschen Erweiterung, als Ordner von RF2-Dateien;"
         " neue Ausgaben am 15. Mai und am 15. November. Übersetzt ist nur ein Teil: eine"
         " Gesamtübersetzung wird nicht angestrebt, die Arbeit folgt Anwendungsfällen.",
         "The International Edition with the German extension, as a folder of RF2 files; new"
         " releases on 15 May and 15 November. Only a part is translated: a complete"
         " translation is not aimed at, the work follows use cases."),
        ("Affiliate-Lizenz nötig. Für die Nutzung in Deutschland ist sie kostenfrei, weil"
         " Deutschland Mitglied von SNOMED International ist. Der Lizenznehmer gibt jährlich"
         " eine Erklärung zur Nutzung ab; seine Endnutzer brauchen keine eigene Lizenz. SNOMED CT"
         " darf nicht weitergegeben werden: das Paket bleibt in der eigenen Ablage.",
         "An affiliate licence is needed. For use in Germany it is free of charge, because"
         " Germany is a member of SNOMED International. The licence holder declares the use"
         " once a year; its end users need no licence of their own. SNOMED CT may not be"
         " passed on: the package stays in one's own store."),
        (("Im Member Licensing and Distribution Service (MLDS) von SNOMED International"
          " anmelden, beim Öffnen die Sprache „Deutsch“ wählen und die Affiliate-Lizenz für"
          " Deutschland beantragen. Das BfArM beschreibt die Schritte in seinen Hinweisen zur"
          " Lizenzbeantragung.",
          "Register in the Member Licensing and Distribution Service (MLDS) of SNOMED"
          " International, choose German when it opens, and apply for the affiliate licence"
          " for Germany. The BfArM describes the steps in its notes on applying."),
         ("Nach der Freigabe im MLDS die deutsche National Edition laden und entpacken.",
          "Once approved, download the German National Edition in MLDS and unpack it."),
         ("Den entpackten Ordner mit dem Befehl unten aufnehmen. Übernommen werden die aktiven"
          " Konzepte mit ihren deutschen Bezeichnungen; mit „--term-language en“ zusätzlich die"
          " englischen.",
          "Take the unpacked folder in with the command below. The active concepts are taken"
          " with their German terms; with \"--term-language en\" the English ones as well.")),
        ((("Lizenz beantragen und MLDS nutzen (BfArM)", "Applying for a licence and using MLDS"
           " (BfArM)"),
          "https://www.bfarm.de/DE/Kodiersysteme/Terminologien/SNOMED-CT/Lizenz/_node.html"),
         (("MLDS, deutsche Ansicht", "MLDS, German view"),
          "https://mlds.ihtsdotools.org/#/landing/DE?lang=de"),
         (("Hinweise zur Lizenzbeantragung (PDF)", "Notes on applying for the licence (PDF)"),
          "https://www.bfarm.de/SharedDocs/Downloads/DE/Kodiersysteme/SNOMED-CT/"
          "Hinweise_Lizenzbeantragung.pdf?__blob=publicationFile"),
         (("National Edition und National Extension (BfArM)",
           "National Edition and National Extension (BfArM)"),
          "https://www.bfarm.de/DE/Kodiersysteme/Terminologien/SNOMED-CT/National-Edition/"
          "_node.html"),
         (("Fragen und Antworten zur Lizenzvergabe", "Questions and answers on licensing"),
          "https://www.bfarm.de/DE/Kodiersysteme/_FAQ/SNOMED-CT/SNOMED-CT-Lizenzvergabe/"
          "faq-liste.html")),
        "lexterm snomed ORDNER"),
)


def sources(code: str | None = None) -> list[dict[str, Any]]:
    """The sources in one language ("de" or "en", else the one in force), as plain data."""
    place = 0 if (code or current()) == "de" else 1
    return [{"key": s.key, "name": s.name[place], "what": s.what[place],
             "conditions": s.conditions[place], "steps": [step[place] for step in s.steps],
             "links": [{"label": label[place], "url": url} for label, url in s.links],
             "command": s.command} for s in SOURCES]


def text(code: str | None = None) -> str:
    """The sources as text for a person to read."""
    german = (code or current()) == "de"
    parts = []
    for source in sources(code):
        lines = [source["name"], "=" * len(source["name"]), source["what"], "",
                 ("Bedingungen: " if german else "Conditions: ") + source["conditions"], ""]
        lines += [f"{number}. {step}" for number, step in enumerate(source["steps"], 1)]
        lines += ["", ("Aufnehmen: " if german else "Taking it in: ") + source["command"], ""]
        lines += [f"- {link['label']}: {link['url']}" for link in source["links"]]
        parts.append("\n".join(lines))
    return "\n\n".join(parts)
