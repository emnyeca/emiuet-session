"""Interactive CLI debug harness for EmiuetCore.

This is an *adapter*, not part of the core: it turns typed commands into
``InputFrame``s, feeds the engine, and renders the resulting MIDI events and
DisplayState. A GUI front-end can later reuse the same engine the same way.

Run::

    python -m apps.desktop_debug                            # interactive (two-row)
    python -m apps.desktop_debug --layout-orientation alternating
    python -m apps.desktop_debug --demo                     # scripted demonstration
    python -m apps.desktop_debug --script FILE

Interactive commands (type ``help``)::

    1..8        trigger a key (NoteOn+NoteOff)      hold N / rel N  sustain/release
    next / prev move segment                        up / down / reset  register shift
    mode octave|fifth|fourth|custom N               app+ / app- / app0  approach
    tempo BPM   change tempo                         tick MS  advance virtual time
    profile     cycle profile                        panic   all active notes off
    orientation [two-row|alternating]  switch/show view   layout  show current view
    state       reprint                              help / quit

Two-row view (TWO_ROW_CORE_COLOR): the colour line is the top row and the core
line the bottom row; each line ascends left to right.
"""

from __future__ import annotations

import sys

from emiuet_session.core.approach import ApproachDirection
from emiuet_session.core.frames import InputFrame, OutputFrame, RegisterCommand, SegmentCommand
from emiuet_session.core.register_shift import RegisterShiftMode
from emiuet_session.fixtures import sample_performance_model
from emiuet_session.runtime import EmiuetCore

_MODES = {
    "octave": RegisterShiftMode.OCTAVE,
    "fifth": RegisterShiftMode.FIFTH_SLIDE,
    "fourth": RegisterShiftMode.FOURTH_SLIDE,
    "custom": RegisterShiftMode.CUSTOM_SEMITONE,
}

_DEMO_SCRIPT = """\
state
layout
orientation alternating
orientation two-row
1
hold 0
next
rel 0
up
mode fifth
up
3
reset
app+
5
app0
tempo 90
panic
prev
"""


