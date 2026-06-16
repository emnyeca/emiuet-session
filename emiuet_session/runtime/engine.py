"""EmiuetCore -- the portable runtime engine.

    output = core.process(input_frame)

Responsibilities: hold the PerformanceModel; track current segment/step; advance
steps automatically by tempo inside a segment; turn 8 key presses into MIDI
notes through the current layout, register shift and approach modifiers; manage
note lifecycle safely; and produce a DisplayState.

Note-lifecycle rules (these are the ones tests guard):
- A held note keeps the MIDI note it was triggered with until its key is
  released -- layout changes and segment/step advances never retune or retrigger
  a sounding note.
- Register shift and approach offsets are baked in at trigger time only.
- Panic sends NoteOff for every active note. No path leaves a stuck note.

No GUI, MIDI library, or platform API is touched here.
"""

from __future__ import annotations

from ..core.approach import ApproachState
from ..core.display import DisplayState
from ..core.frames import InputFrame, OutputFrame, RegisterCommand, SegmentCommand
from ..core.midi import MidiEvent
from ..core.pitch import clamp_midi
from ..core.profile import PerformanceProfile
from ..core.register_shift import RegisterShift
from ..model.performance import Layout, PerformanceModel, Segment, Step

_PROFILE_LABELS = {
    PerformanceProfile.NORMAL: "NORM",
    PerformanceProfile.COLOR: "COLR",
    PerformanceProfile.OUTSIDE_UP: "OUT+",
    PerformanceProfile.OUTSIDE_DOWN: "OUT-",
    PerformanceProfile.DOMINANT_MOTION: "DOM",
}


class EmiuetCore:
    def __init__(
        self,
        model: PerformanceModel,
        *,
        channel: int = 1,
        velocity: int = 100,
        tempo_bpm: float | None = None,
    ) -> None:
        self.model = model
        self.channel = channel
        self.velocity = velocity
        self.tempo_bpm = tempo_bpm if tempo_bpm is not None else model.default_tempo

        self.segment_index = 0
        self.step_index = 0
        self._step_elapsed_ms = 0.0
        self._last_now_ms: float | None = None

        self.register = RegisterShift()
        self.approach = ApproachState()
        self.profile = PerformanceProfile.NORMAL

        # slot index -> the MIDI note currently sounding for that slot.
        self._active: dict[int, int] = {}

    # ---- accessors -----------------------------------------------------

    def current_segment(self) -> Segment:
        return self.model.segments[self.segment_index]

    def current_step(self) -> Step:
        return self.current_segment().steps[self.step_index]

    def current_layout(self) -> Layout:
        return self.current_step().layout

    def active_notes(self) -> tuple[int, ...]:
        return tuple(sorted(self._active.values()))

    def step_duration_ms(self) -> float:
        ms_per_beat = 60000.0 / self.tempo_bpm
        return self.current_step().duration_beats * ms_per_beat

    # ---- main loop -----------------------------------------------------

    def process(self, frame: InputFrame) -> OutputFrame:
        events: list[MidiEvent] = []

        if frame.tempo_bpm is not None and frame.tempo_bpm > 0:
            self.tempo_bpm = frame.tempo_bpm

        self._apply_profile(frame)
        self._apply_register(frame)
        self._apply_approach(frame)

        if frame.panic:
            events.extend(self._panic())

        self._advance_time(frame)
        self._apply_segment_command(frame)

        events.extend(self._release_keys(frame.key_releases))
        events.extend(self._press_keys(frame.key_presses))

        return OutputFrame(midi_events=events, display=self._display())

    # ---- handlers ------------------------------------------------------

    def _apply_profile(self, frame: InputFrame) -> None:
        cmd = frame.profile_command
        if cmd is None:
            return
        if cmd == "cycle":
            self.profile = self.profile.next()
        elif isinstance(cmd, PerformanceProfile):
            self.profile = cmd

    def _apply_register(self, frame: InputFrame) -> None:
        if frame.register_mode is not None:
            self.register.set_mode(frame.register_mode, frame.register_custom_step)
        cmd = frame.register_command
        if cmd == RegisterCommand.UP:
            self.register.up()
        elif cmd == RegisterCommand.DOWN:
            self.register.down()
        elif cmd == RegisterCommand.RESET:
            self.register.reset()

    def _apply_approach(self, frame: InputFrame) -> None:
        if frame.approach_press is not None:
            self.approach.press(frame.approach_press)
        if frame.approach_release is not None:
            self.approach.release(frame.approach_release)

    def _advance_time(self, frame: InputFrame) -> None:
        """Auto-advance steps inside the current segment by elapsed time.

        Held notes are untouched; only the active layout for *future* presses
        changes. We never walk past the last step of a segment automatically --
        that boundary is crossed only by a manual Next.
        """
        if self._last_now_ms is None:
            self._last_now_ms = frame.now_ms
        dt = max(0.0, frame.now_ms - self._last_now_ms)
        self._last_now_ms = frame.now_ms

        self._step_elapsed_ms += dt
        steps = self.current_segment().steps
        while self.step_index < len(steps) - 1 and self._step_elapsed_ms >= self.step_duration_ms():
            self._step_elapsed_ms -= self.step_duration_ms()
            self.step_index += 1

    def _apply_segment_command(self, frame: InputFrame) -> None:
        cmd = frame.segment_command
        if cmd == SegmentCommand.NEXT and self.segment_index < self.model.segment_count() - 1:
            self.segment_index += 1
            self.step_index = 0
            self._step_elapsed_ms = 0.0
        elif cmd == SegmentCommand.PREV and self.segment_index > 0:
            self.segment_index -= 1
            self.step_index = 0
            self._step_elapsed_ms = 0.0

    def _release_keys(self, slots: tuple[int, ...]) -> list[MidiEvent]:
        events: list[MidiEvent] = []
        for slot in slots:
            note = self._active.pop(slot, None)
            if note is not None:
                events.append(MidiEvent.note_off(note, self.channel))
        return events

    def _press_keys(self, slots: tuple[int, ...]) -> list[MidiEvent]:
        events: list[MidiEvent] = []
        layout = self.current_layout()
        for slot in slots:
            if not 0 <= slot < 8:
                continue
            base = layout.slots[slot].preferred_midi
            offset = self.register.offset_semitones + self.approach.offset_for_trigger()
            note = clamp_midi(base + offset)
            # Re-press without release: stop the old note before retriggering.
            old = self._active.get(slot)
            if old is not None:
                events.append(MidiEvent.note_off(old, self.channel))
            events.append(MidiEvent.note_on(note, self.velocity, self.channel))
            self._active[slot] = note
        return events

    def _panic(self) -> list[MidiEvent]:
        events = [MidiEvent.note_off(note, self.channel) for note in self._active.values()]
        self._active.clear()
        return events

    # ---- display -------------------------------------------------------

    def _display(self) -> DisplayState:
        step = self.current_step()
        segment = self.current_segment()
        return DisplayState(
            current_chord=step.chord,
            next_chord=step.next_chord,
            register_label=self.register.label(),
            profile_label=_PROFILE_LABELS[self.profile],
            slot_labels=self.current_layout().note_labels(),
            segment_index=self.segment_index,
            segment_count=self.model.segment_count(),
            step_index=self.step_index,
            step_count=len(segment.steps),
            selected_collection=step.scale_collection,
            scale_priority=step.scale_priority,
            retry_level=step.retry_level,
            lpc=step.lpc,
            active_notes=self.active_notes(),
        )
