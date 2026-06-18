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
from ..core.mode import PerformanceMode
from ..core.pitch import clamp_midi, note_label_octave
from ..core.profile import PerformanceProfile
from ..core.register_shift import RegisterShift
from ..core.solo import (
    PendingNoteModifiers,
    SoloCursor,
    SoloGesture,
    resolve_solo_note,
)
from ..core.timeline import (
    ChordContext,
    CompiledTimeline,
    HarmonicAhead,
    RuntimeTransposePolicy,
    TimelineAdvanceMode,
    TimelineBasis,
    validate_transpose_offset,
    transpose_context,
)
from ..core.transport import (
    AdvanceMode,
    StopPolicy,
    TransportEvent,
    TransportState,
)
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
        mode: PerformanceMode = PerformanceMode.CHORD,
        advance_mode: AdvanceMode = AdvanceMode.MANUAL,
        timeline: CompiledTimeline | None = None,
        stop_policy: StopPolicy = StopPolicy.RESET_TO_HEAD,
        channel: int = 1,
        velocity: int = 100,
        tempo_bpm: float | None = None,
        anchor_midi: int = 60,
        transpose_offset_semitones: int = 0,
        runtime_transpose_policy: RuntimeTransposePolicy | None = None,
    ) -> None:
        self.model = model
        self.mode = mode
        self.advance_mode = advance_mode
        self.timeline = timeline
        self.stop_policy = stop_policy
        self.channel = channel
        self.velocity = velocity
        self.anchor_midi = anchor_midi
        self.tempo_bpm = tempo_bpm if tempo_bpm is not None else model.default_tempo
        self.transpose_offset_semitones = validate_transpose_offset(transpose_offset_semitones)
        self.runtime_transpose_policy = (
            runtime_transpose_policy
            if runtime_transpose_policy is not None
            else self._default_transpose_policy_for_runtime(advance_mode, timeline)
        )

        self.segment_index = 0
        self.step_index = 0
        self._step_elapsed_ms = 0.0
        self._last_now_ms: float | None = None

        # Transport / playhead (Auto Follow).
        self.transport_state = TransportState.STOPPED
        self._ticks = 0  # MIDI clock playhead, advanced only while RUNNING
        self.harmonic_ahead = HarmonicAhead()
        self.contrast_mod = False  # hold: read the step through its contrast context

        self.register = RegisterShift()
        self.approach = ApproachState()
        self.profile = PerformanceProfile.NORMAL

        # ChordMode: slot index -> the MIDI note currently sounding for that slot.
        self._active: dict[int, int] = {}

        # SoloMode: relative-resolver state (mono, last-press-wins).
        self.cursor = SoloCursor()
        self.pending = PendingNoteModifiers()
        self._solo_note: int | None = None
        self._solo_gesture: SoloGesture | None = None
        self._solo_trace: str = ""

    @classmethod
    def from_session_timeline(
        cls,
        model: PerformanceModel,
        session_timeline,
        *,
        mode: PerformanceMode = PerformanceMode.CHORD,
        stop_policy: StopPolicy = StopPolicy.RESET_TO_HEAD,
        channel: int = 1,
        velocity: int = 100,
        tempo_bpm: float | None = None,
        anchor_midi: int = 60,
        transpose_offset_semitones: int = 0,
    ) -> "EmiuetCore":
        advance_mode = (
            AdvanceMode.MANUAL
            if session_timeline.advance_mode is TimelineAdvanceMode.MANUAL
            else AdvanceMode.AUTO_FOLLOW
        )
        return cls(
            model,
            mode=mode,
            advance_mode=advance_mode,
            timeline=session_timeline.compiled_timeline,
            stop_policy=stop_policy,
            channel=channel,
            velocity=velocity,
            tempo_bpm=tempo_bpm,
            anchor_midi=anchor_midi,
            transpose_offset_semitones=transpose_offset_semitones,
            runtime_transpose_policy=session_timeline.runtime_transpose_policy,
        )

    @staticmethod
    def _default_transpose_policy_for_runtime(
        advance_mode: AdvanceMode,
        timeline: CompiledTimeline | None,
    ) -> RuntimeTransposePolicy:
        if timeline is not None:
            if timeline.basis is TimelineBasis.DIGITONE_STEP:
                return RuntimeTransposePolicy.LOCKED
            return RuntimeTransposePolicy.ALLOWED
        if advance_mode is AdvanceMode.AUTO_FOLLOW:
            return RuntimeTransposePolicy.LOCKED
        return RuntimeTransposePolicy.ALLOWED

    # ---- accessors -----------------------------------------------------

    def current_segment(self) -> Segment:
        return self.model.segments[self.segment_index]

    def current_step(self) -> Step:
        return self.current_segment().steps[self.step_index]

    def current_layout(self) -> Layout:
        return self.current_step().layout

    def current_lpc(self) -> tuple[int, ...]:
        return self.current_context().lpc

    def current_core_pcs(self) -> tuple[int, ...]:
        return self.current_context().core_pcs

    @property
    def ticks(self) -> int:
        """Transport playhead. Kept across Stop so FB Continue can resume."""
        return self._ticks

    def _view_ticks(self) -> int:
        """Position the resolver/display reads. While STOPPED with a reset-to-head
        StopPolicy this shows the head (0) WITHOUT destroying the transport playhead
        (``_ticks``), so a following FB Continue still resumes from where it stopped."""
        if (
            self.transport_state is TransportState.STOPPED
            and self.stop_policy is StopPolicy.RESET_TO_HEAD
        ):
            return 0
        return self._ticks

    def current_compiled_step(self):
        """Compiled timeline step under the (view) playhead (Auto Follow only)."""
        if self.advance_mode is AdvanceMode.AUTO_FOLLOW and self.timeline is not None:
            return self.timeline.find_step_by_tick(self._view_ticks())
        return None

    def current_context(self) -> ChordContext:
        """NOW: the timeline-current chord's default (progression) context, or the
        PerformanceModel's current step (Manual)."""
        compiled = self.current_compiled_step()
        if compiled is not None:
            return self._apply_runtime_transpose(compiled.chord_context)
        step = self.current_step()
        return self._apply_runtime_transpose(
            ChordContext(step.chord, step.core_pcs, step.lpc, step.scale_collection)
        )

    def _resolved_step(self):
        """Which compiled step the resolver reads: the Harmonic Ahead target when
        armed, otherwise the current step. None in Manual mode."""
        if self.harmonic_ahead.active and self.harmonic_ahead.target_step is not None:
            return self.harmonic_ahead.target_step
        return self.current_compiled_step()

    def effective_context(self) -> ChordContext:
        """AIM: what the Solo resolver actually looks at.

        Harmonic Ahead chooses *which step*; Contrast MOD chooses *which context*
        of that step (contrast when held and available, else progression).
        """
        step = self._resolved_step()
        if step is None:
            return self.current_context()  # Manual: no contrast contexts
        if self.contrast_mod and step.has_context(step.mod_context_role):
            context = step.context_for(step.mod_context_role)
        else:
            context = step.context_for(step.default_context_role) or step.chord_context
        return self._apply_runtime_transpose(context)

    def _apply_runtime_transpose(self, context: ChordContext) -> ChordContext:
        if self.transpose_offset_semitones == 0:
            return context
        if self.runtime_transpose_policy is RuntimeTransposePolicy.LOCKED:
            return context
        return transpose_context(context, self.transpose_offset_semitones)

    def next_context_chord(self) -> str:
        compiled = self.current_compiled_step()
        if compiled is not None and self.timeline is not None:
            nxt = self.timeline.find_next_distinct_chord(compiled)
            return nxt.chord_context.chord if nxt else ""
        return self.current_step().next_chord

    def active_notes(self) -> tuple[int, ...]:
        notes = list(self._active.values())
        if self._solo_note is not None:
            notes.append(self._solo_note)
        return tuple(sorted(notes))

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
        self._apply_pending(frame)

        events.extend(self._apply_transport(frame))
        if self.transport_state is TransportState.RUNNING and frame.clock_pulses:
            self._ticks += frame.clock_pulses

        self._apply_ahead_commands(frame)

        if frame.restart_head:
            self._restart_head()

        if frame.panic:
            events.extend(self._panic())
            self.harmonic_ahead.clear()
            self.contrast_mod = False

        if self.advance_mode is AdvanceMode.MANUAL:
            self._advance_time(frame)
        self._apply_segment_command(frame)

        # Auto-clear Harmonic Ahead once the playhead reaches the target chord.
        self._update_ahead_arrival()

        if self.mode is PerformanceMode.SOLO:
            if frame.solo_gesture_release is not None:
                events.extend(self._solo_release(frame.solo_gesture_release))
            if frame.solo_gesture is not None:
                events.extend(self._solo_trigger_note(frame.solo_gesture))
        else:  # ChordMode (BassistMode is reserved/no-op for now)
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

    def _apply_pending(self, frame: InputFrame) -> None:
        """Pending modifiers affect only the next solo note, then reset on use."""
        if frame.pending_octave_up:
            self.pending.octave_shift += 1
        if frame.pending_octave_down:
            self.pending.octave_shift -= 1
        if frame.pending_skip:
            self.pending.skip_count += 1
        if frame.clear_pending_reset_cursor:
            self.pending.reset()
            self.cursor.reset()

    def _restart_head(self) -> None:
        """Jump to the head of the form (first segment/step). Cursor is kept."""
        self.segment_index = 0
        self.step_index = 0
        self._step_elapsed_ms = 0.0

    def _apply_transport(self, frame: InputFrame) -> list[MidiEvent]:
        """Handle FA/FB/FC. Continue is NOT treated as Start (playhead kept)."""
        event = frame.transport_event
        if event is TransportEvent.START:
            # 頭から再生: playhead reset、transient 全 clear、全音停止。
            self.transport_state = TransportState.RUNNING
            self._ticks = 0
            self.harmonic_ahead.clear()
            self.pending.reset()
            self.cursor.reset()
            self.contrast_mod = False
            return self._all_notes_off()
        if event is TransportEvent.CONTINUE:
            # 続き再生: playhead は reset しない。事故防止で transient は clear。
            self.transport_state = TransportState.RUNNING
            self.harmonic_ahead.clear()
            self.pending.reset()
            self.contrast_mod = False
            return []
        if event is TransportEvent.STOP:
            # 停止。notes/pending/ahead は clear するが、transport playhead は維持する
            # （FB Continue が続きから再開できるように）。head 表示は _view_ticks で行う。
            self.transport_state = TransportState.STOPPED
            self.harmonic_ahead.clear()
            self.pending.reset()
            self.contrast_mod = False
            return self._all_notes_off()
        return []

    def _apply_ahead_commands(self, frame: InputFrame) -> None:
        if frame.harmonic_ahead:
            self._arm_ahead(direction=+1)
        if frame.experimental_previous_context:
            self._arm_ahead(direction=-1)
        if frame.clear_ahead_pending:
            self.harmonic_ahead.clear()
            self.pending.reset()
        if frame.resync:
            self.harmonic_ahead.clear()
            self.pending.reset()
            self.cursor.reset()
        # Contrast MOD is a momentary hold (press engages, release releases).
        if frame.contrast_mod_press:
            self.contrast_mod = True
        if frame.contrast_mod_release:
            self.contrast_mod = False

    def _arm_ahead(self, direction: int) -> None:
        # AHEAD_ACTIVE 中は ignore（連打で 2 つ先へ進まない）。timeline が要る。
        if self.harmonic_ahead.active or self.timeline is None:
            return
        current = self.current_compiled_step()
        if current is None:
            return
        from ..core.timeline import AheadTargetPolicy

        if direction < 0:
            target = self.timeline.find_prev_distinct_chord(current)
        elif self.harmonic_ahead.policy is AheadTargetPolicy.NEXT_STEP:
            target = self.timeline.find_next_step(current)
        else:
            target = self.timeline.find_next_distinct_chord(current)
        if target is not None:
            self.harmonic_ahead.active = True
            self.harmonic_ahead.target_step = target

    def _update_ahead_arrival(self) -> None:
        if not self.harmonic_ahead.active:
            return
        current = self.current_compiled_step()
        if current is not None and current.id == self.harmonic_ahead.target_step_id:
            self.harmonic_ahead.clear()

    def _all_notes_off(self) -> list[MidiEvent]:
        return self._panic()

    def _apply_segment_command(self, frame: InputFrame) -> None:
        # Navigation wraps in both directions (SegmentNavigationPolicy: wrap).
        count = self.model.segment_count()
        cmd = frame.segment_command
        if cmd == SegmentCommand.NEXT:
            self.segment_index = (self.segment_index + 1) % count
        elif cmd == SegmentCommand.PREV:
            self.segment_index = (self.segment_index - 1) % count
        else:
            return
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

    def _solo_trigger_note(self, gesture: SoloGesture) -> list[MidiEvent]:
        """Resolve and sound the next solo note (mono, last-press-wins).

        The resolver looks at the *effective* context: the Harmonic Ahead target
        when armed, otherwise the current chord (timeline or model).
        """
        context = self.effective_context()
        resolution = resolve_solo_note(
            gesture,
            self.cursor.last_output_note,
            context.lpc,
            context.core_pcs,
            pending_octave_shift=self.pending.octave_shift,
            pending_skip_count=self.pending.skip_count,
            anchor_midi=self.anchor_midi,
            phrase_direction=self.cursor.phrase_direction,
        )
        events: list[MidiEvent] = []
        if self._solo_note is not None:  # stop the currently sounding solo note first
            events.append(MidiEvent.note_off(self._solo_note, self.channel))
        events.append(MidiEvent.note_on(resolution.note, self.velocity, self.channel))
        self._solo_note = resolution.note
        self._solo_gesture = gesture
        self.cursor.update(gesture, resolution.note)
        self._solo_trace = resolution.reason
        self.pending.reset()
        return events

    def _solo_release(self, gesture: SoloGesture) -> list[MidiEvent]:
        """Release only stops the note if this key produced the current note."""
        if self._solo_note is not None and self._solo_gesture is gesture:
            event = MidiEvent.note_off(self._solo_note, self.channel)
            self._solo_note = None
            self._solo_gesture = None
            return [event]
        return []

    def _panic(self) -> list[MidiEvent]:
        events = [MidiEvent.note_off(note, self.channel) for note in self._active.values()]
        self._active.clear()
        if self._solo_note is not None:
            events.append(MidiEvent.note_off(self._solo_note, self.channel))
            self._solo_note = None
            self._solo_gesture = None
        return events

    # ---- display -------------------------------------------------------

    def _display(self) -> DisplayState:
        step = self.current_step()
        segment = self.current_segment()
        layout = self.current_layout()
        now = self.current_context()
        aim = self.effective_context()
        aim_label = aim.display or aim.chord
        return DisplayState(
            current_chord=now.chord,
            next_chord=self.next_context_chord(),
            register_label=self.register.label(),
            profile_label=_PROFILE_LABELS[self.profile],
            slot_labels=layout.note_labels(),
            orientation=layout.orientation.value,
            core_line=tuple(note_label_octave(s.preferred_midi) for s in layout.core_slots()),
            color_line=tuple(note_label_octave(s.preferred_midi) for s in layout.color_slots()),
            segment_index=self.segment_index,
            segment_count=self.model.segment_count(),
            step_index=self.step_index,
            step_count=len(segment.steps),
            selected_collection=now.scale_collection,
            scale_priority=step.scale_priority,
            retry_level=step.retry_level,
            lpc=aim.lpc,
            active_notes=self.active_notes(),
            mode="Solo" if self.mode is PerformanceMode.SOLO else "Chord",
            core_pcs=aim.core_pcs,
            last_output_note=self.cursor.last_output_note,
            last_gesture=self.cursor.last_gesture.name if self.cursor.last_gesture else "",
            phrase_direction=self.cursor.phrase_direction.value,
            pending_octave=self.pending.octave_shift,
            pending_skip=self.pending.skip_count,
            resolver_trace=self._solo_trace,
            advance_mode=self.advance_mode.value,
            transport=self.transport_state.value,
            ticks=self._view_ticks(),
            now_chord=now.display or now.chord,
            aim_chord=aim_label,
            ahead_active=self.harmonic_ahead.active,
            contrast_active=self.contrast_mod,
            warning=self._timeline_warning(),
        )

    def _timeline_warning(self) -> str:
        if self.advance_mode is not AdvanceMode.AUTO_FOLLOW:
            return self._transpose_warning()
        if self.timeline is None:
            return "Auto Follow expects a Digitone-step-aligned timeline, but none is loaded."
        if self.timeline.basis is TimelineBasis.SEGMENT_MAP:
            return (
                "Auto Follow cannot use a manual segment-map timeline. "
                f"Current timeline_basis is {self.timeline.basis.value}. "
                "Use a manual advance mode for this timeline."
            )
        transpose_warning = self._transpose_warning()
        if transpose_warning:
            return transpose_warning
        return ""

    def _transpose_warning(self) -> str:
        if (
            self.transpose_offset_semitones != 0
            and self.runtime_transpose_policy is RuntimeTransposePolicy.LOCKED
        ):
            return "Runtime Song Transpose is locked for this timeline."
        if (
            self.transpose_offset_semitones != 0
            and self.runtime_transpose_policy is RuntimeTransposePolicy.WARN
        ):
            return "Runtime Song Transpose may diverge from the external device timeline."
        return ""
