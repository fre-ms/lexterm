# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""The command line of lexterm: the core's commands under lexterm's name.

    lexterm packages list | import FILE | export PACKAGE FILE | remove PACKAGE
    lexterm tag FILE [--package PACKAGE]... [--class CLASS]...

The store is lexterm's in the user's data folder unless ``--store`` names another.  A store
that holds no package yet is answered from the packages that come with lexterm, so that
``lexterm tag`` works from the first call.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import lexcor.cli
from lexcor import Mention, Store

import lexterm


def _tag(text: str, store: Store, packages: Iterable[str] | None,
         classes: Iterable[str] | None) -> list[Mention]:
    return lexterm.tag(text, store if store.packages() else None, packages, classes)


def main(arguments: Sequence[str] | None = None) -> int:
    """Run one command; returns the exit code."""
    return lexcor.cli.main(arguments, program="lexterm", library="lexterm", tagger=_tag)


if __name__ == "__main__":
    raise SystemExit(main())
