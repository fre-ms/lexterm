# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm's package window: lexcor's, with lexterm's readers (the Alpha-ID-SE, releases of
SNOMED CT) and its text on where terminologies come from.

It needs PySide6 (``pip install "lexterm[window]"``).  A program that shows lexcor's
:class:`~lexcor.window.PackageWindow` over lexterm's store hands it :func:`readers` and
:func:`lexterm.sources.html`.
"""

from __future__ import annotations

from pathlib import Path

from lexcor import Package, Store, say
from lexcor.window import Reader
from lexcor.window import open_window as open_core_window

from lexterm import sources


def _alpha_id(path: Path) -> list[Package]:
    from lexterm.alphaid import read_alpha_id

    return read_alpha_id(path)[0]


def _snomed(path: Path) -> list[Package]:
    from lexterm.snomed import read_rf2

    return [read_rf2(path)]


def readers() -> tuple[Reader, ...]:
    """The forms lexterm reads packages from besides lexcor's."""
    return (Reader(("Alpha-ID-SE des BfArM (ZIP oder Datendatei)",
                    "Alpha-ID-SE of the BfArM (ZIP or data file)"), _alpha_id, False,
                   "*.zip *.txt"),
            Reader(("SNOMED-CT-Ausgabe (ZIP-Datei, wie geladen)",
                    "SNOMED CT release (ZIP file as downloaded)"), _snomed, False, "*.zip"),
            Reader(("SNOMED-CT-Ausgabe (entpackter RF2-Ordner)",
                    "SNOMED CT release (unpacked RF2 folder)"), _snomed, True))


def open_window(store: Store) -> int:
    """Open the package window over lexterm's store, until the person closes it."""
    return open_core_window(store, readers(), sources.html(),
                            say("lexterm: Pakete", "lexterm: packages"))
