"""Drive the Emiuet Session R&D core from a real MIDI controller.

Usage (PowerShell; use a backtick ` for line continuation, or one line)::

    # list MIDI input and output ports
    python -m apps.desktop_debug.midi_controller_harness --list-ports

    # play the core from a controller and send to a MIDI OUT port
    python -m apps.desktop_debug.midi_controller_harness `
        --midi-in "H12MIDI-Pro 1" `
        --midi-out "H12MIDI-Pro 1" `
        --profile apps/desktop_debug/controller_profiles/ccp16.json

    # mapping + core only, no hardware (synthetic messages); add --dry-run for OUT log
    python -m apps.desktop_debug.midi_controller_harness --self-test

For each incoming message the harness logs RAW (the MIDI message), MAPPED (the
resolved action), CORE (the engine's abstract MIDI events), and -- when a MIDI
OUT is attached -- OUT (the messages actually sent), plus the two-row
DisplayState.
"""

from __future__ import annotations

import argparse
import sys
import time

from emiuet_session.core.frames import InputFrame
from emiuet_session.core.mode import PerformanceMode
from emiuet_session.core.timeline import AheadTargetPolicy, CompiledTimeline, TimelineBasis
from emiuet_session.core.timeline_io import load_compiled_timeline
from emiuet_session.core.transport import AdvanceMode, TransportEvent
from emiuet_session.fixtures import sample_compiled_timeline, sample_performance_model
from emiuet_session.runtime import EmiuetCore

from .cli import DebugConsole
from .midi_input import (
    ControllerProfile,
    MidiInputMapper,
    MidiMessage,
    ProfileError,
    list_input_ports,
    open_input,
    realtime_input_frame,
)
from .midi_output import MidiOutputAdapter, list_output_ports

_SELF_TEST_PROFILE = "ccp16"


def _consume(console, frame: InputFrame, adapter: MidiOutputAdapter | None):
    """Process a frame and send its events; return (out, list of OUT log lines)."""
    frame.now_ms = console.clock_ms
    out = console.core.process(frame)
    out_lines: list[str] = []
    if adapter is not None:
        for ev in out.midi_events:
            out_lines.append(adapter.send_event(ev))
        if frame.panic:  # also send All Notes Off (CC 123) to channels in use
            out_lines.extend(adapter.all_notes_off())
    return out, out_lines


def _print_block(raw: str, mapped: str | None, out, out_lines: list[str], console) -> None:
    print(f"RAW    : {raw}")
    print(f"MAPPED : {mapped if mapped else '(unmapped -- not in profile)'}")
    for ev in out.midi_events:
        print(f"CORE   : {ev.short()}")
    for line in out_lines:
        print(f"OUT    : {line}")
    print(console.render(out))
    print()


def _emit(console, result, adapter: MidiOutputAdapter | None, frame: InputFrame | None) -> None:
    if frame is None:
        print(f"RAW    : {result.raw}")
        print(f"MAPPED : {result.mapped if result.mapped else '(unmapped -- not in profile)'}")
        print()
        return
    out, out_lines = _consume(console, frame, adapter)
    _print_block(result.raw, result.mapped, out, out_lines, console)


def _shutdown(console, adapter: MidiOutputAdapter | None, send_all_notes_off: bool) -> None:
    """Stuck-note safety: stop everything still sounding when the harness ends."""
    if adapter is None:
        return
    panic = console.core.process(InputFrame(panic=True))
    for ev in panic.midi_events:
        print(f"OUT    : {adapter.send_event(ev)}")
    if send_all_notes_off:
        for line in adapter.all_notes_off():
            print(f"OUT    : {line}")
    adapter.close()


def _chord_script(ch: int) -> list[MidiMessage]:
    return [
        MidiMessage("note_on", channel=ch, note=36, velocity=127),  # slot 0 press (C)
        MidiMessage("note_off", channel=ch, note=36),  # slot 0 release
        MidiMessage("note_on", channel=ch, note=40, velocity=127),  # slot 1 press (colour)
        MidiMessage("note_on", channel=ch, note=45, velocity=127),  # next_segment
        MidiMessage("note_off", channel=ch, note=40),  # slot 1 release (held across change)
        MidiMessage("note_on", channel=ch, note=47, velocity=127),  # register_up
        MidiMessage("program_change", channel=ch),  # unsupported -> logged only
        MidiMessage("note_on", channel=ch, note=50, velocity=127),  # panic
    ]


