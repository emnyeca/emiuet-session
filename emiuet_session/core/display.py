"""DisplayState -- what the OLED/GUI needs to render, with no display library.

The engine returns this plain snapshot every frame. A renderer (OLED driver,
desktop GUI, CLI) formats it. The debug fields are extra context useful during
R&D and may be hidden on the small instrument display.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DisplayState:
    # Primary performance view.
    current_chord: str = ""
    next_chord: str = ""
    register_label: str = ""
    profile_label: str = ""
    slot_labels: tuple[str, ...] = ()  # 8 note labels, left to right

    # Progress.
    segment_index: int = 0
    segment_count: int = 0
    step_index: int = 0
    step_count: int = 0

    # Debug / R&D context (selected_collection, scale priority, etc.).
    selected_collection: str = ""
    scale_priority: int = 0
    retry_level: int = 0
    lpc: tuple[int, ...] = ()  # local pitch collection (pitch classes)
    active_notes: tuple[int, ...] = field(default_factory=tuple)

    def header_lines(self) -> list[str]:
        """The compact two/three-line view planned for the OLED."""
        top = f"{self.current_chord} > {self.next_chord}".strip(" >")
        mid = f"{self.register_label}  {self.profile_label}".strip()
        notes = " ".join(self.slot_labels)
        return [top, mid, notes]
