"""Register shift behaviour (spec test 6)."""

from emiuet_session.core.frames import InputFrame, RegisterCommand
from emiuet_session.core.midi import MidiEventType
from emiuet_session.core.register_shift import RegisterShift, RegisterShiftMode
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore


def test_octave_mode_steps_by_twelve():
    reg = RegisterShift(mode=RegisterShiftMode.OCTAVE)
    reg.up()
    assert reg.offset_semitones == 12
    reg.up()
    assert reg.offset_semitones == 24
    reg.reset()
    assert reg.offset_semitones == 0


def test_fifth_slide_steps_by_seven():
    reg = RegisterShift(mode=RegisterShiftMode.FIFTH_SLIDE)
    reg.up()
    assert reg.offset_semitones == 7
    reg.down()
    reg.down()
    assert reg.offset_semitones == -7


def test_custom_semitone_mode():
    reg = RegisterShift()
    reg.set_mode(RegisterShiftMode.CUSTOM_SEMITONE, custom_step=3)
    reg.up()
    assert reg.offset_semitones == 3


def test_register_shift_applies_to_triggered_note():
    core = EmiuetCore(sample_performance_model())
    base = core.current_layout().slots[0].preferred_midi

    on0 = _note_on(core.process(InputFrame(key_presses=(0,))))
    assert on0 == base
    core.process(InputFrame(key_releases=(0,)))

    core.process(InputFrame(register_command=RegisterCommand.UP))  # OCTAVE default
    on1 = _note_on(core.process(InputFrame(key_presses=(0,))))
    assert on1 == base + 12


def _note_on(out):
    notes = [e.note for e in out.midi_events if e.type is MidiEventType.NOTE_ON]
    assert len(notes) == 1
    return notes[0]