def _solo_script(ch: int) -> list[MidiMessage]:
    # 36 repeat, 41 core_up, 42 lpc_up, 43 chromatic_up, 46 pending_skip,
    # 49 pending_octave_up, 45 next_segment, 40 resolve, 51 panic
    def on(note):
        return MidiMessage("note_on", channel=ch, note=note, velocity=127)

    def off(note):
        return MidiMessage("note_off", channel=ch, note=note)

    return [
        on(36), off(36),          # repeat (initial) -> C4
        on(41), off(41),          # core_up -> D4
        on(42), off(42),          # lpc_up
        on(43), off(43),          # chromatic_up
        on(46),                   # pending_skip
        on(41), off(41),          # core_up with skip=1
        on(49),                   # pending_octave_up
        on(41), off(41),          # core_up +12
        on(45),                   # next_segment (held note stays; next gesture uses new LPC)
        on(40), off(40),          # resolve in the new chord
        on(51),                   # panic
    ]


def _autofollow_script() -> list[tuple[str, str, InputFrame]]:
    """Synthetic transport + gesture frames demonstrating Auto Follow + Harmonic Ahead."""
    from emiuet_session.core.solo import SoloGesture

    return [
        ("FA Start", "start", InputFrame(transport_event=TransportEvent.START)),
        ("pad repeat", "repeat", InputFrame(solo_gesture=SoloGesture.REPEAT)),
        ("pad harmonic_ahead", "harmonic_ahead", InputFrame(harmonic_ahead=True)),
        ("pad core_up (AIM=next chord)", "core_up", InputFrame(solo_gesture=SoloGesture.CORE_UP)),
        ("pad lpc_up (ahead held)", "lpc_up", InputFrame(solo_gesture=SoloGesture.LPC_UP)),
        ("F8 x24 -> arrive next step", "clock x24", InputFrame(clock_pulses=24)),
        ("pad resolve (new chord)", "resolve", InputFrame(solo_gesture=SoloGesture.RESOLVE)),
        ("pad contrast_mod hold", "contrast_mod press", InputFrame(contrast_mod_press=True)),
        ("pad core_up (AIM=contrast)", "core_up", InputFrame(solo_gesture=SoloGesture.CORE_UP)),
        ("release contrast_mod", "contrast_mod release", InputFrame(contrast_mod_release=True)),
        ("FC Stop", "stop", InputFrame(transport_event=TransportEvent.STOP)),
    ]


def _self_test(console, mapper, adapter, mode, advance_mode) -> int:
    print("Self-test: feeding synthetic messages (no hardware).\n")
    if advance_mode is AdvanceMode.AUTO_FOLLOW:
        for raw, mapped, frame in _autofollow_script():
            out, out_lines = _consume(console, frame, adapter)
            _print_block(raw, mapped, out, out_lines, console)
        return 0
    # CCP16 sends on channel 10 (0-based 9) at FULL LEVEL velocity 127.
    ch = (mapper.profile.midi_channel or 1) - 1
    script = _solo_script(ch) if mode is PerformanceMode.SOLO else _chord_script(ch)
    for msg in script:
        result = mapper.map(msg)
        _emit(console, result, adapter, result.frame)
    return 0


def build_console(
    mode, advance_mode, ahead_policy, orientation, timeline_basis="digitone-step",
    timeline_path=None,
) -> DebugConsole:
    timeline = None
    if advance_mode is AdvanceMode.AUTO_FOLLOW:
        # A real EUB Changes export (--timeline) takes precedence; otherwise use the
        # built-in sample compiled timeline.
        timeline = (
            load_compiled_timeline(timeline_path) if timeline_path else sample_compiled_timeline()
        )
        # Honour --timeline-basis so the warning path is observable on hardware:
        # an original-song basis must actually produce the warning, not silently
        # behave like digitone-step.
        if timeline_basis == "original-song":
            timeline = CompiledTimeline(
                basis=TimelineBasis.ORIGINAL_SONG,
                steps=timeline.steps,
                original_tempo=timeline.original_tempo,
                digitone_tempo=timeline.digitone_tempo,
            )
    core = EmiuetCore(
        sample_performance_model(), mode=mode, advance_mode=advance_mode, timeline=timeline
    )
    core.harmonic_ahead.policy = ahead_policy
    return DebugConsole(core, orientation=orientation)


