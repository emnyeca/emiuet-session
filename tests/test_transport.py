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


def test_stop_clears_and_resets_to_head():
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=30))
    c.process(InputFrame(solo_gesture=SoloGesture.CORE_UP))  # something sounding
    out = c.process(InputFrame(transport_event=TransportEvent.STOP))
    assert c.transport_state is TransportState.STOPPED
    assert c.ticks == 0  # StopPolicy.RESET_TO_HEAD
    assert any(e.type is MidiEventType.NOTE_OFF for e in out.midi_events)
    assert c.active_notes() == ()


def test_continue_does_not_reset_playhead():
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=30))
    c.process(InputFrame(transport_event=TransportEvent.STOP))  # resets to head (ticks 0)
    # Move playhead manually to simulate a mid-pattern position before Continue.
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=40))
    pos = c.ticks
    c.process(InputFrame(transport_event=TransportEvent.STOP))  # resets to head again
    # Now use KEEP_POSITION semantics check on Continue specifically:
    c2 = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=sample_compiled_timeline(24),
    )
    c2.process(InputFrame(transport_event=TransportEvent.START))
    c2.process(InputFrame(clock_pulses=40))
    before = c2.ticks
    c2.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert c2.transport_state is TransportState.RUNNING
    assert c2.ticks == before  # Continue must NOT reset the playhead
    assert pos == 40


def test_continue_is_not_start():
    # Continue keeps position; Start resets it. They must differ.
    c = core()
    c.process(InputFrame(transport_event=TransportEvent.START))
    c.process(InputFrame(clock_pulses=50))
    c.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert c.ticks == 50  # not reset
    c.process(InputFrame(transport_event=TransportEvent.START))
    assert c.ticks == 0  # reset
