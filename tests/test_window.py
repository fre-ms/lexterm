# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""lexterm's package window: lexcor's, with lexterm's readers and its text on where
terminologies come from."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from lexcor import set_language

import lexterm
from lexterm import sources
from lexterm.alphaid import ALPHA_ID


def test_the_sources_come_as_html_with_every_link() -> None:
    page = sources.html("de")
    for source in sources.sources("de"):
        assert source["name"] in page
        assert all(f'href="{link["url"]}"' in page for link in source["links"])
    assert "<script" not in page and "„Aufnehmen …“" in page


qt = pytest.importorskip("PySide6.QtWidgets")


def test_the_window_reads_the_alpha_id_and_shows_where_it_comes_from(tmp_path: Path) -> None:
    from lexcor.window import PackageWindow
    from test_alphaid import data_file  # the tests' folder is on the path as pytest runs them

    from lexterm.window import readers

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    set_language("en")
    app = qt.QApplication.instance() or qt.QApplication([])
    try:
        alpha_id, snomed_zip, snomed = readers()
        assert (alpha_id.folder, snomed_zip.folder, snomed.folder) == (False, False, True)
        with lexterm.open_store(tmp_path / "store.sqlite") as store:
            window = PackageWindow(store, readers(), sources.html("en"))
            assert [a.text() for a in window.take.menu().actions()] == [
                "FHIR CodeSystem, FHIR package or list …",
                "Alpha-ID-SE of the BfArM (ZIP or data file) …",
                "SNOMED CT release (ZIP file as downloaded) …",
                "SNOMED CT release (unpacked RF2 folder) …"]
            worker = window.take_in(data_file(tmp_path / "file"), alpha_id)
            worker.wait(10_000)
            app.processEvents()
            assert "Taken in: Alpha-ID-SE, 4 concepts" in window.status.text()
            assert ALPHA_ID in window.list.chosen()
            assert "Getting" not in window.sources.toPlainText()
            assert "Alpha-ID-SE of the BfArM" in window.sources.toPlainText()
    finally:
        set_language(None)
