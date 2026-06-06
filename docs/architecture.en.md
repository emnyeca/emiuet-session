# Architecture

## System overview

```
Changes
    ↓
Song model
    ↓
Position engine
    ↓
Chord context
    ↓
Local Pitch Collection engine
    ↓
Performance engine
    ↓
Synth engine / MIDI output
```

## Modules

- **Song manager:** Loads and stores song definitions and metadata.
- **Position manager:** Tracks the current bar and beat and handles navigation.
- **LPC engine:** Derives Local Pitch Collections from chords.
- **Key scanner:** Reads analog sensors, applies filtering and detects note events.
- **Synth engine:** Generates audio on the Teensy via the Audio Library.
- **MIDI engine:** Formats and sends MIDI note and control messages.
- **UI engine:** Drives the display, encoders, LEDs and user interaction.

## Data flow

1. The user selects a song.
2. The song manager loads its structure and chords.
3. The position manager sets the bar counter to the start.
4. During each processing frame:
   - The key scanner reads sensors and detects key events.
   - The LPC engine generates a list of playable notes based on the current chord.
   - The performance engine maps sensor events to note numbers and velocities.
   - The synth engine plays the notes and/or the MIDI engine sends messages.
   - The UI engine updates the display and LEDs.
