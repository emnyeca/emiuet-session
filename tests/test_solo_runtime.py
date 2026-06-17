"""Solo Mode の runtime 挙動（mono last-press-wins / pending / wrap / lifecycle）。"""

from emiuet_session.core.frames import InputFrame, SegmentCommand
from emiuet_session.core.midi import MidiEventType
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.solo import SoloGesture
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore


def solo_core():
    return EmiuetCore(sample_performance_model(), mode=PerformanceMode.SOLO)


def _types(out):
    return [e.type for e in out.midi_events]


def _notes(out, kind):
    return [e.note for e in out.midi_events if e.type is kind]


def test_solo_gesture_emits_note_on():
    core = solo_core()
    out = core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))
    assert _notes(out, MidiEventType.NOTE_ON) == [60]  # initial repeat -> C4
    assert core.active_notes() == (60,)


def test_new_gesture_stops_previous_then_sounds_new():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 (60)
    out = core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # -> D4 (62)
    assert _types(out) == [MidiEventType.NOTE_OFF, MidiEventType.NOTE_ON]
    assert _notes(out, MidiEventType.NOTE_OFF) == [60]
    assert _notes(out, MidiEventType.NOTE_ON) == [62]
    assert core.active_notes() == (62,)


def test_old_key_release_does_not_stop_current_note():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 via REPEAT
    core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # D4 via CORE_UP (current)
    # Releasing the OLD key (REPEAT) must not stop the note made by CORE_UP.
    out = core.process(InputFrame(solo_gesture_release=SoloGesture.REPEAT))
    assert out.midi_events == []
    assert core.active_notes() == (62,)
    # Releasing the current key (CORE_UP) stops it.
    out2 = core.process(InputFrame(solo_gesture_release=SoloGesture.CORE_UP))
    assert _notes(out2, MidiEventType.NOTE_OFF) == [62]
    assert core.active_notes() == ()


def test_panic_stops_active_solo_note():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))
    out = core.process(InputFrame(panic=True))
    assert len(_notes(out, MidiEventType.NOTE_OFF)) == 1
    assert core.active_notes() == ()


def test_pending_octave_then_gesture_then_reset():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 (60)
    core.process(InputFrame(pending_octave_up=True))
    assert core.pending.octave_shift == 1
    out = core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # D + 12 = 74
    assert _notes(out, MidiEventType.NOTE_ON) == [74]
    assert core.pending.octave_shift == 0  # reset after use


def test_pending_skip_stacks_and_resets():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 (60)
    core.process(InputFrame(pending_skip=True))
    core.process(InputFrame(pending_skip=True))
    assert core.pending.skip_count == 2
    out = core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # 3rd nearest core -> A (69)
    assert _notes(out, MidiEventType.NOTE_ON) == [69]
    assert core.pending.skip_count == 0


def test_clear_pending_reset_cursor():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # sets cursor
    core.process(InputFrame(pending_skip=True, pending_octave_up=True))
    core.process(InputFrame(clear_pending_reset_cursor=True))
    assert core.pending.skip_count == 0 and core.pending.octave_shift == 0
    assert core.cursor.last_output_note is None


def test_next_segment_wraps_in_solo_mode():
    core = solo_core()
    last = core.model.segment_count() - 1
    core.process(InputFrame(segment_command=SegmentCommand.PREV))
    assert core.segment_index == last
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert core.segment_index == 0


def test_gesture_after_segment_change_uses_new_lpc():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # Dm7 core -> C4 (60)
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))  # -> G7
    # G7 core = G B D F; LPC_UP from 60 should use G7's LPC, not Dm7's.
    out = core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))
    note = _notes(out, MidiEventType.NOTE_ON)[0]
    assert note % 12 in {pc % 12 for pc in core.current_core_pcs()}


def test_restart_head_returns_to_first_segment():
    core = solo_core()
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert core.segment_index == 2
    core.process(InputFrame(restart_head=True))
    assert core.segment_index == 0 and core.step_index == 0


def test_held_solo_note_survives_segment_change():
    core = solo_core()
    core.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # sounds a note
    held = core.active_notes()
    out = core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert out.midi_events == []  # not retriggered
    assert core.active_notes() == held


def test_chord_mode_still_uses_slots():
    core = EmiuetCore(sample_performance_model())  # default ChordMode
    out = core.process(InputFrame(key_presses=(0,)))
    assert _notes(out, MidiEventType.NOTE_ON) == [60]  # slot 0 of Dm7 layout
