<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# lexterm

Finds medical terms in German clinical text and assigns them the codes of the terminologies they belong to,
for a person to confirm.

The project is at its first stage (0.1). The [design](docs/design.md) says what is to be built and in which
order. What lexterm shares with its sibling lexident (identifying information) is a common core,
[lexcor](https://github.com/fre-ms/lexcor), in a repository of its own.

```python
import lexterm

for mention in lexterm.tag("Bekannte arterielle Hypertonie, Ramipril seit 2019."):
    print(mention.start, mention.end, mention.text,
          [(a.system, a.code, a.cls, a.kind) for a in mention.assignments])
```

What is here:

- `lexterm.tag`: which concepts a text mentions, each with the package, the code, the class and the kind of the
  match; `lexterm.covers`: whether a span is medical vocabulary at all, generously (a part of a hyphenated word
  counts, an eponym on its own counts), for a program that guesses at names;
- the medical rules: spellings that stand side by side ("Colitis" and "Kolitis"), and the head nouns after
  which a name is an eponym ("Babinski-Zeichen");
- one free package that comes with it: the German names of what Wikidata lists with a medical identifier
  (ICD-10, ATC, INN, LOINC, MeSH), 17,600 items in 39,600 names, CC0 1.0, with Wikidata's identifiers as codes;
- a store of its own for the packages a user imports, edits or builds from a source they hold a licence for
  (`lexterm.open_store()`, `lexterm.install(store)`), and the command line `lexterm packages …`, `lexterm tag
  FILE`.

- the annotation document (`lexterm.annotate`, `lexterm tag FILE --annotation FILE`): what was found and what
  a person decided, in one JSON file beside the text; a later run keeps every decision.

- the output as FHIR (`lexterm.export.codeable_concepts`, `lexterm export fhir ANNOTATION`): a mention becomes a
  `CodeableConcept` with its wording as text and a coding from every code system that knows it.

- readers for what a user gets themselves: FHIR CodeSystems and FHIR packages (`lexterm packages import`),
  releases of SNOMED CT in RF2 (`lexterm snomed FOLDER`), and the Alpha-ID-SE of the BfArM (`lexterm alpha-id
  FILE`), whose everyday wordings of diagnoses become the Alpha-ID as a code system and supplements to the
  ICD-10-GM and to the ORPHAcodes; `lexterm sources` says where they come from.

One wording is coded in every code system that lists it; nothing chooses between packages. Without a store
lexterm recognises with the package it brings, in memory, and writes nothing anywhere; that is how a program
that reads documents uses it. Not here yet: the windows, the output for medDAV, the client and server of a
terminology server.

Tests: `pytest`; checks: `ruff check .` and `mypy`.

## What it is to do

1. **Keep a database of medical terms**, built from packages: free ones that come with it, and ones a user
   builds locally from a source they hold a licence for (SNOMED CT, a medical dictionary, their own lists).
   Packages can be imported, exported (CSV, FHIR CodeSystem) and edited.
2. **Recognise the terms in a text and tag them.** A term may belong to several packages and then carries
   several assignments. A window shows the tagged text with the source and code of every assignment; a person
   confirms, discards or adds assignments, so that what a machine proposed and what a person checked stay apart.
3. **Write the result in standard forms**: FHIR `CodeableConcept`, and the words in which medDAV takes a
   clinical entry over.

Licensed terminologies are not shipped. Where a licence stands in the way there are instructions instead: how to
build a package from freely available data, or how to connect a terminology server that runs under the user's
own licence. lexterm can be the client of such a server, and a small server itself: it serves its own packages
through the FHIR terminology interface and recognises terms for other programs.

## Documents

- [Getting terminologies](docs/terminologies.md): where the coding systems of the BfArM (ICD-10-GM, OPS, ATC …)
  and the German edition of SNOMED CT come from, under which conditions, and how lexterm takes them in.
- [Design](docs/design.md): packages, recognition, the annotation document, the windows, output, client and
  server, stages.
- [Survey of open-source tools](reports/Bestandsaufnahme%20quelloffener%20Werkzeuge.md) (in German): terminology
  servers, recognisers, review tools and German term sources, and what follows for this project.
- [Trial of existing recognisers](reports/Erprobung%20vorhandener%20Erkenner.md) (in German): twelve
  recognisers measured with one German dictionary, and the [bench](bench/) that measured them.
- [Name search](docs/name-search-2026-11-26.md).

## Licence

MIT. Term packages carry the licence of their source.
