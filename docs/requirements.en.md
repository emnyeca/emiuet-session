# Functional requirements

## Core features

- **Load song data from Changes.**  A song definition includes structure, chords, tempo and meter.
- **Navigate the current position.**  The player can move forward or backward through the song.  A display shows the current bar and chord.
- **Display the current chord.**  The UI always indicates which chord is active.
- **Generate the Local Pitch Collection.**  For each chord the instrument calculates the set of allowed notes.
- **Map the LPC to the performance surface.**  Only notes from the LPC are playable at any moment.
- **Internal sound generation.**  A lightweight synthesizer on the hardware produces audio.
- **MIDI output.**  The device sends note and CC messages over USB and TRS MIDI.

## Input

- 16 analog performance keys
- Rotary encoder for navigation
- Function buttons
- Optional footswitch input

## Output

- Internal synthesizer
- USB MIDI
- TRS MIDI Type‑A

## Display

- Current song name
- Current section
- Current bar number
- Current chord and scale
- Active LPC
