"""Transport (FA/FB/FC/F8) と playhead の挙動。"""

from emiuet_session.core.frames import InputFrame
from emiuet_session.core.midi import MidiEventType
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.solo import SoloGesture
from emiuet_session.core.transport import AdvanceMode, TransportEvent, TransportState
from emiuet_session.fixtures import sample_compiled_timeline, sample_performance_model
from emiuet_session.runtime import EmiuetCore


def core():
    return EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=sample_compiled_timeline(24),
    )


def test_start_sets_running_and_resets_playhead():
    c = core()
    c.process(InputFrame(clock_pulses=10))  # ignored while stopped
    c.process(InputFrame(transport_event=TransportEvent.START))
    assert c.transport_state is TransportState.RUNNING
    assert c.ticks == 0


def test_clock_advances_only_while_running():
    c = core()
    c.process(InputFrame(clock_pulses=24))
    assert c.ticks == 0  # STOPPED -> ignored
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=24))
    assert c.ticks == 24  # RUNNING -> advances


def test_stop_clears_notes_but_keeps_transport_playhead():
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=30))
    c.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # something sounding
    out = c.process(InputFrame(transport_event=TransportEvent.STOP))
    assert c.transport_state is TransportState.STOPPED
    assert any(e.type is MidiEventType.NOTE_OFF for e in out.midi_events)
    assert c.active_notes() == ()
    # transport playhead is retained so FB Continue can resume.
    assert c.ticks == 30


def test_stop_with_reset_policy_views_head_without_destroying_playhead():
    # Default StopPolicy.RESET_TO_HEAD: the display/resolver shows the head while
    # stopped, but the transport playhead is preserved for Continue.
    c = core()  # sample timeline: Dm7 at tick 0, G7 at tick 24
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=30))  # in G7 (>=24)
    assert c.current_context().chord == "G7"
    c.process(InputFrame(transport_event=TransportEvent.STOP))
    assert c.current_context().chord == "Dm7"  # view shows head
    assert c.ticks == 30  # but transport playhead kept


def test_stop_then_continue_keeps_playhead_for_digitone_continue():
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=40))
    c.process(InputFrame(transport_event=TransportEvent.STOP))
    c.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert c.ticks == 40


def test_keep_position_stop_policy_views_current_position():
    from emiuet_session.core.transport import StopPolicy

    c = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=sample_compiled_timeline(24),
        stop_policy=StopPolicy.KEEP_POSITION,
    )
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=30))  # G7
    c.process(InputFrame(transport_event=TransportEvent.STOP))
    assert c.current_context().chord == "G7"  # KEEP_POSITION shows where it stopped
    assert c.ticks == 30


def test_continue_is_not_start():
    # Continue keeps position; Start resets it. They must differ.
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=50))
    c.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert c.ticks == 50  # not reset
    c.process(InputFrame(transport_event=TransportEvent.START))
    assert c.ticks == 0  # reset
