"""Solo Mode の controller profile / MIDI mapping テスト。"""

from apps.desktop_debug.midi_input import (
    PROFILES_DIR,
    ControllerProfile,
    MidiInputMapper,
    MidiMessage,
)
from emiuet_session.core.frames import SegmentCommand
from emiuet_session.core.solo import SoloGesture

SOLO_PROFILE = ControllerProfile.load(PROFILES_DIR / "ccp16_solo.json")
CH = (SOLO_PROFILE.midi_channel or 1) - 1  # 0-based channel for messages


def mapper():
    return MidiInputMapper(SOLO_PROFILE)


def on(note):
    return MidiMessage("note_on", channel=CH, note=note, velocity=127)


def test_solo_profile_loads():
    assert SOLO_PROFILE.name == "CCP16BK Solo Mode profile"
    assert SOLO_PROFILE.midi_channel == 10


def test_note_36_maps_to_repeat_gesture():
    frame = mapper().map(on(36)).frame
    assert frame.solo_gesture is SoloGesture.REPEAT


def test_note_40_maps_to_resolve_gesture():
    frame = mapper().map(on(40)).frame
    assert frame.solo_gesture is SoloGesture.RESOLVE


def test_note_off_maps_to_gesture_release():
    frame = mapper().map(MidiMessage("note_off", channel=CH, note=41)).frame
    assert frame.solo_gesture_release is SoloGesture.CORE_UP


def test_note_45_maps_to_next_segment():
    frame = mapper().map(on(45)).frame
    assert frame.segment_command == SegmentCommand.NEXT


def test_note_46_maps_to_pending_skip():
    frame = mapper().map(on(46)).frame
    assert frame.pending_skip is True


def test_note_48_49_map_to_pending_octave():
    down = mapper().map(on(48)).frame
    up = mapper().map(on(49)).frame
    assert down.pending_octave_down is True
    assert up.pending_octave_up is True


def test_note_50_maps_to_restart_head():
    frame = mapper().map(on(50)).frame
    assert frame.restart_head is True


def test_chord_profile_still_uses_slots():
    chord = ControllerProfile.load(PROFILES_DIR / "ccp16.json")
    frame = MidiInputMapper(chord).map(MidiMessage("note_on", channel=9, note=36, velocity=127)).frame
    assert frame.key_presses == (0,)  # ChordMode slot mapping intact
    assert frame.solo_gesture is None
