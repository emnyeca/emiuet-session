"""Contrast MOD: effective context の切替（Harmonic Ahead との共存含む）。"""

from pathlib import Path

from emiuet_session.core.frames import InputFrame
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.solo import SoloGesture
from emiuet_session.core.timeline_io import load_compiled_timeline, parse_compiled_timeline
from emiuet_session.core.transport import AdvanceMode, TransportEvent
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore

FIXTURE = Path(__file__).parent / "fixtures" / "dm7_g7_cmaj7_a7_contrast_timeline.json"


def started_core(timeline=None):
    c = EmiuetCore(
        sample_performance_model(),
        mode=PerformanceMode.SOLO,
        advance_mode=AdvanceMode.AUTO_FOLLOW,
        timeline=timeline or load_compiled_timeline(FIXTURE),
    )
    c.process(InputFrame(transport_event=TransportEvent.START))  # at Dm7 (tick 0)
    return c


def test_default_effective_context_is_progression():
    c = started_core()
    assert c.effective_context().role == "progression"
    assert c.effective_context().scale_collection == "Dorian"


def test_contrast_mod_switches_effective_context():
    c = started_core()
    c.process(InputFrame(contrast_mod_press=True))
    aim = c.effective_context()
    assert aim.role == "contrast"
    assert aim.scale_collection == "Half-Whole Diminished"
    assert c.current_context().chord == "Dm7"  # NOW unchanged
    c.process(InputFrame(contrast_mod_release=True))
    assert c.effective_context().role == "progression"


def test_resolver_uses_contrast_lpc_when_modded():
    c = started_core()
    # Dm7 contrast = D Half-Whole Diminished: D Eb F F# G# A B C.
    contrast_lpc = set(c.timeline.steps[0].context_for("contrast").lpc)
    c.process(InputFrame(contrast_mod_press=True))
    c.process(InputFrame(solo_gesture=SoloGesture.REPEAT))  # C4 (60), a core tone
    out = c.process(InputFrame(solo_gesture=SoloGesture.LPC_UP))
    note = [e.note for e in out.midi_events if e.velocity > 0][0]
    assert note % 12 in contrast_lpc


def test_harmonic_ahead_and_contrast_combine():
    # NOW Dm7, Ahead -> G7, Contrast ON => G7 contrast (G7 HW).
    c = started_core()
    c.process(InputFrame(harmonic_ahead=True))  # AIM step = G7
    c.process(InputFrame(contrast_mod_press=True))
    aim = c.effective_context()
    assert c.current_context().chord == "Dm7"  # NOW
    assert aim.display == "G7 HW"  # ahead step, contrast context
    assert aim.scale_collection == "Half-Whole Diminished"


def test_contrast_falls_back_to_progression_when_absent():
    # Build a timeline whose step has no contrast context.
    data = {
        "schema": "emnyeca.emiuet_session.compiled_timeline",
        "schema_version": 2,
        "timeline_basis": "digitone_step",
        "steps": [
            {
                "id": "s0", "start_tick": 0, "end_tick": 24, "chord": "C",
                "default_context_role": "progression", "mod_context_role": "contrast",
                "contexts": {
                    "progression": {
                        "role": "progression", "display": "Cmaj7", "scale_name": "Ionian",
                        "scale_root": "C", "resolver_core": ["C", "E", "G", "B"],
                        "lpc": ["C", "D", "E", "F", "G", "A", "B"],
                    }
                },
            }
        ],
    }
    c = started_core(timeline=parse_compiled_timeline(data))
    c.process(InputFrame(contrast_mod_press=True))
    # No contrast context -> resolver falls back to progression.
    assert c.effective_context().role == "progression"


def test_transport_start_clears_contrast_mod():
    c = started_core()
    c.process(InputFrame(contrast_mod_press=True))
    c.process(InputFrame(transport_event=TransportEvent.START))
    assert not c.contrast_mod
    assert c.effective_context().role == "progression"


def test_transport_stop_clears_contrast_mod():
    c = started_core()
    c.process(InputFrame(contrast_mod_press=True))
    c.process(InputFrame(transport_event=TransportEvent.STOP))
    assert not c.contrast_mod


def test_transport_continue_clears_contrast_mod():
    c = started_core()
    c.process(InputFrame(contrast_mod_press=True))
    c.process(InputFrame(transport_event=TransportEvent.CONTINUE))
    assert not c.contrast_mod


def test_panic_clears_contrast_mod():
    c = started_core()
    c.process(InputFrame(contrast_mod_press=True))
    c.process(InputFrame(panic=True))
    assert not c.contrast_mod
    assert c.effective_context().role == "progression"


def test_manual_mode_has_no_contrast():
    c = EmiuetCore(sample_performance_model(), mode=PerformanceMode.SOLO)  # manual
    c.process(InputFrame(contrast_mod_press=True))
    # No timeline -> effective context is the model's; contrast has no effect/crash.
    assert c.effective_context().chord  # non-empty, no error
