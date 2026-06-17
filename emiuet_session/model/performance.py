"""Emiuet Session Performance Model -- the playable layout, distinct from Song.

Key definitions:
- Segment: the unit a player advances with one Next press.
- Step   : a chord change *inside* a segment; steps auto-advance by tempo.

So one Next press moves to the next Segment; if that Segment holds several
Steps, the engine walks them automatically at the current tempo. This keeps
manual operation to a comfortable rate even at fast tempos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..core.pitch import note_name


class SlotKind(Enum):
    CORE = "core"
    COLOR = "color"
    TENSION = "tension"
    ALTERED = "altered"
    APPROACH = "approach"


class LayoutOrientation(Enum):
    """How the 8 slots are read on the surface.

    The slot indices (0..7, even = core, odd = colour) are the same in both; only
    the visual/melodic interpretation differs.
    """

    # ``■ □ ■ □ ■ □ ■ □`` -- one row, core and colour interleaved (legacy).
    ALTERNATING_ROW = "alternating_row"
    # Two rows of four: bottom = core line, top = colour line. Each line ascends
    # left-to-right; the interleaved reading need not ascend. R&D default.
    #   □ □ □ □   (colour: slots 1 3 5 7)
    #   ■ ■ ■ ■   (core:   slots 0 2 4 6)
    TWO_ROW_CORE_COLOR = "two_row_core_color"


@dataclass(frozen=True)
class Slot:
    index: int  # 0..7
    kind: SlotKind
    pitch_class: int
    preferred_midi: int
    label: str
    weight: float = 0.0
    source_degree: str = ""  # degree/label from the analysis candidate

    def is_core_position(self) -> bool:
        return self.index % 2 == 0


@dataclass(frozen=True)
class Layout:
    """Exactly 8 slots, core in even positions, colour in odd positions."""

    slots: tuple[Slot, ...]
    orientation: LayoutOrientation = LayoutOrientation.TWO_ROW_CORE_COLOR

    def __post_init__(self) -> None:
        if len(self.slots) != 8:
            raise ValueError(f"Layout must have 8 slots, got {len(self.slots)}")

    def labels(self) -> tuple[str, ...]:
        return tuple(s.label for s in self.slots)

    def note_labels(self) -> tuple[str, ...]:
        return tuple(note_name(s.pitch_class) for s in self.slots)

    def core_slots(self) -> tuple[Slot, ...]:
        """The core line (bottom row): slots 0, 2, 4, 6 -- ascending in pitch."""
        return tuple(self.slots[i] for i in (0, 2, 4, 6))

    def color_slots(self) -> tuple[Slot, ...]:
        """The colour line (top row): slots 1, 3, 5, 7 -- ascending in pitch."""
        return tuple(self.slots[i] for i in (1, 3, 5, 7))


@dataclass
class Step:
    step_id: str
    beat_offset: float  # offset within the segment, in quarter-beats
    duration_beats: float  # length in quarter-beats
    chord: str
    next_chord: str
    analysis_summary: str
    layout: Layout
    profiles: dict = field(default_factory=dict)  # profile -> Layout (future)

    # Debug/R&D context carried from the analysis so the engine can build a
    # DisplayState without depending on the analysis layer at runtime.
    scale_collection: str = ""
    scale_priority: int = 0
    retry_level: int = 0
    lpc: tuple[int, ...] = ()
    core_pcs: tuple[int, ...] = ()  # chord tones (core pitch classes), for Solo Mode


@dataclass
class Segment:
    segment_id: str
    label: str
    manual_advance_length: float  # quarter-beats covered by one Next press
    duration_beats: float
    steps: list[Step] = field(default_factory=list)


@dataclass
class PerformanceModel:
    version: int = 1
    source_title: str = ""
    default_tempo: float = 120.0
    meter: str = "4/4"
    segments: list[Segment] = field(default_factory=list)

    def segment_count(self) -> int:
        return len(self.segments)
