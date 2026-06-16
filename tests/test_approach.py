"""Approach +/- modifier behaviour (spec test 7)."""

from emiuet_session.core.approach import ApproachDirection, ApproachPolicy, ApproachState
from emiuet_session.core.frames import InputFrame
from emiuet_session.core.midi import MidiEventType
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore


def _note_on(out):
    notes = [e.note for e in out.midi_events if e.type is MidiEventType.NOTE_ON]
    assert len(notes) == 1
    return notes[0]


def test_momentary_plus_raises_next_trigger():
    core = EmiuetCore(sample_performance_model())
    base = core.current_layout().slots[2].preferred_midi
    core.process(InputFrame(approach_press=ApproachDirection.PLUS))
    assert _note_on(core.process(InputFrame(key_presses=(2,)))) == base + 1


def test_momentary_minus_lowers_trigger():
    core = EmiuetCore(sample_performance_model())
    base = core.current_layout().slots[2].preferred_midi
    core.process(InputFrame(approach_press=ApproachDirection.MINUS))
    assert _note_on(core.process(InputFrame(key_presses=(2,)))) == base - 1


def test_momentary_clears_on_release():
    core = EmiuetCore(sample_performance_model())
    base = core.current_layout().slots[2].preferred_midi
    core.process(InputFrame(approach_press=ApproachDirection.PLUS))
    core.process(InputFrame(approach_release=ApproachDirection.PLUS))
    core.process(InputFrame(key_releases=(2,)))  # ensure slot free
    assert _note_on(core.process(InputFrame(key_presses=(2,)))) == base


def test_next_note_only_consumes_after_one_trigger():
    state = ApproachState(policy=ApproachPolicy.NEXT_NOTE_ONLY)
    state.press(ApproachDirection.PLUS)
    assert state.offset_for_trigger() == 1
    assert state.offset_for_trigger() == 0  # consumed
