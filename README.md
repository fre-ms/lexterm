<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# lexterm

Finds medical terms in German clinical text and assigns them the codes of the terminologies they belong to,
for a person to confirm.

The project is at the design stage: there is no library here yet, only a prototype of the matcher inside the
bench. The [design](docs/design.md) says what is to be built and in which order.

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

- [Design](docs/design.md): packages, recognition, the annotation document, the windows, output, client and
  server, stages.
- [Survey of open-source tools](reports/Bestandsaufnahme%20quelloffener%20Werkzeuge.md) (in German): terminology
  servers, recognisers, review tools and German term sources, and what follows for this project.
- [Trial of existing recognisers](reports/Erprobung%20vorhandener%20Erkenner.md) (in German): twelve
  recognisers measured with one German dictionary, and the [bench](bench/) that measured them.
- [Name search](docs/name-search-2026-11-26.md).

## Licence

MIT. Term packages carry the licence of their source.
