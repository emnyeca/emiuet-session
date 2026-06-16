"""Harmonic Analysis model -- the export target for EUB Changes.

This represents the *result* of Changes' chord analysis: the local pitch
collection, the chosen scale, and per-pitch roles/weights. Emiuet Session reads
this; it does not compute it. The fields below are the contract we want Changes
to fill. They need not match Changes' internal structures exactly yet, but the
shape is designed so a Changes exporter can populate it.

See docs/emiuet_performance_model.md for the assumptions made where the Changes
theory spec is not yet wired in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PitchRole(Enum):
    """Why a pitch is in the collection -- drives 8-slot placement."""

    CORE = "core"  # chord tone, high importance
    TENSION = "tension"  # available tension (9/11/13)
    ALTERED_TENSION = "altered_tension"  # b9/#9/#11/b13 etc.
    APPROACH = "approach"  # chromatic approach note
    AVOID = "avoid"  # avoid note (suppressed in NORMAL profile)
    COLOR = "color"  # scale colour tone, lower priority


@dataclass(frozen=True)
class PitchCandidate:
    pitch_class: int  # 0..11
    label: str  # degree/name, e.g. "b9", "M3", "13"
    role: PitchRole
    weight: float = 0.0  # importance, higher = place first
    stability: float = 0.0  # 0..1, how resolved/restful
    tension: float = 0.0  # 0..1, how tense/colourful


@dataclass
class HarmonicStep:
    """Analysis for one chord change."""

    chord_symbol: str
    root_pc: int
    quality: str  # e.g. "m7", "7", "maj7", "7alt"
    chord_tones: tuple[int, ...] = ()  # pitch classes
    local_pitch_collection: tuple[int, ...] = ()  # pitch classes (LPC)
    scale_collection: str = ""  # selected scale name
    scale_priority: int = 0  # priority rank of selected scale (lower = higher)
    retry_level: int = 0  # fallback/retry depth used to reach this result
    candidates: list[PitchCandidate] = field(default_factory=list)

    def candidates_with_roles(self, roles: set[PitchRole]) -> list[PitchCandidate]:
        return [c for c in self.candidates if c.role in roles]


@dataclass
class HarmonicAnalysis:
    """Ordered analysis steps aligned with the song's chord changes."""

    title: str = ""
    steps: list[HarmonicStep] = field(default_factory=list)