def run(
    midi_in, profile, orientation, adapter, send_all_notes_off, mode, advance_mode,
    ahead_policy, timeline_basis, timeline_path,
) -> int:
    console = build_console(
        mode, advance_mode, ahead_policy, orientation, timeline_basis, timeline_path
    )
    mapper = MidiInputMapper(profile)
    port = open_input(midi_in)
    start = time.monotonic()

    out_name = adapter.name if adapter is not None else "(none, log only)"
    print(f"Input : {port.name}")
    print(f"Output: {out_name}")
    print(f"Mode: {mode.value}  Advance: {advance_mode.value}")
    print("Press Ctrl+C to stop.\n")
    print(console.handle("state"))
    print()

    prev_now, prev_ahead = None, False
    try:
        for msg in port:
            console.clock_ms = (time.monotonic() - start) * 1000.0
            realtime = realtime_input_frame(msg.type)
            if realtime is not None:
                out, out_lines = _consume(console, realtime, adapter)
                d = out.display
                # Clock is high-frequency: only render on a meaningful change.
                changed = (
                    realtime.transport_event is not None
                    or bool(out.midi_events)
                    or d.now_chord != prev_now
                    or d.ahead_active != prev_ahead
                )
                if changed:
                    _print_block(msg.type, msg.type, out, out_lines, console)
                prev_now, prev_ahead = d.now_chord, d.ahead_active
                continue
            result = mapper.map(MidiMessage.from_mido(msg))
            _emit(console, result, adapter, result.frame)
            if result.frame is not None:
                prev_now, prev_ahead = console.core.current_context().chord, console.core.harmonic_ahead.active
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        _shutdown(console, adapter, send_all_notes_off)
        port.close()
    return 0


def _print_ports(show_in: bool, show_out: bool) -> int:
    try:
        if show_in:
            print("MIDI input ports:")
            ins = list_input_ports()
            for i, name in enumerate(ins) if ins else []:
                print(f"[{i}] {name}")
            if not ins:
                print("(none)")
        if show_out:
            if show_in:
                print()
            print("MIDI output ports:")
            outs = list_output_ports()
            for i, name in enumerate(outs) if outs else []:
                print(f"[{i}] {name}")
            if not outs:
                print("(none)")
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


