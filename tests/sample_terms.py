# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""An invented terminology for the tests: lexterm brings none of its own."""

from __future__ import annotations

from lexcor import Concept, Package, Term

MEDICINE = "https://example.org/CodeSystem/medicine"


def medicine() -> Package:
    """A few concepts with German terms, a drug among them, and an eponym."""
    return Package(url=MEDICINE, version="1", title="Invented medicine", language="de", concepts=[
        Concept("C1", "arterielle Hypertonie", "disorder", "", [Term("Hypertonie", "de")]),
        Concept("C2", "Ramipril", "drug"),
        Concept("C3", "Diabetes mellitus", "disorder"),
        Concept("C4", "Parkinson-Syndrom", "disorder")])
