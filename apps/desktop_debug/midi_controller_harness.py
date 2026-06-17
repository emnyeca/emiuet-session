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
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore

from .cli import DebugConsole
from .midi_input import (
    ControllerProfile,
    MidiInputMapper,
    MidiMessage,
    ProfileError,
    list_input_ports,
    open_input,
)
from .midi_output import MidiOutputAdapter, list_output_ports

_SELF_TEST_PROFILE = "ccp16"


def _emit(console, result, adapter: MidiOutputAdapter | None, frame: InputFrame | None) -> None:
    print(f"RAW    : {result.raw}")
    print(f"MAPPED : {result.mapped if result.mapped else '(unmapped -- not in profile)'}")
    if frame is None:
        print()
        return
    frame.now_ms = console.clock_ms
    out = console.core.process(frame)
    for ev in out.midi_events:
        print(f"CORE   : {ev.short()}")
        if adapter is not None:
            print(f"OUT    : {adapter.send_event(ev)}")
    # On a panic, also send All Notes Off (CC 123) to the channels in use.
    if frame.panic and adapter is not None:
        for line in adapter.all_notes_off():
            print(f"OUT    : {line}")
    print(console.render(out))
    print()


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


def _self_test(console, mapper, adapter: MidiOutputAdapter | None, mode: PerformanceMode) -> int:
    print("Self-test: feeding synthetic CCP16-style messages (no hardware).\n")
    # CCP16 sends on channel 10 (0-based 9) at FULL LEVEL velocity 127. Match the
    # profile's channel so the synthetic messages pass its channel filter.
    ch = (mapper.profile.midi_channel or 1) - 1
    script = _solo_script(ch) if mode is PerformanceMode.SOLO else _chord_script(ch)
    for msg in script:
        result = mapper.map(msg)
        _emit(console, result, adapter, result.frame)
    return 0


def run(midi_in, profile, orientation, adapter, send_all_notes_off, mode) -> int:
    console = DebugConsole(EmiuetCore(sample_performance_model(), mode=mode), orientation=orientation)
    mapper = MidiInputMapper(profile)
    port = open_input(midi_in)
    start = time.monotonic()

    out_name = adapter.name if adapter is not None else "(none, log only)"
    print(f"Input : {port.name}")
    print(f"Output: {out_name}")
    print("Press Ctrl+C to stop.\n")
    print(console.handle("state"))
    print()
    try:
        for msg in port:
            console.clock_ms = (time.monotonic() - start) * 1000.0
            result = mapper.map(MidiMessage.from_mido(msg))
            _emit(console, result, adapter, result.frame)
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

    try:
        adapter = _make_adapter(args)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.self_test:
        default_profile = "ccp16_solo" if mode is PerformanceMode.SOLO else _SELF_TEST_PROFILE
        profile = ControllerProfile.load(_default_profile_path(default_profile))
        print(f"Mode: {args.mode}  |  Loaded profile: {profile.name}")
        print(f"Output: {adapter.name if adapter else '(none, log only)'}\n")
        console = DebugConsole(
            EmiuetCore(sample_performance_model(), mode=mode), orientation=args.layout_orientation
        )
        rc = _self_test(console, MidiInputMapper(profile), adapter, mode)
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
    print(f"Mode: {args.mode}  |  Loaded profile: {profile.name}")

    try:
        return run(
            args.midi_in, profile, args.layout_orientation, adapter,
            args.send_all_notes_off_on_exit, mode,
        )
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2


def _default_profile_path(name: str):
    from .midi_input import PROFILES_DIR

    return PROFILES_DIR / f"{name}.json"


if __name__ == "__main__":
    raise SystemExit(main())
