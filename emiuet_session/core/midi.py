"""Abstract MIDI event model.

The core never calls a hardware/library MIDI API. It emits these plain events;
an adapter (firmware ``usbMIDI``/TRS, desktop virtual port, test assertion)
translates them. This keeps the engine portable and unit-testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MidiEventType(Enum):
    NOTE_ON = "note_on"
    NOTE_OFF = "note_off"
    CONTROL_CHANGE = "control_change"
    PITCH_BEND = "pitch_bend"
    ALL_NOTES_OFF = "all_notes_off"


@dataclass(frozen=True)
class MidiEvent:
    """One abstract MIDI message. Unused fields stay at their defaults."""

    type: MidiEventType
    channel: int = 1
    note: int = 0
    velocity: int = 0
    controller: int = 0
    value: int = 0
    pitch_bend: int = 0  # -8192..8191, 0 = centre

    @staticmethod
    def note_on(note: int, velocity: int, channel: int = 1) -> "MidiEvent":
        return MidiEvent(MidiEventType.NOTE_ON, channel=channel, note=note, velocity=velocity)

    @staticmethod
    def note_off(note: int, channel: int = 1) -> "MidiEvent":
        return MidiEvent(MidiEventType.NOTE_OFF, channel=channel, note=note)

    @staticmethod
    def control_change(controller: int, value: int, channel: int = 1) -> "MidiEvent":
        return MidiEvent(
            MidiEventType.CONTROL_CHANGE, channel=channel, controller=controller, value=value
        )

    @staticmethod
    def all_notes_off(channel: int = 1) -> "MidiEvent":
        return MidiEvent(MidiEventType.ALL_NOTES_OFF, channel=channel)

    def short(self) -> str:
        """Compact one-line form for debug/harness output."""
        if self.type is MidiEventType.NOTE_ON:
            return f"NoteOn  ch{self.channel} n{self.note:>3} v{self.velocity}"
        if self.type is MidiEventType.NOTE_OFF:
            return f"NoteOff ch{self.channel} n{self.note:>3}"
        if self.type is MidiEventType.CONTROL_CHANGE:
            return f"CC      ch{self.channel} c{self.controller} v{self.value}"
        if self.type is MidiEventType.ALL_NOTES_OFF:
            return f"AllNotesOff ch{self.channel}"
        return f"PitchBend ch{self.channel} {self.pitch_bend}"
