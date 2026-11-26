# SPDX-FileCopyrightText: 2026 fre.ms
# SPDX-License-Identifier: MIT
"""What is medical in the rules of recognition.

The core matches words; these two tables are what a medical library adds to it (lexcor's
design, section 4.5).
"""

from __future__ import annotations

# Spellings that German medicine has side by side: "Colitis" and "Kolitis", "Phenytoin" and
# "Fenytoin".  A term and a text agree where they are the same after these replacements, made
# in this order.  Measured on discharge letters: the table finds places a plain matcher
# misses ("Hepatische Encephalopathie") and assigns nothing wrongly, where a tolerance for one
# wrong letter did ("Papille" for "Pupille").
VARIANTS: tuple[tuple[str, str], ...] = (
    ("ph", "f"), ("th", "t"), ("rh", "r"), ("ce", "ze"), ("ci", "zi"), ("cy", "zy"),
    ("cae", "zae"), ("c", "k"), ("y", "i"),
)

# Head nouns after which the first part of a hyphenated term is an eponym that reports use on
# its own ("Babinski-Zeichen", then "Babinski positiv").  Heads of anatomy and chemistry are
# left out on purpose: "Müller-Gang" and "Berlin-Blau" must not make the surname Müller or the
# town Berlin medical vocabulary.
EPONYM_HEADS: frozenset[str] = frozenset({
    "zeichen", "syndrom", "test", "probe", "manöver", "manoever", "reflex", "phänomen",
    "phaenomen", "skala", "score", "index", "trias", "kriterien", "klassifikation", "lagerung",
    "griff", "punkt", "position", "stadium", "formel", "gleichung", "koeffizient", "regel",
    "gesetz", "effekt", "reaktion", "methode", "verfahren", "technik", "operation", "naht",
    "schnitt", "zugang",
})
