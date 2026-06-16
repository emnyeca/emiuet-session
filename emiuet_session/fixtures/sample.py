"""Built-in sample: ``Dm7 | G7 | Cmaj7 | A7alt`` in 4/4.

A short ii-V-I (in C) plus a turnaround dominant. It exercises smooth voice
leading (Dm7->G7->Cmaj7 share tones), an avoid note (the 11 on G7 and Cmaj7),
and altered tensions (A7alt).

Assumptions made where the EUB Changes theory spec is not yet wired in (these
are documented in docs/emiuet_performance_model.md):
- Weights/stability/tension are hand-set placeholders, not Changes output.
- A7alt's core is taken as the A7 chord tones (A C# E G); the altered notes are
  modelled as ALTERED_TENSION/COLOR candidates. The natural 5th is retained as a
  core tone for the 8-key surface even though a strict altered scale omits it.
- LPCs are the obvious parent scales (Dorian/Mixolydian/Ionian/Altered).
"""

from __future__ import annotations

from ..model.analysis import HarmonicAnalysis, HarmonicStep, PitchCandidate, PitchRole
from ..model.build import build_performance_model
from ..model.performance import PerformanceModel
from ..model.song import ChordSymbol, Meter, Section, Song

# pitch classes: C0 Db1 D2 Eb3 E4 F5 F#6 G7 Ab8 A9 Bb10 B11
_C = PitchCandidate  # local alias to keep the table readable
_CORE = PitchRole.CORE
_TEN = PitchRole.TENSION
_ALT = PitchRole.ALTERED_TENSION
_COL = PitchRole.COLOR
_AVOID = PitchRole.AVOID


def sample_song() -> Song:
    chords = [
        ChordSymbol("Dm7", bar=1, beats=4.0),
        ChordSymbol("G7", bar=2, beats=4.0),
        ChordSymbol("Cmaj7", bar=3, beats=4.0),
        ChordSymbol("A7alt", bar=4, beats=4.0),
    ]
    return Song(
        title="Sample ii-V-I Turnaround",
        default_tempo=120.0,
        meter=Meter(4, 4),
        sections=[Section(name="A", chords=chords)],
    )


def sample_analysis() -> HarmonicAnalysis:
    return HarmonicAnalysis(
        title="Sample ii-V-I Turnaround",
        steps=[
            HarmonicStep(
                chord_symbol="Dm7",
                root_pc=2,
                quality="m7",
                chord_tones=(2, 5, 9, 0),
                local_pitch_collection=(2, 4, 5, 7, 9, 11, 0),
                scale_collection="D Dorian",
                scale_priority=1,
                retry_level=0,
                candidates=[
                    _C(2, "R", _CORE, weight=1.00, stability=0.9, tension=0.0),
                    _C(5, "m3", _CORE, weight=0.90, stability=0.8, tension=0.1),
                    _C(0, "m7", _CORE, weight=0.85, stability=0.7, tension=0.2),
                    _C(9, "5", _CORE, weight=0.70, stability=0.85, tension=0.0),
                    _C(4, "9", _TEN, weight=0.65, stability=0.4, tension=0.5),
                    _C(11, "13", _TEN, weight=0.60, stability=0.35, tension=0.55),
                    _C(7, "11", _COL, weight=0.55, stability=0.4, tension=0.5),
                ],
            ),
            HarmonicStep(
                chord_symbol="G7",
                root_pc=7,
                quality="7",
                chord_tones=(7, 11, 2, 5),
                local_pitch_collection=(7, 9, 11, 0, 2, 4, 5),
                scale_collection="G Mixolydian",
                scale_priority=1,
                retry_level=0,
                candidates=[
                    _C(7, "R", _CORE, weight=1.00, stability=0.9, tension=0.0),
                    _C(11, "M3", _CORE, weight=0.90, stability=0.8, tension=0.1),
                    _C(5, "m7", _CORE, weight=0.85, stability=0.7, tension=0.3),
                    _C(2, "5", _CORE, weight=0.70, stability=0.85, tension=0.0),
                    _C(9, "9", _TEN, weight=0.65, stability=0.4, tension=0.5),
                    _C(4, "13", _TEN, weight=0.60, stability=0.4, tension=0.5),
                    _C(8, "b9", _ALT, weight=0.50, stability=0.2, tension=0.8),
                    _C(10, "#9", _ALT, weight=0.50, stability=0.2, tension=0.8),
                    _C(0, "11", _AVOID, weight=0.10, stability=0.3, tension=0.6),
                ],
            ),
            HarmonicStep(
                chord_symbol="Cmaj7",
                root_pc=0,
                quality="maj7",
                chord_tones=(0, 4, 7, 11),
                local_pitch_collection=(0, 2, 4, 5, 7, 9, 11),
                scale_collection="C Ionian",
                scale_priority=1,
                retry_level=0,
                candidates=[
                    _C(0, "R", _CORE, weight=1.00, stability=0.95, tension=0.0),
                    _C(4, "M3", _CORE, weight=0.90, stability=0.8, tension=0.1),
                    _C(11, "M7", _CORE, weight=0.85, stability=0.7, tension=0.2),
                    _C(7, "5", _CORE, weight=0.70, stability=0.85, tension=0.0),
                    _C(2, "9", _TEN, weight=0.65, stability=0.4, tension=0.45),
                    _C(9, "13", _TEN, weight=0.60, stability=0.4, tension=0.45),
                    _C(5, "11", _AVOID, weight=0.10, stability=0.3, tension=0.7),
                ],
            ),
            HarmonicStep(
                chord_symbol="A7alt",
                root_pc=9,
                quality="7alt",
                chord_tones=(9, 1, 4, 7),
                local_pitch_collection=(9, 10, 0, 1, 3, 5, 7),
                scale_collection="A Altered",
                scale_priority=2,
                retry_level=1,
                candidates=[
                    _C(9, "R", _CORE, weight=1.00, stability=0.85, tension=0.1),
                    _C(1, "M3", _CORE, weight=0.90, stability=0.75, tension=0.2),
                    _C(7, "m7", _CORE, weight=0.85, stability=0.7, tension=0.3),
                    _C(4, "5", _CORE, weight=0.60, stability=0.7, tension=0.2),
                    _C(10, "b9", _ALT, weight=0.55, stability=0.15, tension=0.85),
                    _C(0, "#9", _ALT, weight=0.55, stability=0.15, tension=0.85),
                    _C(3, "b5", _ALT, weight=0.50, stability=0.2, tension=0.8),
                    _C(5, "b13", _COL, weight=0.50, stability=0.25, tension=0.75),
                ],
            ),
        ],
    )


def sample_performance_model() -> PerformanceModel:
    return build_performance_model(sample_song(), sample_analysis())
