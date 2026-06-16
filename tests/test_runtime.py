"""Runtime: tempo-driven step timing and segment advance (spec test 13 + more)."""

from emiuet_session.core.frames import InputFrame, SegmentCommand
from emiuet_session.model.analysis import (
    HarmonicAnalysis,
    HarmonicStep,
    PitchCandidate,
    PitchRole,
)
from emiuet_session.model.build import build_performance_model
from emiuet_session.model.song import ChordSymbol, Meter, Section, Song
from emiuet_session.runtime import EmiuetCore


def _core_step(symbol, root, tones):
    cands = [
        PitchCandidate(pc, "d", PitchRole.CORE, weight=1.0 - 0.05 * i, stability=0.8)
        for i, pc in enumerate(tones)
    ]
    return HarmonicStep(
        chord_symbol=symbol,
        root_pc=root,
        quality="x",
        chord_tones=tuple(tones),
        local_pitch_collection=tuple(tones),
        scale_collection="S",
        scale_priority=1,
        candidates=cands,
    )


def two_step_segment_model(tempo=200.0):
    """One 4/4 bar with two 2-beat chords; at fast tempo they share one segment."""
    chords = [ChordSymbol("Dm7", 1, 0.0, 2.0), ChordSymbol("G7", 1, 2.0, 2.0)]
    song = Song("t", tempo, Meter(4, 4), [Section("A", chords)])
    analysis = HarmonicAnalysis(
        "t", [_core_step("Dm7", 2, [2, 5, 9, 0]), _core_step("G7", 7, [7, 11, 2, 5])]
    )
    return build_performance_model(song, analysis)


def test_two_chords_group_into_one_segment_with_two_steps():
    model = two_step_segment_model()
    assert model.segment_count() == 1
    assert len(model.segments[0].steps) == 2


def test_steps_auto_advance_by_tempo_inside_segment():
    core = EmiuetCore(two_step_segment_model(tempo=200.0))
    assert core.step_duration_ms() == 600.0  # 2 beats @ 200 BPM
    core.process(InputFrame(now_ms=0))
    assert core.step_index == 0
    core.process(InputFrame(now_ms=599))
    assert core.step_index == 0  # not yet
    core.process(InputFrame(now_ms=600))
    assert core.step_index == 1  # auto-advanced


def test_does_not_auto_advance_past_last_step():
    core = EmiuetCore(two_step_segment_model(tempo=200.0))
    core.process(InputFrame(now_ms=0))
    core.process(InputFrame(now_ms=10_000))  # way past
    assert core.step_index == 1  # last step of the segment, stays put
    assert core.segment_index == 0  # never crosses a manual boundary


def test_tempo_update_recalculates_step_timing():
    core = EmiuetCore(two_step_segment_model(tempo=200.0))
    assert core.step_duration_ms() == 600.0
    core.process(InputFrame(tempo_bpm=120.0))
    assert core.step_duration_ms() == 1000.0  # 2 beats @ 120 BPM


def test_auto_step_advance_does_not_retrigger_held_note():
    core = EmiuetCore(two_step_segment_model(tempo=200.0))
    core.process(InputFrame(now_ms=0, key_presses=(0,)))
    held = core.active_notes()
    out = core.process(InputFrame(now_ms=600))
    assert core.step_index == 1
    assert out.midi_events == []  # no retrigger
    assert core.active_notes() == held


def test_segment_advance_clamps_at_ends():
    from emiuet_session.fixtures import sample_performance_model

    core = EmiuetCore(sample_performance_model())
    core.process(InputFrame(segment_command=SegmentCommand.PREV))
    assert core.segment_index == 0  # cannot go below 0
    for _ in range(10):
        core.process(InputFrame(segment_command=SegmentCommand.NEXT))
    assert core.segment_index == core.model.segment_count() - 1  # clamps at end


def test_display_state_tracks_current_and_next_chord():
    from emiuet_session.fixtures import sample_performance_model

    core = EmiuetCore(sample_performance_model())
    out = core.process(InputFrame())
    assert out.display.current_chord == "Dm7"
    assert out.display.next_chord == "G7"