def _make_adapter(args) -> MidiOutputAdapter | None:
    if args.midi_out:
        return MidiOutputAdapter.open(args.midi_out)  # may raise RuntimeError
    if args.dry_run:
        return MidiOutputAdapter()  # port=None -> formats OUT lines, sends nothing
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emiuet Session MIDI controller harness")
    parser.add_argument("--list-ports", action="store_true", help="list input and output ports")
    parser.add_argument("--list-inputs", action="store_true", help="list MIDI input ports")
    parser.add_argument("--list-outputs", action="store_true", help="list MIDI output ports")
    parser.add_argument("--midi-in", help="MIDI input port name, substring, or index")
    parser.add_argument("--midi-out", help="MIDI output port name, substring, or index")
    parser.add_argument("--profile", help="path to a controller profile JSON")
    parser.add_argument(
        "--layout-orientation", default="two-row", choices=["two-row", "alternating"]
    )
    parser.add_argument(
        "--mode", default="chord", choices=["chord", "solo", "bassist"],
        help="performance mode (default: chord; bassist is reserved/not implemented)",
    )
    parser.add_argument(
        "--advance-mode", default="manual", choices=["manual", "auto-follow"],
        help="manual segment advance, or auto-follow the Digitone-step timeline",
    )
    parser.add_argument(
        "--clock-source", default="midi-clock", choices=["internal", "midi-clock"],
        help="(auto-follow) clock source; only midi-clock is wired in v0",
    )
    parser.add_argument(
        "--transport-source", default="midi-transport", choices=["manual", "midi-transport"],
        help="(auto-follow) transport source; only midi-transport is wired in v0",
    )
    parser.add_argument(
        "--timeline-basis", default="digitone-step", choices=["digitone-step", "original-song"],
        help="(auto-follow) timeline basis; auto-follow expects digitone-step",
    )
    parser.add_argument(
        "--timeline", help="(auto-follow) path to a compiled timeline JSON from EUB Changes",
    )
    parser.add_argument(
        "--ahead-target", default="next-distinct-chord",
        choices=["next-distinct-chord", "next-step"],
        help="Harmonic Ahead target policy",
    )
    parser.add_argument(
        "--self-test", action="store_true", help="run synthetic messages, no hardware needed"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="format OUT log lines without sending MIDI"
    )
    parser.add_argument(
        "--send-all-notes-off-on-exit",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="also send CC 123 (All Notes Off) on exit (default: on)",
    )
    args = parser.parse_args(argv)

    if args.list_ports or args.list_inputs or args.list_outputs:
        show_in = args.list_ports or args.list_inputs
        show_out = args.list_ports or args.list_outputs
        return _print_ports(show_in, show_out)

    print("Emiuet Session -- MIDI controller harness")

    if args.mode == "bassist":
        print("BassistMode は予約のみで未実装です。--mode chord または --mode solo を使ってください。",
              file=sys.stderr)
        return 2
    mode = PerformanceMode.SOLO if args.mode == "solo" else PerformanceMode.CHORD
    advance_mode = (
        AdvanceMode.AUTO_FOLLOW if args.advance_mode == "auto-follow" else AdvanceMode.MANUAL
    )
    ahead_policy = (
        AheadTargetPolicy.NEXT_STEP if args.ahead_target == "next-step"
        else AheadTargetPolicy.NEXT_DISTINCT_CHORD
    )

    # v0 wires only midi-clock / midi-transport. Reject the unimplemented sources
    # explicitly (in Auto Follow) rather than silently ignoring them.
    if advance_mode is AdvanceMode.AUTO_FOLLOW:
        if args.clock_source != "midi-clock":
            parser.error("--clock-source internal is not implemented in v0; use midi-clock")
        if args.transport_source != "midi-transport":
            parser.error("--transport-source manual is not implemented in v0; use midi-transport")

    try:
        adapter = _make_adapter(args)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.self_test:
        if advance_mode is AdvanceMode.AUTO_FOLLOW:
            default_profile = "ccp16_autofollow"
        elif mode is PerformanceMode.SOLO:
            default_profile = "ccp16_solo"
        else:
            default_profile = _SELF_TEST_PROFILE
        profile = ControllerProfile.load(_default_profile_path(default_profile))
        print(f"Mode: {args.mode}  Advance: {args.advance_mode}  |  Profile: {profile.name}")
        print(f"Output: {adapter.name if adapter else '(none, log only)'}\n")
        console = build_console(
            mode, advance_mode, ahead_policy, args.layout_orientation, args.timeline_basis,
            args.timeline,
        )
        rc = _self_test(console, MidiInputMapper(profile), adapter, mode, advance_mode)
        _shutdown(console, adapter, args.send_all_notes_off_on_exit)
        return rc

    if not args.midi_in or not args.profile:
        parser.error(
            "--midi-in and --profile are required "
            "(or use --list-ports / --self-test). --midi-out is optional."
        )

    try:
        profile = ControllerProfile.load(args.profile)
    except ProfileError as exc:
        print(f"profile error: {exc}", file=sys.stderr)
        return 2
    print(f"Mode: {args.mode}  Advance: {args.advance_mode}  |  Profile: {profile.name}")

    try:
        return run(
            args.midi_in, profile, args.layout_orientation, adapter,
            args.send_all_notes_off_on_exit, mode, advance_mode, ahead_policy,
            args.timeline_basis, args.timeline,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2


def _default_profile_path(name: str):
    from .midi_input import PROFILES_DIR

    return PROFILES_DIR / f"{name}.json"


if __name__ == "__main__":
    raise SystemExit(main())
