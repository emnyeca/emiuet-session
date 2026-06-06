# Phase 1 Breadboard Prototype

This document is the wiring and bring-up note for the first Emiuet Session prototype.
The purpose is to measure whether the performance surface, manual song-position stepping, and USB/TRS MIDI output are fast and observable enough before committing to the later hardware shape.

## Scope

- Teensy 4.1 firmware built with PlatformIO.
- 16 analog key inputs through one CD74HC4067 multiplexer.
- Manual forward/back buttons for fixed song-position stepping.
- USB MIDI and TRS MIDI Type-A CC output.
- Serial monitor output for raw/filtered key values and active chord position.

This phase does not implement LPC generation, display UI, internal synth, Changes import, or production PCB constraints.

## Prototype Pinout

| Function | Teensy 4.1 pin | Breadboard connection |
|---|---:|---|
| MUX S0 | 2 | CD74HC4067 S0 |
| MUX S1 | 3 | CD74HC4067 S1 |
| MUX S2 | 4 | CD74HC4067 S2 |
| MUX S3 | 5 | CD74HC4067 S3 |
| MUX SIG | A0 | CD74HC4067 SIG |
| Step forward | 6 | Momentary switch to GND |
| Step back | 7 | Momentary switch to GND |
| TRS MIDI TX | 1 / Serial1 TX | Type-A MIDI output circuit input |

## Analog Key Wiring

For a breadboard-safe first pass, each key channel can be either a potentiometer wiper or a sensor divider output.

- CD74HC4067 VCC: 3.3 V.
- CD74HC4067 GND and EN: GND.
- Channel C0-C15: analog key outputs.
- SIG: Teensy A0.
- Keep every analog output within 0-3.3 V.

The firmware uses a press threshold of `620` and a release threshold of `520` at 10-bit ADC resolution. These values are intentionally easy to change in `include/Phase1Config.h` after the first measurements.

## TRS MIDI Type-A Note

Do not connect Teensy TX directly to a TRS jack as a final electrical interface. Use the standard 3.3 V MIDI output driver/current-limiting circuit for the breadboard test, then connect it to the Type-A TRS jack:

- Tip: MIDI current-loop pin corresponding to DIN pin 5.
- Ring: MIDI current-loop pin corresponding to DIN pin 4.
- Sleeve: shield/chassis reference only where appropriate for the chosen output circuit.

The firmware sends CC messages through both `usbMIDI` and `Serial1` at 31250 baud.

## Bring-Up Checklist

1. Build and upload the `teensy41` PlatformIO environment.
2. Open the serial monitor at 115200 baud.
3. Confirm the startup line and fixed song position are printed.
4. Sweep each of the 16 analog channels and confirm the matching `keys=N:value` field changes.
5. Press and release around the threshold and confirm `*` appears only when pressed.
6. Press forward/back buttons and confirm the printed chord position changes.
7. Monitor USB MIDI and confirm CC20 changes on position steps, CC95 changes with aggregate pressure, and CC40-CC55 change for individual keys.
8. Connect the TRS MIDI output circuit to a receiver and repeat the CC observations.

## Data To Record

Record observations in `docs/experiments/phase1_results.md`.

- Scan stability and noise per sensor type.
- Threshold values that feel playable.
- Worst visible latency for USB and TRS MIDI.
- Wiring mistakes or pin conflicts.
- Any Phase 2 design decisions implied by the test.
