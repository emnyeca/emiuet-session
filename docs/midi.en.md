# MIDI specification

Emiuet Session sends and receives standard MIDI messages.

## Channels

- **Note output channel:** Configurable (default 1).  All Note On/Off messages use this channel.
- **Control Change channel:** Configurable (default 1).  CC messages are typically sent on the same channel.

## Note mapping

- Each physical key maps to a note number derived from the current Local Pitch Collection.
- Extra keys beyond the LPC size may repeat the collection an octave higher or remain inactive.
- Velocity is derived from the initial pressure or travel speed.

## Control Change

- **CC95** (default) conveys overall pressure or a user‑defined expression parameter.
- Additional CC numbers may be assigned to individual keys or sensors.
- Firmware should send CC messages only when values change or at a minimum interval to avoid flooding.

## Program Change

Future firmware may implement Program Change to switch internal synth presets or external instruments.

## Connectivity

- **USB‑MIDI:** Class‑compliant device for computers and mobile devices.
- **TRS MIDI Type‑A:** Compatible with standard DIN MIDI using an adaptor.
- **BLE‑MIDI (optional):** If an ESP32 or similar module is included, wireless MIDI may be supported.

## Timing

The total latency from key press to MIDI transmission should remain under 5 ms for USB and under 8 ms for TRS.
