"""MIDI output adapter conversion and sending (no MIDI hardware/library)."""

import pytest

from apps.desktop_debug.midi_controller_harness import _emit
from apps.desktop_debug.midi_input import ControllerProfile, MidiInputMapper, MidiMessage
from apps.desktop_debug.midi_output import (
    MidiOutputAdapter,
    event_to_mido_spec,
    to_mido_channel,
)
from emiuet_session.core.frames import InputFrame
from emiuet_session.core.midi import MidiEvent
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore

from apps.desktop_debug.cli import DebugConsole


class FakePort:
    """Records sent messages; stands in for a mido output port in tests."""

    def __init__(self):
        self.sent = []
        self.name = "fake-out"
        self.closed = False

    def send(self, msg):
        self.sent.append(msg)

    def close(self):
        self.closed = True


def make_adapter():
    # identity message_factory so sent messages are the plain spec dicts
    return MidiOutputAdapter(port=FakePort(), message_factory=lambda **k: k, name="fake-out")


# --- channel conversion --------------------------------------------------


def test_channel_one_maps_to_mido_zero():
    assert to_mido_channel(1) == 0


def test_channel_sixteen_maps_to_mido_fifteen():
    assert to_mido_channel(16) == 15


@pytest.mark.parametrize("bad", [0, 17, -1])
def test_invalid_channel_rejected(bad):
    with pytest.raises(ValueError, match="1..16"):
        to_mido_channel(bad)


# --- event -> mido spec --------------------------------------------------


def test_note_on_converts_to_mido_note_on():
    spec = event_to_mido_spec(MidiEvent.note_on(60, 100, channel=1))
    assert spec == {"type": "note_on", "channel": 0, "note": 60, "velocity": 100}


def test_note_off_converts_to_mido_note_off():
    spec = event_to_mido_spec(MidiEvent.note_off(60, channel=16))
    assert spec == {"type": "note_off", "channel": 15, "note": 60, "velocity": 0}


def test_all_notes_off_converts_to_cc_123():
    spec = event_to_mido_spec(MidiEvent.all_notes_off(channel=1))
    assert spec == {"type": "control_change", "channel": 0, "control": 123, "value": 0}


def test_unsupported_event_returns_none():
    from emiuet_session.core.midi import MidiEventType

    assert event_to_mido_spec(MidiEvent(MidiEventType.PITCH_BEND, channel=1)) is None


# --- adapter behaviour ---------------------------------------------------


def test_send_note_on_reaches_port():
    adapter = make_adapter()
    line = adapter.send_event(MidiEvent.note_on(60, 100, channel=1))
    assert adapter.port.sent == [{"type": "note_on", "channel": 0, "note": 60, "velocity": 100}]
    assert "note_on ch=1 note=60 velocity=100 -> fake-out" == line


def test_unsupported_event_is_logged_not_sent():
    from emiuet_session.core.midi import MidiEventType

    adapter = make_adapter()
    line = adapter.send_event(MidiEvent(MidiEventType.PITCH_BEND, channel=1))
    assert adapter.port.sent == []
    assert "unsupported" in line


def test_all_notes_off_targets_used_channels():
    adapter = make_adapter()
    adapter.send_event(MidiEvent.note_on(60, 100, channel=1))
    adapter.port.sent.clear()
    lines = adapter.all_notes_off()
    assert adapter.port.sent == [{"type": "control_change", "channel": 0, "control": 123, "value": 0}]
    assert lines == ["all_notes_off ch=1 -> fake-out"]


def test_dry_run_adapter_sends_nothing_but_logs():
    adapter = MidiOutputAdapter()  # port=None
    line = adapter.send_event(MidiEvent.note_on(60, 100, channel=1))
    assert "note_on ch=1 note=60 velocity=100 -> dry-run" == line  # no crash, no port


# --- harness wiring ------------------------------------------------------


def _console():
    return DebugConsole(EmiuetCore(sample_performance_model()))


def test_emit_without_adapter_logs_only(capsys):
    console = _console()
    _emit(console, _mapped(0), None, InputFrame(key_presses=(0,)))
    out = capsys.readouterr().out
    assert "CORE" in out and "OUT" not in out  # no output sent


def test_emit_with_adapter_sends_core_events(capsys):
    console = _console()
    adapter = make_adapter()
    _emit(console, _mapped(0), adapter, InputFrame(key_presses=(0,)))
    out = capsys.readouterr().out
    assert "OUT" in out
    assert any(m["type"] == "note_on" for m in adapter.port.sent)


def _mapped(slot):
    profile = ControllerProfile.from_dict(
        {"name": "t", "note_mappings": {"36": {"type": "slot", "slot": slot}}}
    )
    return MidiInputMapper(profile).map(MidiMessage("note_on", note=36, velocity=127))
