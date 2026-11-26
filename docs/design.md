<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# lexterm: design

Draft 0.3, 26 November 2026. Nothing of this is built yet but a prototype of the matcher and a bench.

**Since 0.3 the parts lexterm shares with its sibling lexident are designed in lexcor's repository**, and that
design is the one in force for them: packages and the store (here sections 4.1, 4.4 and 4.5), recognition
(5.2 to 5.5), the annotation document (6), the windows (7), client and server (9 and 10). What remains
lexterm's own is what is medical: its packages and importers (4.2 and 4.3), its table of spelling variants,
its output (8). The sections below are kept until lexcor is built, so that nothing is lost on the way. Two
reports (in German) say what exists already and why the parts below are built or taken over: the
[survey of open-source tools](../reports/Bestandsaufnahme%20quelloffener%20Werkzeuge.md) and the
[trial of existing recognisers](../reports/Erprobung%20vorhandener%20Erkenner.md).

## 1 Purpose

lexterm finds medical terms in German clinical text and assigns each of them the codes of the terminologies it
belongs to, for a person to confirm. It does three things:

1. It keeps a database of medical terms, built from **packages** that can be imported, exported and edited.
2. It **recognises** the terms in a text and tags them. A term that several packages hold carries several
   assignments. A window shows the tagged text; a person confirms, discards and adds assignments, and what a
   machine proposed stays apart from what a person checked.
3. It **writes the result in standard forms**: FHIR `CodeableConcept`, and the words in which medDAV takes a
   clinical entry over.

It is a library, a command-line program and a window, and it can be both the **client** of a terminology server
and a small **server** itself.

Two conditions hold for everything in it: it runs on an ordinary computer **without a graphics card or other
special hardware**, and it **can be packaged** as a program that is shipped with others (as PseudonyMed and
optdoc are). A part that needs more is an option outside the package, never the core.

What it is not:

- It does not decide what holds for the patient. It finds **mentions**: "no sign of epilepsy" and "mother with
  dementia" contain the terms without their being the patient's findings. Negation, suspicion and family history
  are a later stage (section 5.5), and a person decides.
- It is not a full terminology server. It serves its own packages and answers the common questions about a code;
  the hierarchy of SNOMED CT, its query language and the authoring of terminologies stay with the servers made
  for them (section 9).
- It ships no licensed terminology.

## 2 Neighbours

lexterm is one of several parts that work alone and together.

| Part | What it does | What it has to do with lexterm |
|---|---|---|
| optdoc | cleans up scans and photos and reads their text | lexterm takes text; where the text came from a page, the positions on the page are optdoc's |
| PseudonyMed | pseudonymises patient documents | uses lexterm to know which words are medical terms and must not be redacted by guesswork, and which words name a drug or a laboratory test; it joins optdoc, lexterm and lexident |
| lexident (planned) | the same idea for identifying information: hospitals, occupations, studies, titles | a sibling; section 12 |
| medorello | files documents into the patient record | runs lexterm on a document's text and keeps the result beside it |
| medonomina | shows and edits the clinical entries (medDAV) | takes confirmed assignments over as proposals |

Rules that follow from this:

- lexterm knows nothing of patients, records or pseudonyms. It gets a text and returns annotations.
- Which packages count for what is the caller's choice. PseudonyMed protects a word because it is in the
  anatomy package and not because it is in a list of occupations; lexterm gives every term its package and its
  class and decides nothing.
- No part carries a copy of another part's code.

## 3 Words used here

- **Package**: one terminology or list in one version, with its licence: "ICD-10-GM 2026", "German MeSH 2026",
  "my own terms".
- **Concept**: one meaning in a package, with a code and a name to show.
- **Term**: one wording of a concept as it may stand in a text: the preferred name, a synonym, an abbreviation.
- **Mention**: a place in a text where a term stands.
- **Assignment**: the statement that a mention means a concept. A mention has as many assignments as packages
  (and meanings) hold its term.

## 4 Packages

### 4.1 Form

