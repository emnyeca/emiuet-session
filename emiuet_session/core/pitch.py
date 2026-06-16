"""Pitch-class and MIDI-note helpers.

Pitch classes are integers 0..11 with C = 0. MIDI note 60 is middle C (C4).
These helpers are deliberately tiny and dependency-free so the firmware port
can mirror them directly.
"""

from __future__ import annotations

# Note: index == pitch class. Sharps and flats are both provided because the
# correct spelling depends on harmonic context (e.g. Eb in Dm vs D# elsewhere).
NOTE_NAMES_SHARP = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NOTE_NAMES_FLAT = ("C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B")

MIDDLE_C = 60


def pitch_class(midi_note: int) -> int:
    """Return the pitch class (0..11) of a MIDI note."""
    return midi_note % 12


def note_name(pc: int, *, prefer_flat: bool = True) -> str:
    """Human-readable note name for a pitch class."""
    names = NOTE_NAMES_FLAT if prefer_flat else NOTE_NAMES_SHARP
    return names[pc % 12]


def nearest_midi_note(pc: int, anchor: int) -> int:
    """MIDI note of pitch class ``pc`` closest to ``anchor``.

    Used by the layout builder and runtime to keep slot-to-slot movement small:
    given a pitch class and a reference note, pick the octave that minimises the
    semitone jump. Ties resolve upward (toward the anchor's register and above).
    """
    pc = pc % 12
    base = anchor - (anchor % 12) + pc  # same pc, near anchor's octave
    candidates = (base - 12, base, base + 12)
    return min(candidates, key=lambda n: (abs(n - anchor), -n))


def clamp_midi(note: int, lo: int = 0, hi: int = 127) -> int:
    """Clamp a MIDI note into the valid 0..127 range (or a tighter window)."""
    return max(lo, min(hi, note))
