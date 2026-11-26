# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""Search by meaning, for the bench only.

A model trained on the names of concepts (SapBERT, here its multilingual variant on
XLM-RoBERTa) turns a string into a vector; names that mean the same lie near each other,
whatever their spelling or language.  The names of a dictionary are turned into vectors
once, and a run of words from a text takes the nearest of them.

Needs ``torch`` and ``transformers`` and the folder of the model in ``LEXTERM_BENCH_MODEL``.
Vectors of a dictionary are kept in ``LEXTERM_BENCH_CACHE`` when it is set.  Everything runs
on the processor; no graphics card is used even where one is present.
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import numpy as np

BATCH = 128
MAX_TOKENS = 25  # as the model was trained
BLOCK = 2048


class Embedder:
    """Vectors of unit length for strings: the model's output at the first position."""

    def __init__(self, folder: Path) -> None:
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.folder = folder
        self.tokenizer = AutoTokenizer.from_pretrained(folder, local_files_only=True)
        self.model = AutoModel.from_pretrained(folder, local_files_only=True).eval()
        self.strings = 0
        self.seconds = 0.0

    def embed(self, strings: list[str]) -> np.ndarray:
        started = time.perf_counter()
        rows = np.zeros((len(strings), self.model.config.hidden_size), dtype=np.float32)
        order = sorted(range(len(strings)), key=lambda i: len(strings[i]))
        with self.torch.inference_mode():
            for start in range(0, len(order), BATCH):
                batch = order[start:start + BATCH]
                tokens = self.tokenizer([strings[i] for i in batch], padding=True,
                                        truncation=True, max_length=MAX_TOKENS,
                                        return_tensors="pt")
                first = self.model(**tokens)[0][:, 0, :]
                rows[batch] = self.torch.nn.functional.normalize(first, dim=1).numpy()
        self.strings += len(strings)
        self.seconds += time.perf_counter() - started
        return rows


class Index:
    """The names of a dictionary as vectors, and the nearest of them for any string."""

    def __init__(self, embedder: Embedder, names: list[str], lower: bool = False) -> None:
        self.embedder = embedder
        self.names = names
        self.lower = lower
        self.known: dict[str, tuple[float, int]] = {}
        spelt = [self.spelt(name) for name in names]
        cache = os.environ.get("LEXTERM_BENCH_CACHE")
        key = hashlib.sha256("\n".join([embedder.folder.name, *spelt]).encode()).hexdigest()[:16]
        stored = Path(cache) / f"names-{key}.npy" if cache else None
        started = time.perf_counter()
        if stored and stored.exists():
            self.vectors = np.load(stored)
        else:
            self.vectors = embedder.embed(spelt)
            if stored:
                stored.parent.mkdir(parents=True, exist_ok=True)
                np.save(stored, self.vectors)
        self.build_seconds = time.perf_counter() - started

    def spelt(self, string: str) -> str:
        string = " ".join(string.split())
        return string.lower() if self.lower else string

    def nearest(self, strings: list[str], k: int = 1) -> tuple[np.ndarray, np.ndarray]:
        """For each string the ``k`` nearest names: their nearness (cosine) and their numbers."""
        vectors = self.embedder.embed([self.spelt(s) for s in strings])
        scores = np.zeros((len(strings), k), dtype=np.float32)
        numbers = np.zeros((len(strings), k), dtype=np.int64)
        for start in range(0, len(strings), BLOCK):
            block = vectors[start:start + BLOCK] @ self.vectors.T
            top = np.argpartition(-block, k - 1, axis=1)[:, :k]
            best = np.take_along_axis(block, top, axis=1)
            order = np.argsort(-best, axis=1)
            scores[start:start + BLOCK] = np.take_along_axis(best, order, axis=1)
            numbers[start:start + BLOCK] = np.take_along_axis(top, order, axis=1)
        return scores, numbers

    def best(self, strings: list[str]) -> dict[str, tuple[float, int]]:
        """The nearest name of each string, remembered across calls."""
        new = sorted({s for s in strings if s not in self.known})
        if new:
            scores, numbers = self.nearest(new)
            for string, score, number in zip(new, scores[:, 0], numbers[:, 0], strict=True):
                self.known[string] = (float(score), int(number))
        return {s: self.known[s] for s in strings}


_embedders: dict[Path, Embedder] = {}
_indexes: dict[tuple[Path, bool, int], Index] = {}


def embedder() -> Embedder:
    """The model named by ``LEXTERM_BENCH_MODEL``, loaded once."""
    folder = Path(os.environ["LEXTERM_BENCH_MODEL"])
    if folder not in _embedders:
        _embedders[folder] = Embedder(folder)
    return _embedders[folder]


def index(names: list[str], lower: bool = False) -> Index:
    """The index of these names, built once for each list."""
    model = embedder()
    key = (model.folder, lower, hash(tuple(names)))
    if key not in _indexes:
        _indexes[key] = Index(model, names, lower)
    return _indexes[key]
