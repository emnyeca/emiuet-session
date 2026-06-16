# R&D Core & Desktop Debug Harness

## 概要 (JA)

`EmiuetCore` を実際に動かして演奏状態・MIDI イベント・表示状態を確認するための
デスクトップ用 CLI ハーネスです。GUI には依存しません（将来 GUI へ拡張可能な構造）。
キー操作、セグメント送り、レジスタシフト、approach、テンポ変更、panic を試せます。

## Running

From the repo root:

```sh
python -m apps.desktop_debug                            # interactive (two-row)
python -m apps.desktop_debug --layout-orientation alternating
python -m apps.desktop_debug --demo                     # scripted demonstration
python -m apps.desktop_debug --script FILE
```

The harness is an **adapter**: it turns typed commands into `InputFrame`s, feeds
`EmiuetCore`, and renders the emitted MIDI events plus the `DisplayState`. A GUI
front-end could reuse the engine the same way.

## Commands

| Command | Effect |
|---------|--------|
| `1`..`8` | trigger a key (NoteOn + NoteOff) |
| `hold N` / `rel N` | sustain / release slot N (0-based) |
| `next` / `prev` | move segment |
| `up` / `down` / `reset` | register shift |
| `mode octave\|fifth\|fourth\|custom N` | set register step size |
| `app+` / `app-` / `app0` | approach up / down / clear |
| `profile` | cycle performance profile |
| `tempo BPM` | change tempo (recomputes step timing) |
| `tick MS` | advance virtual time (drives step auto-advance) |
| `panic` | all active notes off |
| `orientation [two-row\|alternating]` | switch / show the layout view |
| `layout` | show the current view |
| `state` | reprint current state |
| `help` / `quit` | help / exit |

## Reading the output (two-row, default)

```
[seg 1/4 step 1/1]  Dm7 > G7    OCT+0  NORM  (two-row)
  color: .E  .G  .B  .C+1
  core : #C  #D  #F  #A
  dbg  : D Dorian prio1 retry0 lpc=[2, 4, 5, 7, 9, 11, 0] active=[]
  midi : NoteOn  ch1 n 60 v100
```

- line 1 — segment/step progress, current → next chord, register label, profile,
  and the current view name.
- colour line (top, `.`) and core line (bottom, `#`); each ascends left-to-right.
  `C+1` is one octave above the C-anchor register (the borrowed upper extension).
- `dbg` — selected scale, priority, retry level, LPC, active notes.
- `midi` — the abstract events emitted this frame.

`orientation alternating` switches to the single-row view
(`keys : 1#C  2.E  3#D ...`); the note values are identical, only the reading
changes.

## What the demo shows

`--demo` walks a fixed script that demonstrates the load, a key trigger, a held
note surviving a segment change (released with its original pitch), register
shift modes, an approach-modified trigger, a tempo change, and panic. It runs
non-interactively, so it doubles as a quick smoke test of the engine.

## Future adapters

The same `OutputFrame` can drive a virtual MIDI-out port and a GUI shell, and a
generic MIDI-controller input adapter can build `InputFrame`s — none of which
require changes to the core. These are intentionally left as later work so the
playable/testable core lands first.
