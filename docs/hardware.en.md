# Hardware notes

This document records hardware choices and recommendations for Emiuet Session prototypes.

## Key switches

Emiuet Session uses analog key switches to capture continuous travel or pressure.  Two approaches are considered:

- **Hall‑effect switches (magnetic).**  Each key contains a magnet and a Hall sensor on the PCB.  The sensor output reflects the magnet position.  Pros: smooth linear response, long lifespan.  Cons: requires precise alignment.
- **Force‑sensitive resistors (FSR).**  Simple resistive sensors that change resistance with pressure.  Pros: inexpensive and easy to integrate.  Cons: non‑linear response and drift over time.

For a compact keyboard layout, magnetic switches are recommended.  For a fretboard‑style layout, FSRs under rubber pads are acceptable.

## Microcontroller

Teensy 4.x boards are the primary target.  They offer high CPU speed, fast ADC sampling, built‑in USB‑MIDI and an audio library.  Smaller Teensy models or other MCUs can be used for simpler prototypes.

## Multiplexing

Use CD74HC4067 16‑channel analog multiplexer chips to read many sensors with few analog pins.  Connect the multiplexer output to a single ADC input and use GPIO pins to select channels.

## Power and I/O

- Power via USB‑C or an internal Li‑Po battery with a charger circuit.
- TRS Type‑A MIDI output jack.
- 3.5 mm stereo audio output (optionally balanced).
- Optional headphone amplifier.

## Enclosure

Early prototypes can use laser‑cut acrylic or 3D‑printed cases.  Final versions may use aluminium or wood.  Ensure that keys are firmly mounted and that LEDs are diffused for clear feedback.
