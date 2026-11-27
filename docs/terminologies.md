<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# Getting terminologies

lexterm comes with one free package (the German names of what Wikidata lists with a medical identifier). Every
other terminology a user gets themselves: lexterm never downloads anything, because terminologies are given out
under conditions a person has to accept, some under a licence. This page says where each comes from and how
lexterm takes it in. The same text, in German and English, is in the program: `lexterm sources`.

What lexterm reads:

- a FHIR CodeSystem as a JSON file, with its concepts in it (`content: complete`);
- a FHIR package (`.tgz`): every CodeSystem in it is taken in, and those that name their concepts elsewhere are
  left out and named;
- a CSV file with the columns `term`, `code`, `display`, `class`, `kind`, `language` (only `term` is needed);
- a release of SNOMED CT in its own form, RF2 (`lexterm snomed FOLDER`).

A package that may not be passed on stays in the user's own store and is never written into an export meant for
others. The addresses below were read on 27 November 2026.

## Coding systems of the BfArM

ICD-10-GM, OPS, ATC with DDD, ICD-O-3, ICF, KDL, ORPHAcodes, the German variant of LOINC and more, each as a FHIR CodeSystem.

**Conditions.** Free of charge. Before a download its conditions must be accepted expressly; the download makes a usage agreement with the BfArM.

1. Choose the coding system in the overview and open its tab "Download".
2. Read the download conditions and tick the box to accept them.
3. Download "FHIR/JSON" (ICD-10-GM 2026: 40 MB) or the smaller FHIR package (TGZ, 1.2 MB); for packages from the package registry the page names an access token.
4. The official titles seldom stand in a letter in so many words. Lists of everyday wordings such as the Alpha-ID-SE find more.

```
lexterm packages import CodeSystem-icd10gm-2026.json
```

- [Overview of the coding systems](https://terminologien.bfarm.de/kodiersysteme.html)
- [Download conditions](https://terminologien.bfarm.de/download-conditions.html)
- [Example: download of ICD-10-GM 2026](https://terminologien.bfarm.de/CodeSystem-icd10gm-2026.download.html)

## Alpha-ID-SE of the BfArM

More than 89,000 diagnosis wordings from the alphabetical index, each with its ICD-10-GM code and for rare diseases the Orpha number; new every year.

**Conditions.** Free of charge, under the download conditions of the BfArM.

1. Download the file from the BfArM's download page.
2. lexterm has no reader of its own for its layout yet: bring the file into a CSV file with the columns "term" (wording) and "code" (ICD-10-GM code).

```
lexterm packages import alpha-id.csv --url http://fhir.de/CodeSystem/bfarm/icd-10-gm --term-language de
```

- [Alpha-ID-SE at the BfArM](https://www.bfarm.de/DE/Kodiersysteme/Terminologien/Alpha-ID-SE/_node.html)
- [Downloads of the Alpha-ID-SE](https://www.bfarm.de/DE/Kodiersysteme/Services/Downloads/_node.html#anker-alpha-id-downloads)

## SNOMED CT, German National Edition

The International Edition with the German extension, as a folder of RF2 files; new releases on 15 May and 15 November. Only a part is translated: a complete translation is not aimed at, the work follows use cases.

**Conditions.** An affiliate licence is needed. For use in Germany it is free of charge, because Germany is a member of SNOMED International. The licence holder declares the use once a year; its end users need no licence of their own. SNOMED CT may not be passed on: the package stays in one's own store.

1. Register in the Member Licensing and Distribution Service (MLDS) of SNOMED International, choose German when it opens, and apply for the affiliate licence for Germany. The BfArM describes the steps in its notes on applying.
2. Once approved, download the German National Edition in MLDS and unpack it.
3. Take the unpacked folder in with the command below. The active concepts are taken with their German terms; with "--term-language en" the English ones as well.

```
lexterm snomed ORDNER
```

- [Applying for a licence and using MLDS (BfArM)](https://www.bfarm.de/DE/Kodiersysteme/Terminologien/SNOMED-CT/Lizenz/_node.html)
- [MLDS, German view](https://mlds.ihtsdotools.org/#/landing/DE?lang=de)
- [Notes on applying for the licence (PDF)](https://www.bfarm.de/SharedDocs/Downloads/DE/Kodiersysteme/SNOMED-CT/Hinweise_Lizenzbeantragung.pdf?__blob=publicationFile)
- [National Edition and National Extension (BfArM)](https://www.bfarm.de/DE/Kodiersysteme/Terminologien/SNOMED-CT/National-Edition/_node.html)
- [Questions and answers on licensing](https://www.bfarm.de/DE/Kodiersysteme/_FAQ/SNOMED-CT/SNOMED-CT-Lizenzvergabe/faq-liste.html)
