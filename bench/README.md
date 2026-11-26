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
python bench.py link   BRAT_FOLDER QID_CUI.csv DICTIONARY.csv[.gz] results/ [--lower]
```

- `bench.py`: makes the test set from a dictionary (so the truth is known by construction), runs and scores.
- `tools.py`: the recognisers, each behind `build(entries)` and `tag(text)`. One that is not installed is left
  out. Names for `--tools`: `proto`, `proto-fold`, `lexcor`, `lexcor-variants`, `simstring-0.9`,
  `simstring-0.8`, `simstring-0.7`, `flashtext`, `flashtext-de`, `aho`, `spacy`, `iamsystem`,
  `iamsystem-stem`, `iamsystem-fuzzy`, `edsnlp`, `edsnlp-simstring`, `medcat`, `medcat-dict`, `quickumls`,
  `meaning-0.95`, `meaning-0.9`, `meaning-0.85`, `meaning-0.8`.
- `proto.py`: a prototype of lexterm's own matcher (design, section 5.2). `lexcor` is the core that grew out
  of it and must give the same results; put its repository on `PYTHONPATH`.
- `semantic.py`: search by meaning. A model trained on the names of concepts (SapBERT on XLM-RoBERTa) turns
  names into vectors; the `meaning-*` recognisers give every run of words the prototype left the nearest name
  of the dictionary when it is near enough, and `link` asks the same of the places people annotated, leaving
  the finding aside. It needs `torch`, `transformers`, `sentencepiece` and `protobuf`, the folder of the model
  in `LEXTERM_BENCH_MODEL` (fetched by hand from
  [Hugging Face](https://huggingface.co/cambridgeltl/SapBERT-UMLS-2020AB-all-lang-from-XLMR): the files
  `config.json`, `model.safetensors`, `sentencepiece.bpe.model`, `special_tokens_map.json`,
  `tokenizer_config.json`, 1.1 GB; its card names no licence) and, to keep the vectors of a dictionary
  between runs, a folder in `LEXTERM_BENCH_CACHE`. It runs on the processor only.

The dictionary is a CSV of term, class and code. The first run used PseudonyMed's list of German labels from
Wikidata (CC0); its results are in [the report](../reports/Erprobung%20vorhandener%20Erkenner.md) (in German).
Run one recogniser per call, so that its time and memory are its own. QuickUMLS needs an environment of its own
(`medspacy-quickumls`) and fetches NLTK data when it starts: set `NLTK_DATA` to a folder of the bench first.
