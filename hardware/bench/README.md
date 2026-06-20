# Emiuet Session — Teensy Development Bench

This directory manages the **Emiuet Session Teensy 4.1 development bench**.
このディレクトリは **Emiuet Session Teensy 4.1 開発ベンチ** を管理します。

> ⚠️ This is **not** the final Emiuet Session PCB.
> It is a replaceable validation rig for bringing up firmware on real hardware.
>
> ⚠️ これは **完成版の Emiuet Session PCB ではありません**。
> 実機上でファームウェアを立ち上げ・検証するための、差し替え可能な開発リグです。

The bench intentionally favors easily replaceable, off-the-shelf parts (tact
switches, breadboard / universal board, jumper wires) so that the input layer
can be swapped later (for example, Hall-effect keys) without redesigning the
performance logic.

## Phase plan / フェーズ計画

| Phase | Goal | Status |
|---|---|---|
| **A** | Validate Teensy 4.1 firmware, 16 performance keys, push rotary encoder, display, onboard microSD, USB MIDI | **This scaffold** |
| **B** | Add TRS MIDI IN/OUT (Serial1, pins 0/1) | Reserved |
| **C** | Evaluate 2×8 key layout / performance feel | Future |
| **D** | Evaluate Audio Shield / I2S DAC | Future |
| **E** | Introduce a carrier PCB or small atopile/KiCad boards | Future |

### Phase A validates / Phase A で検証する範囲

- Teensy 4.1 firmware bring-up on real hardware
- 16 performance keys (initial layout: 4×4 matrix with one diode per key)
- one push rotary encoder (EC11-style)
- a display (option A: 128×64 I2C OLED, option B: 2-inch SPI LCD)
- the **onboard microSD slot** of the Teensy 4.1
- **USB MIDI** over the Teensy onboard USB

### Explicitly out of scope for Phase A / Phase A の対象外

- TRS MIDI IN/OUT → **Phase B** (pins 0/1 reserved only, no circuit yet)
- Audio Shield / I2S DAC → **Phase D** (do **not** route now)
- Hall-effect keys → future evaluation (do **not** route now)
- Final enclosure, production PCB, JLCPCB BOM/CPL → out of scope here

## Logic level / 信号レベル

All bench signals are **3.3 V only**. Teensy 4.1 GPIO is **not 5 V tolerant**.
Never connect a 5 V signal to a Teensy GPIO pin.

すべての信号は **3.3V のみ** です。Teensy 4.1 の GPIO は **5V トレラントではありません**。
5V 信号を Teensy の GPIO に接続しないでください。

## Layout / 構成

```text
hardware/bench/
  README.md                     ← this file
  wiring/                       ← human-readable wiring tables and notes
    phase_a_pinout.md
    phase_a_bom.md
    phase_a_wiring_notes.md
    phase_b_trs_midi_notes.md
  atopile/                      ← machine-readable wiring intent (ato scaffold)
    ato.yaml
    README.md
    src/
    layout/
  kicad/                        ← reserved for later bench carrier boards
  photos/                       ← bring-up photos / reference shots
```

See also: [`docs/emiuet-session/bench_phase_a.md`](../../docs/emiuet-session/bench_phase_a.md)
for the rationale behind these Phase A decisions.
