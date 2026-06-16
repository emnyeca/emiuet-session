"""Note lifecycle and panic safety (spec tests 8 and 14)."""

from emiuet_session.core.frames import InputFrame, SegmentCommand
from emiuet_session.core.midi import MidiEventType
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore


def _notes(out, kind):
    return [e.note for e in out.midi_events if e.type is kind]


def test_press_then_release_emits_matching_on_off():
    core = EmiuetCore(sample_performance_model())
    note = core.current_layout().slots[0].preferred_midi
    on = core.process(InputFrame(key_presses=(0,)))
    assert _notes(on, MidiEventType.NOTE_ON) == [note]
    off = core.process(InputFrame(key_releases=(0,)))
    assert _notes(off, MidiEventType.NOTE_OFF) == [note]
    assert core.active_notes() == ()


def test_held_note_survives_segment_change_with_original_pitch():
    core = EmiuetCore(sample_performance_model())
    held = core.current_layout().slots[0].preferred_midi

    core.process(InputFrame(key_presses=(0,)))
    # Advance segment -- layout changes, but the held note must NOT retrigger.
    advanced = core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert advanced.midi_events == []
    assert core.active_notes() == (held,)

    # Releasing now must turn off the ORIGINAL note, not the new layout's slot 0.
    new_slot0 = core.current_layout().slots[0].preferred_midi
    assert new_slot0 != held  # sanity: layout really changed
    off = core.process(InputFrame(key_releases=(0,)))
    assert _notes(off, MidiEventType.NOTE_OFF) == [held]
    assert core.active_notes() == ()


def test_no_stuck_note_after_prev_next_cycle():
    core = EmiuetCore(sample_performance_model())
    core.process(InputFrame(key_presses=(0, 2, 4)))
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    core.process(InputFrame(segment_command=SegmentCommand.PREV))
    out = core.process(InputFrame(key_releases=(0, 2, 4)))
    assert len(_notes(out, MidiEventType.NOTE_OFF)) == 3
    assert core.active_notes() == ()


def test_repress_without_release_retriggers():
    core = EmiuetCore(sample_performance_model())
    core.process(InputFrame(key_presses=(0,)))
    out = core.process(InputFrame(key_presses=(0,)))
    types = [e.type for e in out.midi_events]
    assert types == [MidiEventType.NOTE_OFF, MidiEventType.NOTE_ON]


def test_octave_nudged_slot_has_normal_lifecycle():
    # A slot whose note was octave-nudged by voicing de-dup behaves like any
    # other: it triggers its (deduped) preferred note, survives a segment change,
    # and releases the same note. Nudging is baked into the layout, not runtime.
    core = EmiuetCore(sample_performance_model())
    layout = core.current_layout()
    nudged = [s.index for s in layout.slots if s.index % 2 == 1 and s.preferred_midi >= 70]
    assert nudged, "expected at least one octave-nudged colour slot in Dm7"
    slot = nudged[0]
    expected = layout.slots[slot].preferred_midi

    on = core.process(InputFrame(key_presses=(slot,)))
    assert _notes(on, MidiEventType.NOTE_ON) == [expected]
    core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert core.active_notes() == (expected,)
    off = core.process(InputFrame(key_releases=(slot,)))
    assert _notes(off, MidiEventType.NOTE_OFF) == [expected]
    assert core.active_notes() == ()


def test_panic_turns_off_all_active_notes():
    core = EmiuetCore(sample_performance_model())
    core.process(InputFrame(key_presses=(0, 1, 2, 3)))
    out = core.process(InputFrame(panic=True))
    assert len(_notes(out, MidiEventType.NOTE_OFF)) == 4
    assert core.active_notes() == ()
