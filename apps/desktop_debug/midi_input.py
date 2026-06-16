"""Generic MIDI input adapter for the desktop debug harness.

This lives in ``apps/`` and is an *adapter* -- the engine core never imports it.
``mido`` / ``python-rtmidi`` are optional and imported lazily, only when a real
port is opened, so the mapping logic, the CLI, and the whole test suite work
with no MIDI library installed.

Flow::

    real port --mido--> MidiMessage --MidiInputMapper--> MappedEvent(InputFrame)

The mapper is pure and duck-typed: it reads ``msg.type/channel/note/velocity/
control/value``, so tests can feed plain ``MidiMessage`` objects without mido.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from emiuet_session.core.approach import ApproachDirection
from emiuet_session.core.frames import InputFrame, RegisterCommand, SegmentCommand

PROFILES_DIR = Path(__file__).parent / "controller_profiles"

# Action types in a profile mapping entry.
_ACTION_SLOT = "slot"
_ACTION_COMMAND = "command"

# Commands that are momentary modifiers (press AND release matter). Every other
# command is a one-shot trigger that fires on press and ignores release.
_APPROACH = {
    "approach_plus": ApproachDirection.PLUS,
    "approach_minus": ApproachDirection.MINUS,
}
_TRIGGER_COMMANDS = {
    "next_segment",
    "previous_segment",
    "register_up",
    "register_down",
    "register_reset",
    "profile_cycle",
    "panic",
}
COMMAND_NAMES = _TRIGGER_COMMANDS | set(_APPROACH)

# A CC button counts as pressed at or above this value (MIDI half-way).
CC_PRESS_THRESHOLD = 64


class ProfileError(ValueError):
    """Raised when a controller profile is missing or malformed."""


@dataclass
class MidiMessage:
    """Minimal, mido-compatible MIDI message (channel is 0-based, like mido)."""

    type: str
    channel: int = 0
    note: int = 0
    velocity: int = 0
    control: int = 0
    value: int = 0

    @classmethod
    def from_mido(cls, m) -> "MidiMessage":
        return cls(
            type=m.type,
            channel=getattr(m, "channel", 0),
            note=getattr(m, "note", 0),
            velocity=getattr(m, "velocity", 0),
            control=getattr(m, "control", 0),
            value=getattr(m, "value", 0),
        )

    def describe(self) -> str:
        ch = self.channel + 1  # show 1-based, matching most controller displays
        if self.type in ("note_on", "note_off"):
            return f"{self.type} ch={ch} note={self.note} velocity={self.velocity}"
        if self.type == "control_change":
            return f"control_change ch={ch} control={self.control} value={self.value}"
        return f"{self.type} ch={ch} (unsupported, logged only)"


@dataclass
class ControllerProfile:
    name: str
    midi_channel: int | None  # 1-based; None = match any channel
    note_mappings: dict[int, dict]
    control_mappings: dict[int, dict]

    @classmethod
    def from_dict(cls, data: dict) -> "ControllerProfile":
        if not isinstance(data, dict):
            raise ProfileError("profile must be a JSON object")
        name = data.get("name", "unnamed profile")
        channel = data.get("midi_channel")
        if channel is not None and not (isinstance(channel, int) and 1 <= channel <= 16):
            raise ProfileError(f"midi_channel must be 1..16 or omitted, got {channel!r}")
        note_mappings = _parse_mappings(data.get("note_mappings", {}), "note_mappings")
        control_mappings = _parse_mappings(data.get("control_mappings", {}), "control_mappings")
        return cls(name, channel, note_mappings, control_mappings)

    @classmethod
    def load(cls, path: str | Path) -> "ControllerProfile":
        p = Path(path)
        if not p.exists():
            raise ProfileError(f"controller profile not found: {p}")
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ProfileError(f"controller profile {p} is not valid JSON: {exc}") from exc
        return cls.from_dict(data)


def _parse_mappings(raw: dict, where: str) -> dict[int, dict]:
    if not isinstance(raw, dict):
        raise ProfileError(f"{where} must be a JSON object")
    out: dict[int, dict] = {}
    for key, entry in raw.items():
        try:
            number = int(key)
        except (TypeError, ValueError):
            raise ProfileError(f"{where} key {key!r} must be an integer (MIDI number)")
        _validate_entry(entry, where, key)
        out[number] = entry
    return out


def _validate_entry(entry: dict, where: str, key) -> None:
    if not isinstance(entry, dict) or "type" not in entry:
        raise ProfileError(f"{where}[{key}] must be an object with a 'type'")
    kind = entry["type"]
    if kind == _ACTION_SLOT:
        slot = entry.get("slot")
        if not (isinstance(slot, int) and 0 <= slot <= 7):
            raise ProfileError(f"{where}[{key}] slot must be 0..7, got {slot!r}")
    elif kind == _ACTION_COMMAND:
        command = entry.get("command")
        if command not in COMMAND_NAMES:
            raise ProfileError(
                f"{where}[{key}] command {command!r} unknown; expected one of "
                f"{sorted(COMMAND_NAMES)}"
            )
    else:
        raise ProfileError(f"{where}[{key}] type must be 'slot' or 'command', got {kind!r}")


@dataclass
class MappedEvent:
    """The result of mapping one MIDI message."""

    raw: str
    mapped: str | None  # human-readable mapped action, or None if unmapped
    frame: InputFrame | None  # the engine input, or None if nothing to do


class MidiInputMapper:
    """Turns MIDI messages into engine InputFrames via a controller profile."""

    def __init__(self, profile: ControllerProfile) -> None:
        self.profile = profile

    def map(self, msg: MidiMessage) -> MappedEvent:
        raw = msg.describe()

        if self.profile.midi_channel is not None and msg.channel != self.profile.midi_channel - 1:
            return MappedEvent(raw, f"(channel {msg.channel + 1} ignored)", None)

        entry, is_press = self._lookup(msg)
        if entry is None:
            return MappedEvent(raw, None, None)  # unmapped / unsupported -> log only

        return self._to_frame(entry, is_press, raw)

    def _lookup(self, msg: MidiMessage) -> tuple[dict | None, bool]:
        if msg.type == "note_on":
            return self.profile.note_mappings.get(msg.note), msg.velocity > 0
        if msg.type == "note_off":
            return self.profile.note_mappings.get(msg.note), False
        if msg.type == "control_change":
            return self.profile.control_mappings.get(msg.control), msg.value >= CC_PRESS_THRESHOLD
        return None, False  # program_change, pitchwheel, clock, etc.

    def _to_frame(self, entry: dict, is_press: bool, raw: str) -> MappedEvent:
        if entry["type"] == _ACTION_SLOT:
            slot = entry["slot"]
            if is_press:
                return MappedEvent(raw, f"slot {slot} press", InputFrame(key_presses=(slot,)))
            return MappedEvent(raw, f"slot {slot} release", InputFrame(key_releases=(slot,)))

        command = entry["command"]
        if command in _APPROACH:
            direction = _APPROACH[command]
            if is_press:
                return MappedEvent(raw, f"{command} press", InputFrame(approach_press=direction))
            return MappedEvent(raw, f"{command} release", InputFrame(approach_release=direction))

        # One-shot trigger commands fire on press only.
        if not is_press:
            return MappedEvent(raw, f"{command} (release ignored)", None)
        return MappedEvent(raw, command, _trigger_frame(command))


def _trigger_frame(command: str) -> InputFrame:
    if command == "next_segment":
        return InputFrame(segment_command=SegmentCommand.NEXT)
    if command == "previous_segment":
        return InputFrame(segment_command=SegmentCommand.PREV)
    if command == "register_up":
        return InputFrame(register_command=RegisterCommand.UP)
    if command == "register_down":
        return InputFrame(register_command=RegisterCommand.DOWN)
    if command == "register_reset":
        return InputFrame(register_command=RegisterCommand.RESET)
    if command == "profile_cycle":
        return InputFrame(profile_command="cycle")
    if command == "panic":
        return InputFrame(panic=True)
    raise ProfileError(f"unhandled command {command!r}")  # unreachable if validated


# --- real MIDI port helpers (mido imported lazily) -------------------------


def _import_mido():
    try:
        import mido
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "MIDI input needs the optional 'mido' (+ python-rtmidi) packages.\n"
            "Install them with:  pip install -r requirements-midi.txt"
        ) from exc
    return mido


def list_input_ports() -> list[str]:
    return list(_import_mido().get_input_names())


def open_input(name_or_index: str):
    """Open a MIDI input by exact name, case-insensitive substring, or index."""
    mido = _import_mido()
    names = mido.get_input_names()
    if not names:
        raise RuntimeError("no MIDI input ports found (is the controller connected?)")

    if name_or_index.isdigit():
        idx = int(name_or_index)
        if not 0 <= idx < len(names):
            raise RuntimeError(f"port index {idx} out of range (0..{len(names) - 1})")
        return mido.open_input(names[idx])

    if name_or_index in names:
        return mido.open_input(name_or_index)
    matches = [n for n in names if name_or_index.lower() in n.lower()]
    if len(matches) == 1:
        return mido.open_input(matches[0])
    if not matches:
        raise RuntimeError(f"no MIDI input matches {name_or_index!r}. Available: {names}")
    raise RuntimeError(f"{name_or_index!r} is ambiguous, matches: {matches}")
