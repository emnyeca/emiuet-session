"""Lightweight Song reference model.

This is *not* a re-implementation of EUB Changes' song model. It is the minimal
shape Emiuet Session needs to receive a Changes export later: structure, meter,
tempo and chord symbols positioned in bars. Chord analysis is NOT done here --
that is Changes' responsibility (see HarmonicAnalysis).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Meter:
    numerator: int = 4
    denominator: int = 4

    def __str__(self) -> str:
        return f"{self.numerator}/{self.denominator}"

    @property
    def beats_per_bar(self) -> float:
        """Bar length measured in quarter-note beats (the universal unit)."""
        return self.numerator * (4.0 / self.denominator)


@dataclass(frozen=True)
class ChordSymbol:
    """A chord placed at a bar/beat. ``beats`` is its duration in quarter-beats."""

    symbol: str
    bar: int
    beat: float = 0.0
    beats: float = 4.0


@dataclass
class Section:
    name: str
    chords: list[ChordSymbol] = field(default_factory=list)


@dataclass
class Song:
    title: str
    default_tempo: float = 120.0
    meter: Meter = field(default_factory=Meter)
    sections: list[Section] = field(default_factory=list)

    def chords(self) -> list[ChordSymbol]:
        out: list[ChordSymbol] = []
        for section in self.sections:
            out.extend(section.chords)
        return out
