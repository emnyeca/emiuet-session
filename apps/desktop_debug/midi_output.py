"""Generic MIDI output adapter for the desktop debug harness.

Lives in ``apps/`` (an adapter). The core only returns abstract ``MidiEvent``s;
this module converts them to mido messages and sends them to a real MIDI OUT
port. ``mido`` is imported lazily, only when a real port is opened, so the
conversion logic and the tests run with no MIDI library installed.

Channel convention: ``MidiEvent.channel`` is user-facing (1..16); mido channels
are 0..15. The conversion subtracts 1 and validates the range.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from emiuet_session.core.midi import MidiEvent, MidiEventType

from .midi_input import _import_mido, resolve_port_name

ALL_NOTES_OFF_CC = 123


def to_mido_channel(channel_1based: int) -> int:
    """Convert a user-facing channel (1..16) to a mido channel (0..15)."""
    if not isinstance(channel_1based, int) or not 1 <= channel_1based <= 16:
        raise ValueError(f"MIDI channel must be 1..16 (user-facing), got {channel_1based!r}")
    return channel_1based - 1


def event_to_mido_spec(event: MidiEvent) -> dict | None:
    """Convert an abstract event to mido Message kwargs, or None if unsupported.

    Supported now: NoteOn, NoteOff, ControlChange, AllNotesOff. Anything else
    (e.g. PitchBend) returns None so the caller can log and skip it.
    """
    channel = to_mido_channel(event.channel)
    if event.type is MidiEventType.NOTE_ON:
        return {"type": "note_on", "channel": channel, "note": event.note, "velocity": event.velocity}
    if event.type is MidiEventType.NOTE_OFF:
        return {"type": "note_off", "channel": channel, "note": event.note, "velocity": 0}
    if event.type is MidiEventType.CONTROL_CHANGE:
        return {"type": "control_change", "channel": channel, "control": event.controller, "value": event.value}
    if event.type is MidiEventType.ALL_NOTES_OFF:
        return {"type": "control_change", "channel": channel, "control": ALL_NOTES_OFF_CC, "value": 0}
    return None


@dataclass
class MidiOutputAdapter:
    """Sends abstract MidiEvents to a MIDI OUT port (or logs only in dry-run).

    ``port`` is a mido output (anything with ``.send(msg)`` and ``.name``); when
    it is None the adapter is in dry-run mode -- it formats OUT log lines but
    sends nothing. ``message_factory`` builds a message from spec kwargs (mido's
    ``Message`` by default; tests inject a recording fake).
    """

    port: object | None = None
    message_factory: object | None = None
    name: str = "dry-run"
    _active_channels: set = field(default_factory=set)

    @classmethod
    def open(cls, name_or_index: str) -> "MidiOutputAdapter":
        mido = _import_mido()
        name = resolve_port_name(mido.get_output_names(), name_or_index, "output")
        port = mido.open_output(name)
        return cls(port=port, message_factory=mido.Message, name=port.name)

    def _send(self, spec: dict) -> None:
        if self.port is None:
            return
        factory = self.message_factory or _import_mido().Message
        self.port.send(factory(**spec))

    def send_event(self, event: MidiEvent) -> str:
        """Send one event; returns the OUT log line (user-facing channel)."""
        spec = event_to_mido_spec(event)
        if spec is None:
            return f"(unsupported {event.type.value}, not sent)"
        self._send(spec)
        if event.type is MidiEventType.NOTE_ON:
            self._active_channels.add(event.channel)
        return self._log_line(event, spec)

    def all_notes_off(self, channels: list[int] | None = None) -> list[str]:
        """Send CC 123 (All Notes Off) to the given channels (default: channels
        we have sent notes on). Returns the OUT log lines."""
        targets = sorted(channels if channels is not None else self._active_channels)
        lines: list[str] = []
        for ch in targets:
            self._send({"type": "control_change", "channel": to_mido_channel(ch),
                        "control": ALL_NOTES_OFF_CC, "value": 0})
            lines.append(f"all_notes_off ch={ch} -> {self.name}")
        return lines

    def close(self) -> None:
        if self.port is not None:
            self.port.close()

    def _log_line(self, event: MidiEvent, spec: dict) -> str:
        ch = event.channel  # user-facing 1..16
        if event.type is MidiEventType.NOTE_ON:
            return f"note_on ch={ch} note={event.note} velocity={event.velocity} -> {self.name}"
        if event.type is MidiEventType.NOTE_OFF:
            return f"note_off ch={ch} note={event.note} velocity=0 -> {self.name}"
        if event.type is MidiEventType.ALL_NOTES_OFF:
            return f"all_notes_off ch={ch} -> {self.name}"
        return f"control_change ch={ch} control={spec['control']} value={spec['value']} -> {self.name}"


def list_output_ports() -> list[str]:
    return list(_import_mido().get_output_names())
