"""Auto Follow: Digitone-step timeline 同期と Harmonic Ahead。"""

from emiuet_session.core.frames import InputFrame
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.solo import SoloGesture
from emiuet_session.core.timeline import (
    ChordContext,
    CompiledHarmonicStep,
    CompiledTimeline,
    TimelineBasis,
)
from emiuet_session.core.transport import AdvanceMode, TransportEvent
from emiuet_session.fixtures import sample_compiled_timeline, sample_performance_model
from emiuet_session.runtime import EmiuetCore


def _dm7_g7_digitone_timeline(ticks_per_step=24):
    """Original Tempo120 4/4 |Dm7|G7| compiled as 2 Digitone steps (tick-based)."""
    dm7 = ChordContext("Dm7", (2, 5, 9, 0), (2, 4, 5, 7, 9, 11, 0))
    g7 = ChordContext("G7", (7, 11, 2, 5), (7, 9, 11, 0, 2, 4, 5))
    steps = [
        CompiledHarmonicStep("s0", 0, ticks_per_step, dm7, 0, "Dm7"),
        CompiledHarmonicStep("s1", ticks_per_step, 2 * ticks_per_step, g7, 1, "G7"),
    ]
    return CompiledTimeline(TimelineBasis.DIGITONE_STEP, steps, original_tempo=120.0, digitone_tempo=60.0)


def _auto_core(timeline):
    return EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=timeline,
    )


def test_auto_follow_uses_digitone_step_timeline():
    c = _auto_core(sample_compiled_timeline())
    assert c.timeline.basis is TimelineBasis.DIGITONE_STEP
    c.process(InputFrame(transport_event=TransportEvent.START))
    assert c.current_context().chord == "Dm7"


def test_chord_switches_at_compiled_step_boundary_not_original_bar():
    # At 120 BPM 4/4, an original bar would be 96 clocks; the compiled step is 24.
    tl = _dm7_g7_digitone_timeline(ticks_per_step=24)
    c = _auto_core(tl)
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=23))
    assert c.current_context().chord == "Dm7"  # still in step 0
    c.process(InputFrame(clock_pulses=1))  # tick 24 = compiled boundary
    assert c.current_context().chord == "G7"  # switched at compiled step, not bar


def test_does_not_advance_on_original_tempo_alone():
    # Without clock pulses, wall-time (now_ms) must not move the harmonic cursor.
    tl = _dm7_g7_digitone_timeline()
    c = _auto_core(tl)
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(now_ms=100_000))  # lots of wall time, no clock
    assert c.current_context().chord == "Dm7"
    assert c.ticks == 0


def test_unknown_basis_warns():
    dm7 = ChordContext("Dm7", (2, 5, 9, 0), (2, 4, 5, 7, 9, 11, 0))
    tl = CompiledTimeline(TimelineBasis.ORIGINAL_SONG, [CompiledHarmonicStep("s0", 0, 24, dm7)])
    c = _auto_core(tl)
    out = c.process(InputFrame())
    assert "timeline_basis" in out.display.warning


def test_missing_timeline_warns():
    c = EmiuetCore(
        sample_performance_model(), mode=PerformanceMode.SOLO, advance_mode=AdvanceMode.AUTO_FOLLOW
    )
    out = c.process(InputFrame())
    assert out.display.warning  # non-empty warning


# --- Harmonic Ahead ------------------------------------------------------


def _started_core():
    c = _auto_core(sample_compiled_timeline(24))  # Dm7 G7 Cmaj7 A7alt
    c.process(InputFrame(transport_event=TransportEvent.START))
    return c


def test_harmonic_ahead_targets_next_distinct_chord():
    c = _started_core()
    c.process(InputFrame(harmonic_ahead=True))
    assert c.harmonic_ahead.active
    assert c.effective_context().chord == "G7"  # next distinct chord
    assert c.current_context().chord == "Dm7"  # NOW unchanged


def test_ahead_holds_through_multiple_notes():
    c = _started_core()
    c.process(InputFrame(harmonic_ahead=True))
    c.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))
    c.process(InputFrame(solo_gesture=SoloGesture.LPC_UP))
    assert c.harmonic_ahead.active
    assert c.effective_context().chord == "G7"


def test_ahead_repress_does_not_advance_two_ahead():
    c = _started_core()
    c.process(InputFrame(harmonic_ahead=True))
    target = c.harmonic_ahead.target_step_id
    c.process(InputFrame(harmonic_ahead=True))  # ignored
    assert c.harmonic_ahead.target_step_id == target


def test_ahead_auto_clears_on_arrival():
    c = _started_core()
    c.process(InputFrame(harmonic_ahead=True))
    c.process(InputFrame(clock_pulses=24))  # arrive at G7
    assert not c.harmonic_ahead.active
    assert c.current_context().chord == "G7"


def test_ahead_clears_on_stop_start_panic_and_clear():
    for trigger in (
        InputFrame(transport_event=TransportEvent.STOP),
        InputFrame(transport_event=TransportEvent.START),
        InputFrame(panic=True),
        InputFrame(clear_ahead_pending=True),
    ):
        c = _started_core()
        c.process(InputFrame(harmonic_ahead=True))
        assert c.harmonic_ahead.active
        c.process(trigger)
        assert not c.harmonic_ahead.active


def test_continue_clears_ahead_but_keeps_playhead():
    c = _started_core()
    c.process(InputFrame(clock_pulses=10))
    c.process(InputFrame(harmonic_ahead=True))
    c.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert not c.harmonic_ahead.active
    assert c.ticks == 10  # Continue keeps the playhead


def test_resolver_uses_current_context_when_not_ahead():
    c = _started_core()
    # No ahead: CORE_UP from C4 uses Dm7 core (D).
    out = c.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))
    note = [e.note for e in out.midi_events if e.velocity > 0][0]
    assert note % 12 in {2, 5, 9, 0}  # Dm7 core


def test_resolver_uses_ahead_target_when_ahead():
    c = _started_core()
    c.process(InputFrame(harmonic_ahead=True))  # AIM G7
    out = c.process(InputFrame(solo_gesture=SoloGesture.CORE_DOWN))
    note = [e.note for e in out.midi_events if e.velocity > 0][0]
    assert note % 12 in {7, 11, 2, 5}  # G7 core
