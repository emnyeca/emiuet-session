"""Emiuet Session R&D core.

A portable, pure-Python improvisation engine for the Emiuet Session mini
instrument. The packages are split by responsibility:

- ``core``    : pure data types and helpers (no I/O, no GUI, no MIDI library)
- ``model``   : Song / Harmonic Analysis / Performance Model and the builders
- ``runtime`` : the playable engine (EmiuetCore) that turns input into MIDI
- ``fixtures``: built-in sample songs for R&D and tests

The C++ firmware port (Teensy / ESP32) is a separate, later phase. This package
mirrors the structure that port will use so the design decisions made here stay
portable. Nothing in ``core``/``model``/``runtime`` may import a GUI toolkit,
a MIDI library, or platform-specific I/O.
"""

__all__ = ["core", "model", "runtime", "fixtures"]
