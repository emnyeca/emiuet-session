"""MIDI input adapter mapping (no MIDI hardware or library required)."""

import pytest

from apps.desktop_debug.midi_input import (
    PROFILES_DIR,
    ControllerProfile,
    MidiInputMapper,
    MidiMessage,
    ProfileError,
)
from emiuet_session.core.approach import ApproachDirection
from emiuet_session.core.frames import RegisterCommand, SegmentCommand

PROFILE = ControllerProfile.from_dict(
    {
        "name": "test",
        "midi_channel": 1,
        "note_mappings": {
            "36": {"type": "slot", "slot": 0},
            "44": {"type": "command", "command": "register_down"},
            "47": {"type": "command", "command": "register_up"},
            "48": {"type": "command", "command": "approach_plus"},
            "49": {"type": "command", "command": "approach_minus"},
            "50": {"type": "command", "command": "panic"},
        },
        "control_mappings": {
            "21": {"type": "command", "command": "next_segment"},
            "25": {"type": "command", "command": "approach_plus"},
        },
    }
)


def mapper():
    return MidiInputMapper(PROFILE)


def test_note_on_maps_to_slot_press():
    frame = mapper().map(MidiMessage("note_on", note=36, velocity=100)).frame
    assert frame.key_presses == (0,) and frame.key_releases == ()


def test_note_off_maps_to_slot_release():
    frame = mapper().map(MidiMessage("note_off", note=36)).frame
    assert frame.key_releases == (0,) and frame.key_presses == ()


def test_note_on_velocity_zero_is_release():
    frame = mapper().map(MidiMessage("note_on", note=36, velocity=0)).frame
    assert frame.key_releases == (0,) and frame.key_presses == ()


def test_cc_at_or_above_threshold_is_command_press():
    frame = mapper().map(MidiMessage("control_change", control=21, value=64)).frame
    assert frame.segment_command == SegmentCommand.NEXT


def test_cc_below_threshold_is_release():
    # A momentary command (approach) released by a low CC value.
    result = mapper().map(MidiMessage("control_change", control=25, value=10))
    assert result.frame.approach_release is ApproachDirection.PLUS
    # A one-shot trigger command ignores the release edge entirely.
    trigger = mapper().map(MidiMessage("control_change", control=21, value=10))
    assert trigger.frame is None and "release ignored" in trigger.mapped


def test_next_segment_reflected_in_frame():
    frame = mapper().map(MidiMessage("control_change", control=21, value=127)).frame
    assert frame.segment_command == SegmentCommand.NEXT


def test_register_up_and_down_reflected_in_frame():
    up = mapper().map(MidiMessage("note_on", note=47, velocity=120)).frame
    down = mapper().map(MidiMessage("note_on", note=44, velocity=120)).frame
    assert up.register_command == RegisterCommand.UP
    assert down.register_command == RegisterCommand.DOWN


def test_approach_press_and_release():
    on = mapper().map(MidiMessage("note_on", note=48, velocity=100)).frame
    off = mapper().map(MidiMessage("note_off", note=48)).frame
    assert on.approach_press is ApproachDirection.PLUS
    assert off.approach_release is ApproachDirection.PLUS


def test_panic_reflected_in_frame():
    frame = mapper().map(MidiMessage("note_on", note=50, velocity=127)).frame
    assert frame.panic is True


def test_unknown_note_is_ignored_but_logged():
    result = mapper().map(MidiMessage("note_on", note=99, velocity=100))
    assert result.frame is None
    assert result.mapped is None
    assert "note=99" in result.raw  # still available for the raw log


def test_unsupported_message_logged_only():
    result = mapper().map(MidiMessage("program_change"))
    assert result.frame is None and result.mapped is None
    assert "program_change" in result.raw


def test_other_channel_is_ignored():
    # Profile is channel 1 (0-based 0); a message on channel 2 (0-based 1) is skipped.
    result = mapper().map(MidiMessage("note_on", channel=1, note=36, velocity=100))
    assert result.frame is None


def test_bundled_profiles_load():
    for name in ("ccp16", "generic_16pad"):
        profile = ControllerProfile.load(PROFILES_DIR / f"{name}.json")
        assert profile.name
        slots = {e["slot"] for e in profile.note_mappings.values() if e["type"] == "slot"}
        assert slots == set(range(8))  # all 8 performance slots are mapped


def test_missing_profile_raises_clear_error():
    with pytest.raises(ProfileError, match="not found"):
        ControllerProfile.load(PROFILES_DIR / "does_not_exist.json")


def test_invalid_command_raises_clear_error():
    with pytest.raises(ProfileError, match="command"):
        ControllerProfile.from_dict(
            {"note_mappings": {"36": {"type": "command", "command": "bogus"}}}
        )


def test_invalid_slot_raises_clear_error():
    with pytest.raises(ProfileError, match="slot"):
        ControllerProfile.from_dict({"note_mappings": {"36": {"type": "slot", "slot": 9}}})
