# Emiuet Session R&D Architecture

## 概要 (JA)

Emiuet Session は Emiuet の mini 版です。フルサイズのギター指板を再現するもの
ではなく、初心者が**少ないキー（8キー）**で、コード進行に追従しながらジャズ的な
即興を楽しむための小型演奏機です。

このドキュメントは、今回追加した **R&D core / Performance Model / Desktop harness**
の構造を説明します。既存の Phase 1（Teensy ファームウェア）はそのまま残し、その横に
GUI / Arduino / MIDI ライブラリに依存しない演奏ロジックを Python で実装しました。
C++（Teensy / ESP32）への移植は、この構造をなぞる**後続フェーズ**です。

## Why this exists

The goal is a *compact, chord-aware improvisation instrument* for beginners:
play interesting, jazz-flavoured lines with few keys while following a chord
progression. This R&D layer prototypes the musical logic in a form that runs and
is testable on a desktop, and that ports cleanly to firmware later.

## Responsibility split (EUB Changes vs Emiuet Session)

Emiuet Session **inherits** Changes' harmonic assets but does **not** embed
Changes' app or UI.

```
EUB Changes (existing, Python)        Emiuet Session (this repo)
--------------------------------      ---------------------------------------
- iReal Pro / song-form import        Model Builder:
- song normalisation                    - read Song + HarmonicAnalysis
- chord analysis                        - build the 8-slot Performance Model
- LPC / scale candidates / priority     - voice-lead step to step
- chord tone / tension / colour info    - group chords into manual segments
        |                             Runtime (EmiuetCore):
        | export (HarmonicAnalysis)     - segment/step state, tempo timing
        v                               - 8 keys -> notes, register, approach
  HarmonicAnalysis model  ----------->  - note lifecycle, panic
                                        - emit abstract MIDI + DisplayState
```

Changes computes *theory*; Emiuet Session turns it into a *playable surface* and
plays it. We keep that boundary so Changes can evolve independently.

## Layers (and the portability rule)

```
emiuet_session/
  core/      pure types + helpers   (no GUI, no MIDI library, no platform I/O)
  model/     Song / Analysis / PerformanceModel + builders (layout, meter)
  runtime/   EmiuetCore.process(InputFrame) -> OutputFrame
  fixtures/  built-in sample song/analysis
apps/
  desktop_debug/   CLI harness (an adapter, not core)
tests/       pytest
docs/        this documentation
```

**Core rule:** nothing in `core/`, `model/`, or `runtime/` may import a GUI
toolkit, a MIDI library, Arduino APIs, or platform-specific I/O. The engine only
*returns* abstract `MidiEvent`s and a `DisplayState`; adapters translate them.
This is what makes the same logic valid on a desktop and (after a C++ port) on a
Teensy/ESP32.

## The frame loop

The engine is driven one frame at a time:

```
output = core.process(input_frame)
```

- `InputFrame` — key press/release edges, register/approach/segment commands,
  tempo, profile, panic, and the current time. The engine keeps held-key state,
  so adapters only report edges.
- `OutputFrame` — abstract MIDI events to emit + a `DisplayState` snapshot.

## Key design decisions (the non-obvious ones)

- **Register shift, not fixed octave.** With only 8 keys, ±12 is often too big a
  jump. The control has selectable step sizes (Octave / FifthSlide / FourthSlide
  / CustomSemitone). Buttons may be labelled Oct+/Oct- physically, but software
  never assumes 12. See `core/register_shift.py`.
- **Manual segment advance.** One Next press moves a musically sensible amount
  (a *segment*); chord changes inside it (*steps*) auto-advance by tempo. This
  keeps manual actions to ~1–2 s even at fast tempos. See `docs/segment_policy.md`.
- **8-slot layout with voicing de-dup.** Core notes on even keys, colour/tension
  on odd keys, voice-led between steps, with a deterministic slot-voicing
  de-duplication pass. See `docs/emiuet_performance_model.md`.
- **Safe note lifecycle.** A held note keeps its triggered pitch until release;
  layout/segment changes never retune or retrigger it. Panic turns everything
  off. These are guarded by tests.

## Firmware porting plan

This Python is the reference implementation. The C++ port will mirror the same
files (`include/emiuet/core`, `src/core`, …): `process()` signature, the abstract
`MidiEvent` model, register-shift/approach/layout policies, and the note
lifecycle rules. The existing Phase 1 firmware (`src/main.cpp`, `KeyScanner`,
`MidiEngine`, `SongData`, `platformio.ini`) is untouched and still builds; it
remains the validated hardware-I/O bring-up while this layer matures.
