"""Input/Output frames -- the single boundary between adapters and the engine.

The engine is driven one frame at a time::

    output = core.process(input_frame)

``InputFrame`` carries discrete commands collected since the last frame plus the
current time. The engine keeps held-key state internally, so adapters only need
to report press/release edges. ``OutputFrame`` carries the abstract MIDI events
to emit and a ``DisplayState`` snapshot for the OLED/GUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .approach import ApproachDirection
from .display import DisplayState
from .midi import MidiEvent
from .profile import PerformanceProfile
from .register_shift import RegisterShiftMode
from .solo import SoloGesture
from .transport import TransportEvent


class SegmentCommand:
    NEXT = "next"
    PREV = "prev"


class RegisterCommand:
    UP = "up"
    DOWN = "down"
    RESET = "reset"


@dataclass
class InputFrame:
    """Commands and time delta for one engine tick."""

    now_ms: float = 0.0

    # Performance keys (slot indices 0..7), as edges since the last frame.
    key_presses: tuple[int, ...] = ()
    key_releases: tuple[int, ...] = ()

    # Register shift.
    register_command: str | None = None  # RegisterCommand.*
    register_mode: RegisterShiftMode | None = None
    register_custom_step: int | None = None

    # Approach modifiers (edges).
    approach_press: ApproachDirection | None = None
    approach_release: ApproachDirection | None = None

    # Navigation.
    segment_command: str | None = None  # SegmentCommand.*

    # Tempo / profile.
    tempo_bpm: float | None = None
    profile_command: PerformanceProfile | str | None = None  # profile, or "cycle"

    # Solo Mode (relative melodic resolver). Gestures are edges, like keys.
    solo_gesture: SoloGesture | None = None
    solo_gesture_release: SoloGesture | None = None
    pending_octave_up: bool = False
    pending_octave_down: bool = False
    pending_skip: bool = False
    clear_pending_reset_cursor: bool = False
    restart_head: bool = False

    # Transport / Auto Follow.
    transport_event: TransportEvent | None = None  # START / CONTINUE / STOP
    clock_pulses: int = 0  # number of F8 ticks to consume this frame

    # Harmonic Ahead.
    harmonic_ahead: bool = False  # arm "ahead" to the next distinct chord
    experimental_previous_context: bool = False  # arm to the previous distinct chord
    clear_ahead_pending: bool = False  # clear Harmonic Ahead + pending modifiers
    resync: bool = False  # clear ahead + pending + reset the solo cursor

    # Contrast MOD (hold): view the current/ahead step through its contrast context.
    contrast_mod_press: bool = False
    contrast_mod_release: bool = False

    # Safety.
    panic: bool = False


@dataclass
class OutputFrame:
    midi_events: list[MidiEvent] = field(default_factory=list)
    display: DisplayState | None = None
