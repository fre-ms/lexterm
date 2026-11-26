<!-- SPDX-FileCopyrightText: 2026 fre.ms -->
<!-- SPDX-License-Identifier: MIT -->

# Bench

Measures recognisers of medical terms on German text, each with the same dictionary: how many terms they find
and link in the forms German text brings, what they tag where nothing should be tagged, and what they cost in
time and memory.

```
python bench.py make  DICTIONARY.csv[.gz]  testset.json
python bench.py run   testset.json results/ --tools proto
python bench.py report results/
python bench.py corpus BRAT_FOLDER QID_CUI.csv DICTIONARY.csv[.gz] results/ --tools proto
python bench.py texts  TEXT_FOLDER DICTIONARY.csv[.gz] results/ --tools proto
```

- `bench.py`: makes the test set from a dictionary (so the truth is known by construction), runs and scores.
- `tools.py`: the recognisers, each behind `build(entries)` and `tag(text)`. One that is not installed is left
  out. Names for `--tools`: `proto`, `proto-fold`, `simstring-0.9`, `simstring-0.8`, `simstring-0.7`,
  `flashtext`, `flashtext-de`, `aho`, `spacy`, `iamsystem`, `iamsystem-stem`, `iamsystem-fuzzy`, `edsnlp`,
  `edsnlp-simstring`, `medcat`, `medcat-dict`, `quickumls`.
- `proto.py`: a prototype of lexterm's own matcher (design, section 5.2).

The dictionary is a CSV of term, class and code. The first run used PseudonyMed's list of German labels from
Wikidata (CC0); its results are in [the report](../reports/Erprobung%20vorhandener%20Erkenner.md) (in German).
Run one recogniser per call, so that its time and memory are its own. QuickUMLS needs an environment of its own
(`medspacy-quickumls`) and fetches NLTK data when it starts: set `NLTK_DATA` to a folder of the bench first.