class DebugConsole:
    def __init__(self, core: EmiuetCore, orientation: str = "two-row") -> None:
        self.core = core
        self.clock_ms = 0.0
        self.render_orientation = orientation  # "two-row" | "alternating"

    # ---- rendering -----------------------------------------------------

    def _key_block(self, d) -> list[str]:
        if self.render_orientation == "two-row":
            # Two rows of four; each line ascends left to right.
            color = "  ".join(f".{label}" for label in d.color_line)  # . = colour
            core = "  ".join(f"#{label}" for label in d.core_line)  # # = core
            return [f"  color: {color}", f"  core : {core}"]
        keys = []
        for i, label in enumerate(d.slot_labels):
            marker = "#" if i % 2 == 0 else "."
            keys.append(f"{i + 1}{marker}{label}")
        return ["  keys : " + "  ".join(keys)]

    def render(self, out: OutputFrame) -> str:
        d = out.display
        assert d is not None
        if d.mode == "Solo":
            return self._render_solo(out, d)
        lines = [
            f"[seg {d.segment_index + 1}/{d.segment_count} "
            f"step {d.step_index + 1}/{d.step_count}]  "
            f"{d.current_chord} > {d.next_chord}    {d.register_label}  {d.profile_label}"
            f"  ({self.render_orientation})",
        ]
        lines += self._key_block(d)
        lines.append(
            f"  dbg  : {d.selected_collection} prio{d.scale_priority} "
            f"retry{d.retry_level} lpc={list(d.lpc)} active={list(d.active_notes)}"
        )
        for ev in out.midi_events:
            lines.append("  midi : " + ev.short())
        return "\n".join(lines)

    def _render_solo(self, out: OutputFrame, d) -> str:
        from emiuet_session.core.pitch import note_name

        last = d.last_output_note
        last_label = f"{note_name(last % 12)}({last})" if last is not None else "-"
        ahead = "  AHEAD" if d.ahead_active else ""
        lines = [
            f"  AIM  {d.aim_chord}{ahead}",
            f"  NOW  {d.now_chord}   t={d.ticks}",
            f"  NEXT {d.next_chord}",
            f"  TR   {d.transport}  {d.advance_mode}  SOLO",
            f"  last: {last_label}  gesture: {d.last_gesture or '-'}  dir: {d.phrase_direction}",
            f"  pending: octave={d.pending_octave:+d} skip={d.pending_skip}",
            f"  core: {' '.join(note_name(pc) for pc in d.core_pcs)}",
            f"  lpc : {' '.join(note_name(pc) for pc in d.lpc)}",
        ]
        if d.resolver_trace:
            lines.append(f"  trace: {d.resolver_trace}")
        if d.warning:
            lines.append(f"  WARN : {d.warning}")
        for ev in out.midi_events:
            lines.append("  midi : " + ev.short())
        return "\n".join(lines)

    # ---- command handling ---------------------------------------------

    def feed(self, frame: InputFrame) -> OutputFrame:
        frame.now_ms = self.clock_ms
        return self.core.process(frame)

    def handle(self, line: str) -> str | None:
        """Process one command line. Returns text to print, or None to quit."""
        parts = line.strip().split()
        if not parts:
            return ""
        cmd, args = parts[0].lower(), parts[1:]

        if cmd in ("quit", "exit", "q"):
            return None
        if cmd == "help":
            return __doc__ or ""
        if cmd == "state":
            return self.render(self.feed(InputFrame()))

        if cmd.isdigit() and 1 <= int(cmd) <= 8:
            slot = int(cmd) - 1
            self.feed(InputFrame(key_presses=(slot,)))
            return self.render(self.feed(InputFrame(key_releases=(slot,))))
        if cmd == "hold" and args:
            return self.render(self.feed(InputFrame(key_presses=(int(args[0]),))))
        if cmd == "rel" and args:
            return self.render(self.feed(InputFrame(key_releases=(int(args[0]),))))

        if cmd == "next":
            return self.render(self.feed(InputFrame(segment_command=SegmentCommand.NEXT)))
        if cmd == "prev":
            return self.render(self.feed(InputFrame(segment_command=SegmentCommand.PREV)))

        if cmd == "up":
            return self.render(self.feed(InputFrame(register_command=RegisterCommand.UP)))
        if cmd == "down":
            return self.render(self.feed(InputFrame(register_command=RegisterCommand.DOWN)))
        if cmd == "reset":
            return self.render(self.feed(InputFrame(register_command=RegisterCommand.RESET)))
        if cmd == "mode" and args:
            mode = _MODES.get(args[0].lower())
            if mode is None:
                return f"unknown mode: {args[0]}"
            step = int(args[1]) if len(args) > 1 else None
            return self.render(
                self.feed(InputFrame(register_mode=mode, register_custom_step=step))
            )

        if cmd == "app+":
            return self.render(self.feed(InputFrame(approach_press=ApproachDirection.PLUS)))
        if cmd == "app-":
            return self.render(self.feed(InputFrame(approach_press=ApproachDirection.MINUS)))
        if cmd == "app0":
            return self.render(
                self.feed(
                    InputFrame(
                        approach_release=ApproachDirection.PLUS,
                    )
                )
            )

        if cmd == "profile":
            return self.render(self.feed(InputFrame(profile_command="cycle")))
        if cmd == "tempo" and args:
            return self.render(self.feed(InputFrame(tempo_bpm=float(args[0]))))
        if cmd == "tick" and args:
            self.clock_ms += float(args[0])
            return self.render(self.feed(InputFrame()))
        if cmd == "panic":
            return self.render(self.feed(InputFrame(panic=True)))

        if cmd in ("orientation", "layout"):
            if args and args[0].lower() in ("two-row", "two", "alternating", "alt"):
                self.render_orientation = "two-row" if args[0].lower().startswith("two") else "alternating"
            return self.render(self.feed(InputFrame()))

        return f"unknown command: {line.strip()} (type 'help')"


def _run_lines(console: DebugConsole, lines: list[str], echo: bool) -> None:
    for raw in lines:
        if echo:
            print(f"> {raw.strip()}")
        result = console.handle(raw)
        if result is None:
            break
        if result:
            print(result)
            print()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    orientation = "two-row"
    if "--layout-orientation" in argv:
        value = argv[argv.index("--layout-orientation") + 1].lower()
        orientation = "alternating" if value.startswith("alt") else "two-row"

    console = DebugConsole(EmiuetCore(sample_performance_model()), orientation=orientation)

    print("Emiuet Session -- desktop debug harness")
    print(f"Loaded: {console.core.model.source_title}  "
          f"({console.core.model.meter}, {console.core.tempo_bpm:.0f} BPM, "
          f"{console.core.model.segment_count()} segments)")
    print()

    if "--demo" in argv:
        _run_lines(console, _DEMO_SCRIPT.splitlines(), echo=True)
        return 0
    if "--script" in argv:
        path = argv[argv.index("--script") + 1]
        with open(path, encoding="utf-8") as fh:
            _run_lines(console, fh.read().splitlines(), echo=True)
        return 0

    print(console.handle("state"))
    print()
    while True:
        try:
            line = input("> ")
        except EOFError:
            break
        result = console.handle(line)
        if result is None:
            break
        if result:
            print(result)
            print()
    return 0
