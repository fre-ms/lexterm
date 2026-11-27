<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# Getting terminologies

lexterm brings no terminology: a user gets every terminology themselves, and lexterm never downloads anything, because terminologies are given out
under conditions a person has to accept, some under a licence. This page says where each comes from and how
lexterm takes it in. The same text, in German and English, is in the program: `lexterm sources`.

What lexterm reads:

- a FHIR CodeSystem as a JSON file, with its concepts in it (`content: complete`);
- a FHIR package (`.tgz`): every CodeSystem in it is taken in, and those that name their concepts elsewhere are
  left out and named;
- a CSV file with the columns `term`, `code`, `display`, `class`, `kind`, `language` (only `term` is needed);
- a FHIR CodeSystem that is a supplement (`content: supplement`): further wordings for the codes of another
  code system, which then code in that system;
- a release of SNOMED CT in its own form, RF2 (`lexterm snomed FOLDER`);
- the Alpha-ID-SE as the BfArM gives it out (`lexterm alpha-id FILE`).

The package window (`lexterm packages window`) takes all of these in with "Take in …" and shows this text beside
the packages; there every package has a box to tick for the runs that follow.

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

More than 89,000 diagnosis wordings from the alphabetical index to the ICD-10-GM, each with its Alpha-ID, its ICD-10-GM codes and for rare diseases the Orpha number; new every year.

**Conditions.** Free of charge, under the download conditions of the BfArM (no changes, and the source is to be named); for the Orpha numbers the terms of use of Orphadata and INSERM hold as well.

1. Download the Alpha-ID-SE of the year wanted from the BfArM's download page (a ZIP file, for example alphaidse2027.zip). The edition of a year belongs to the ICD-10-GM of that year.
2. Take the file in as it was downloaded, with the command below; it need not be unpacked. Three packages come of it: the Alpha-ID as a code system of its own, and its wordings as a supplement to the ICD-10-GM and to the ORPHAcodes. So a wording in a text is coded in all three systems at once, and the ICD-10-GM keeps its official titles.
3. Where the store holds the ICD-10-GM, the codes carry their official titles. lexterm says on taking the file in when the years differ or the ICD-10-GM of the store does not have a code. Entries the file marks as no longer valid are left out.
4. The index lists general words ("Therapie", "Schmerzen") and abbreviations as well. What lexterm finds with them is a proposal for a person to check.

```
lexterm alpha-id alphaidse2027.zip
```

The packages hold the Alpha-ID under `http://fhir.de/CodeSystem/bfarm/alpha-id`, with the codes the file gives a wording as properties of its concept (`icd-10-gm-primary`, `icd-10-gm-star`, `icd-10-gm-additional`, `icd-10-gm-primary-2`, `orpha`), and code the wordings in `http://fhir.de/CodeSystem/bfarm/icd-10-gm` and `http://www.orpha.net`. A wording is taken as the file gives it: one with an explanation in square brackets is found only where a text has it in that form.

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