A package is a **FHIR CodeSystem** (R4), as a JSON file or inside a FHIR package (`.tgz`). This is the form in
which the BfArM publishes ICD-10-GM, OPS and ATC, and every FHIR terminology server reads and writes it, so no
format of lexterm's own is needed:

| What lexterm needs | In the CodeSystem |
|---|---|
| name, version, identifying URI | `title`, `version`, `url` |
| licence and source | `copyright`, `publisher` |
| concept: code and name to show | `concept.code`, `concept.display` |
| terms of a concept, with their language | `concept.designation` (`value`, `language`) |
| kind of a term: preferred, synonym, abbreviation | `concept.designation.use` |
| class of a concept (anatomy, drug, laboratory test, disorder …) | `concept.property` with the code `class` |
| parent of a concept, where the source has a hierarchy | `concept.property` with the code `parent` |

Two things FHIR has no element for are kept in an extension of lexterm's own on the CodeSystem: whether the
package **may be passed on** (`redistributable`), and for a term whether it is matched **only as written**
(abbreviations and words of up to three letters, section 5.2).

A plain list of words (a user's own terms) is a package too: the code of each concept is the word itself, and
the URI is a local one.

**CSV** is the second form, for lists made by hand and for spreadsheets: one row per term with the columns
`term`, `code`, `display`, `class`, `kind`, `language`; only `term` is required. Comma-separated, UTF-8.

### 4.2 Three kinds of package

| Kind | Examples | How it gets to the user |
|---|---|---|
| **bundled**: a licence that allows passing on | Wikidata (CC0), Orphanet (CC BY 4.0), lexterm's own lists (body parts, findings terms, laboratory tests), German MeSH if its terms of use allow | comes with lexterm |
| **built by the user from free data**, where the terms of download forbid passing on or ask for a confirmation | ICD-10-GM, OPS, ATC, Alpha-ID-SE (BfArM) | instructions and a command that fetches from the source after the user has agreed to its terms |
| **licensed** | SNOMED CT (affiliate licence, free of charge in Germany), LOINC, UMLS, a medical dictionary, a rating system's manual | imported locally from the user's own copy, or reached through a terminology server the user runs (section 9); never shipped, never in the repository or its tests |

A package that is not `redistributable` is never written into an export meant for others, and the server guards
it (section 10.3).

### 4.3 Importing and exporting

Importers: FHIR CodeSystem (JSON) and FHIR packages, CSV, SNOMED CT release files (RF2: descriptions and the
language reference set), MeSH XML. A source in a form of its own (a dictionary's export) is brought to CSV by a
small script that stays with the user.

Exports: FHIR CodeSystem and CSV, of a whole package or a selection.

### 4.4 Editing

A user deletes terms that mislead ("Wolf", "Salat"), adds terms and synonyms, moves a term to another class.
These changes are kept as an **overlay** beside the package, never written into it: a new version of the
package replaces the package and leaves the overlay in force. An overlay can be exported and imported like a
package, so that a colleague can take it over.

### 4.5 The store

One SQLite file in the user's data folder holds the packages, their concepts and terms, and the overlays. A
version counter changes with every edit, so that the matcher's index is rebuilt only when needed.

## 5 Recognition

### 5.1 Where it comes from

The matcher is the one PseudonyMed has used since October 2026 over some 45,000 German terms. It is a
dictionary matcher: fast, without a network, without a model, and it gives the same result for the same input.
It finds only what a package holds in so many words; better German packages are the way to find more.

The trial of November 2026 set a prototype of it beside the libraries at hand, each with the same dictionary:
the prototype linked 89 % of the test places and tagged nothing it should not; every plain dictionary matcher
(FlashText, pyahocorasick, spaCy's PhraseMatcher, EDS-NLP, iamsystem as it comes) and MedCAT without a trained
model linked 63 to 64 %, because none of them knows German inflection endings or transliterated umlauts. Only
iamsystem with an ending rule and a tolerance for one spelling error did better there (98 %).

On German text annotated by people (the Mantra corpus) the same prototype, with the free dictionary, found 38 %
of the places and linked 20 % to the identifier the annotators chose; no dictionary method reached half. What
limits it is the dictionary: one annotated place in five stands in it in so many words. The matcher is the
small part of the work; the packages decide how good recognition is.

### 5.2 Matching

A text is cut into words. A term matches where the words of the text spell it:

- regardless of upper and lower case, with umlauts as written or transliterated (`ä`/`ae`, `ß`/`ss`);
- with a German inflection ending (`-s`, `-n`, `-en`, `-e`, `-es`, `-er`, `-em`, `-ern`) on a stem of four or
  more letters;
- as a whole where the term has several words, up to five; the longest term that starts at a word wins;
- **only as written** for abbreviations and for words of up to three letters: "HAT" and "Ohr" are terms, "hat"
  is a verb.

### 5.3 Two questions, kept apart

PseudonyMed asks "must this word be left alone?", and for that the matcher is generous on purpose: it treats
"Parkinson-Syndrom" as medical because "Parkinson" is listed, and "Babinski" alone because "Babinski-Zeichen"
is. For an assignment that is not good enough: a part of a word is not the concept of the whole.

- **`tag`** answers "which concepts does this text mention?". It makes an assignment only where a whole term
  matches by the rules of 5.2.
- **`covers`** answers "is this span medical vocabulary?", with the generous rules, and gives no codes.

### 5.4 Overlaps and several meanings

Where terms overlap, the longest is the mention ("Morbus Parkinson", not "Parkinson" inside it); shorter ones
inside it can be asked for. Where one term stands in several packages, or for several concepts of one package,
every one of them becomes an assignment. lexterm does not choose between them.

### 5.5 Later: context and other recognisers

- **Context**: whether a mention is negated, suspected or about a relative, proposed from trigger words in the
  sentence (the ConText method). No German rules of this kind are freely at hand in the tools surveyed; a
  German trigger list exists and its licence is to be cleared. A stage that can be switched off, and its result
  is a proposal at the mention.
- **Spelling variants**: a fixed rule for the spellings German medicine has side by side (c, k and z: "Colitis"
  and "Kolitis", "Lactulose" and "Laktulose").
- **Spelling errors**: a tolerance for one wrong letter is **not** a way to make assignments. On real letters
  the trial saw it turn "Papille" into "Pupille", "Gewicht" into "Gesicht" and "Kollegen" into "Kollagen". At
  most it is a source of proposals for text that comes from text recognition, each marked as fitting only
  roughly and none in force until a person confirms it.
- **Recognisers that learn** are not ruled out by the two conditions of section 1, which bind the core; they
  are planned from the start as modules that are switched on. A recogniser is anything that takes a text and
  the packages and returns places with codes, and every assignment names the recogniser that made it
  (section 6). What such a module learns from is what the annotation document collects: the assignments a
  person confirmed and rejected. lexcor's design (section 4.7) names the candidates.

## 6 The annotation document

The result of recognition and of a person's review is one JSON file beside the text (`<name>.lexterm.json`).

```json
{
  "lexterm": 1,
  "text": { "sha256": "…", "length": 1834 },
  "packages": [
    { "url": "http://fhir.de/CodeSystem/bfarm/icd-10-gm", "version": "2026", "sha256": "…" }
  ],
  "settings": { "packages": ["…"], "classes": [], "nested": false },
  "mentions": [
    {
      "id": "m1", "start": 112, "end": 128, "exact": "Morbus Parkinson",
      "prefix": "Diagnosen: ", "suffix": ", ED 2019",
      "assignments": [
        {
          "system": "http://fhir.de/CodeSystem/bfarm/icd-10-gm", "version": "2026",
          "code": "G20", "display": "Primäres Parkinson-Syndrom",
          "origin": { "by": "machine", "recogniser": "lexterm 0.2" },
          "status": "proposed"
        }
      ]
    }
  ]
}
```

- **Positions** count Unicode code points from the start of the text. A program whose strings count otherwise
  (UTF-16 in JavaScript and Qt) converts.
- **`exact`, `prefix`, `suffix`** are the wording and a little of what stands around it, so that a mention is
  found again after the text has changed a little (a corrected reading).
- **`origin`** is `machine` with the recogniser, or `person`.
- **`status`** is `proposed`, `confirmed` or `rejected`; a decision carries who made it and when.

Rules:

- A person never deletes what a machine proposed: they **reject** it, and it stays in the file. A later run
  does not bring it back as a proposal.
- What a person confirmed or added stays, whatever a later run finds.
- The same text, the same package versions and the same file give the same result, byte for byte.
- A mention that is not found again after the text has changed is kept in a list of its own and shown, not
  dropped.

## 7 The windows

**Review** (`lexterm review`): the text on the left with its mentions marked, proposed and confirmed ones told
apart at a glance; on the right, for the mention chosen, its assignments with package, code and name. A person
confirms, rejects, adds an assignment (searching the packages by wording or code), and marks a place by hand
that was not recognised. "Confirm all of this package" for long texts.

**Packages** (`lexterm packages`, second tab): the packages with licence, version and number of terms; search,
edit, add and delete terms; import and export.

Both are widgets that another program can embed (PseudonyMed's vocabulary step becomes the second one). The
interface is German or English.

## 8 Output

### 8.1 FHIR

One `CodeableConcept` per mention and meaning, with `text` = the wording in the document. Several codings stand
in one CodeableConcept **only where the packages are known to mean the same concept** (a mapping the packages
carry, such as identifiers shared through Wikidata, or a ConceptMap); otherwise each meaning is a
CodeableConcept of its own. A confirmed coding carries `userSelected: true`. By default only confirmed
assignments are written.

A CodeableConcept is not a resource. What it becomes (a condition, an observation, a medication) is for the
program that takes it over. Who confirmed it and when belongs in a `Provenance` beside that resource; the
annotation document holds what is needed for it.

### 8.2 medDAV

Candidates in medDAV's words: the wording as the value, `CODE`, `SYSTEM`, `VERSION`, and `SOURCE` where the
caller says which document the text is. Confirmed assignments only. medDAV asks for a source and a recorder on
every clinical entry, and whether a mention becomes an entry at all is a person's decision, so lexterm writes
proposals for review and never an entry. The exact form is to be agreed with medDAV and medRDS (section 14).

### 8.3 UIMA CAS

An export and import in the form INCEpTION reads, so that an annotation can be continued there by a team, and
a corpus annotated there can be read back.

## 9 Client of a terminology server

lexterm speaks the FHIR terminology interface to any server that offers it. For SNOMED CT on a single computer
the survey points to Hermes with hades, or Snowstorm Lite, run under the user's own affiliate licence.

- **As a source of a package.** Recognition needs the terms as a local index; one cannot ask a server for every
  word of a text. `lexterm packages add --server …` reads the terms of a code system or a value set from the
  server (`$expand` with designations, in pages) and builds the package on the user's computer, marked as not
  redistributable unless the user says otherwise.
- **While reviewing.** `$lookup` for the details of a code, `$validate-code` when a person types a code in,
  `$translate` to offer the code of another system.
- **Never with patient text.** Only codes, code-system URIs and search words a person types go to a server, and
  the default is a server on the same computer.

## 10 Server

`lexterm serve` makes lexterm's own store and recogniser available to other programs on the same computer or,
if the operator decides so, in the same network.

### 10.1 What it serves

| Request | Answer |
|---|---|
| `GET /metadata` | what the server can do (CapabilityStatement; TerminologyCapabilities with `mode=terminology`) |
| `GET /CodeSystem`, `GET /CodeSystem?url=…` | the packages |
| `CodeSystem/$lookup` | name, terms and properties of a code |
| `CodeSystem/$validate-code` | whether a code exists and its name fits |
| `ValueSet/$expand` with `filter` | the codes of a package whose terms match what was typed: the search behind an input field |
| `ConceptMap/$translate` | the code of another system, where the packages carry the mapping |
| `CodeSystem/$subsumes` | only for packages that carry a hierarchy |
| `POST /annotate` | the annotation document for a text (not FHIR; FHIR has no operation for this) |

### 10.2 What it does not serve

The query language and the full hierarchy of SNOMED CT, versions side by side, authoring. An operator who needs
them runs a server made for them; lexterm can be told to **pass on** what it cannot answer to such a server, so
that a program has one address to ask.

### 10.3 Licences and privacy

- The server listens on the computer itself (loopback) unless the operator opens it.
- A package that is not `redistributable` is not handed out as a whole (its CodeSystem is served with
  `content: not-present`), and its codes are answered beyond the computer only when the operator has stated that
  the licence covers it.
- `/annotate` receives clinical text. It is not logged, and it is the reason for the first point.

## 11 Interfaces

**Library** (Python 3.12 or later):

```python
import lexterm

store = lexterm.open_store()
annotation = lexterm.tag(text, store, packages=["icd-10-gm", "mesh-de"])
for mention in annotation.mentions:
    for assignment in mention.assignments:
        ...
annotation.save("letter.lexterm.json")
concepts = lexterm.export.codeable_concepts(annotation)
```

**Command line**, for people and for programs in other languages (medorello starts it as a companion program,
as it does optdoc):

```
lexterm packages list | show | add | remove | export
lexterm tag TEXTFILE [-o FILE]
lexterm review FILE
lexterm export fhir | meddav | cas  ANNOTATION
lexterm lookup SYSTEM CODE
lexterm serve
```

With `--json` every command prints one JSON document on standard output and nothing else. Names of commands and
options are English; messages are German or English (`--language`).

**Dependencies**: the core needs Python's standard library and SQLite only. The windows (PySide6) and the UIMA
CAS export are extras.

## 12 The sibling: lexident

PseudonyMed's table of identifying information (hospitals, occupations, studies, titles and a user's own
entries, recognised by rules of context) is to become a library of its own on the same idea, and PseudonyMed
then joins optdoc, lexterm and lexident.

lexident is not designed here. What it shares with lexterm is plain already: packages with a licence and an
overlay, the store, the matcher, the annotation document, the review window, client and server. Decided on
26 November 2026: these parts become a **common core** that both libraries use, with the working name
**lexcor**, written without anything medical and without anything about persons in it. lexterm adds the
medical packages, their importers and the output for FHIR and medDAV; lexident adds its packages and the rules
of context that decide whether a listed word identifies anyone.

Decided as well: lexident is to do **all** recognition of identifying information in the end, built in stages.
First what PseudonyMed's identifier step does today (lists with rules of context, registry numbers); then
patterns (telephone, e-mail, bank and insurance numbers, dates); then the identifiers of one patient as a
package the caller hands over. PseudonyMed is then what joins the parts and keeps what is its own: pseudonyms,
redaction, the re-check, the estimate of residual risk.

## 13 Stages

1. **0.1** The matcher and the vocabulary leave PseudonyMed with their history. Packages as FHIR CodeSystem and
   CSV, the store, `tag` with every assignment, `covers`; PseudonyMed switches over.
2. **0.2** The annotation document with origin and status; the two windows.
3. **0.3** Output as FHIR, for medDAV and as UIMA CAS; importers for FHIR packages, SNOMED CT release files and
   MeSH; instructions for the packages a user builds.
4. **0.4** Client of a terminology server.
5. **0.5** Server.

Beside these: the bench in [`bench/`](../bench/), which measures recognisers with one dictionary on a test set
whose truth is known by construction. Its first run is the trial named above. Still to come is a measurement on
freely available German texts with a checked truth.

## 14 Open questions

1. **medDAV and medRDS**: the form of the candidates (8.2) and where medorello keeps the annotation document
   beside a document.
2. **The user's vocabulary today** lives in PseudonyMed's pseudonym database. It moves to lexterm's store once,
   by a command; PseudonyMed keeps no second copy.
3. **German MeSH**: whether its terms of use allow bundling.
4. **The common core** (section 12): decided on 26 November 2026, three repositories (lexcor, lexterm,
   lexident); the core is built first. The server (section 10) is planned and built when a program needs it.
5. **Context** (5.5): the licence of the German trigger list, and whether rules of lexterm's own are better.
6. **The order of stages 0.4 and 0.5**, if a program needs the server early.
