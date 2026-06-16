"""Drive the Emiuet Session R&D core from a real MIDI controller.

Usage::

    # list available MIDI input ports
    python -m apps.desktop_debug.midi_controller_harness --list-ports

    # play the core from a controller via a profile
    python -m apps.desktop_debug.midi_controller_harness \
        --midi-in "MIDI PAD-01" \
        --profile apps/desktop_debug/controller_profiles/ccp16.json

    # demonstrate the mapping + core without any hardware (synthetic messages)
    python -m apps.desktop_debug.midi_controller_harness --self-test

For each incoming message the harness logs RAW (the MIDI message), MAPPED (the
action it resolved to), and then the engine's emitted MIDI events and the
two-row DisplayState (via the shared DebugConsole renderer).
"""

from __future__ import annotations

import argparse
import sys
import time

from emiuet_session.core.frames import InputFrame
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

_SELF_TEST_PROFILE = "ccp16"


def _emit(console: DebugConsole, mapped: str | None, raw: str, frame: InputFrame | None) -> None:
    print(f"RAW    : {raw}")
    print(f"MAPPED : {mapped if mapped else '(unmapped -- not in profile)'}")
    if frame is not None:
        frame.now_ms = console.clock_ms
        out = console.core.process(frame)
        for ev in out.midi_events:
            print(f"CORE   : {ev.short()}")
        print(console.render(out))
    print()


def _self_test(console: DebugConsole, mapper: MidiInputMapper) -> int:
    print("Self-test: feeding synthetic CCP16-style messages (no hardware).\n")
    script = [
        MidiMessage("note_on", channel=0, note=36, velocity=100),  # slot 0 press (C)
        MidiMessage("note_off", channel=0, note=36),  # slot 0 release
        MidiMessage("note_on", channel=0, note=40, velocity=90),  # slot 1 press (colour)
        MidiMessage("note_on", channel=0, note=45, velocity=127),  # next_segment
        MidiMessage("note_off", channel=0, note=40),  # slot 1 release (held across change)
        MidiMessage("note_on", channel=0, note=49, velocity=127),  # approach_plus press
        MidiMessage("note_on", channel=0, note=37, velocity=100),  # slot 2 press (raised +1)
        MidiMessage("note_off", channel=0, note=49),  # approach_plus release
        MidiMessage("note_off", channel=0, note=37),
        MidiMessage("note_on", channel=0, note=47, velocity=127),  # register_up
        MidiMessage("program_change", channel=0),  # unsupported -> logged only
        MidiMessage("note_on", channel=0, note=50, velocity=127),  # panic
    ]
    for msg in script:
        result = mapper.map(msg)
        _emit(console, result.mapped, result.raw, result.frame)
    return 0


def run(midi_in: str, profile: ControllerProfile, orientation: str) -> int:
    console = DebugConsole(EmiuetCore(sample_performance_model()), orientation=orientation)
    mapper = MidiInputMapper(profile)
    port = open_input(midi_in)
    start = time.monotonic()

    print(f"Listening on '{port.name}'. Press Ctrl+C to stop.\n")
    print(console.handle("state"))
    print()
    try:
        for msg in port:
            console.clock_ms = (time.monotonic() - start) * 1000.0
            result = mapper.map(MidiMessage.from_mido(msg))
            _emit(console, result.mapped, result.raw, result.frame)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        port.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emiuet Session MIDI controller harness")
    parser.add_argument("--list-ports", action="store_true", help="list MIDI input ports and exit")
    parser.add_argument("--midi-in", help="MIDI input port name, substring, or index")
    parser.add_argument("--profile", help="path to a controller profile JSON")
    parser.add_argument(
        "--layout-orientation", default="two-row", choices=["two-row", "alternating"]
    )
    parser.add_argument(
        "--self-test", action="store_true", help="run synthetic messages, no hardware needed"
    )
    args = parser.parse_args(argv)

    if args.list_ports:
        try:
            ports = list_input_ports()
        except RuntimeError as exc:
            print(exc, file=sys.stderr)
            return 2
        if not ports:
            print("No MIDI input ports found.")
        for i, name in enumerate(ports):
            print(f"[{i}] {name}")
        return 0

    print("Emiuet Session -- MIDI controller harness")

    if args.self_test:
        profile = ControllerProfile.load(_default_profile_path(_SELF_TEST_PROFILE))
        print(f"Loaded profile: {profile.name}\n")
        console = DebugConsole(EmiuetCore(sample_performance_model()), orientation=args.layout_orientation)
        return _self_test(console, MidiInputMapper(profile))

    if not args.midi_in or not args.profile:
        parser.error("--midi-in and --profile are required (or use --list-ports / --self-test)")

    try:
        profile = ControllerProfile.load(args.profile)
    except ProfileError as exc:
        print(f"profile error: {exc}", file=sys.stderr)
        return 2
    print(f"Loaded profile: {profile.name}")

    try:
        return run(args.midi_in, profile, args.layout_orientation)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2


def _default_profile_path(name: str):
    from .midi_input import PROFILES_DIR

    return PROFILES_DIR / f"{name}.json"


if __name__ == "__main__":
    raise SystemExit(main())
