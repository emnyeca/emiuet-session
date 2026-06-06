# Roadmap

This document outlines the planned phases for the Emiuet Session project.  The roadmap is high level and subject to change as the project evolves.

## Phase 1 – Basic Prototype

- Set up the Teensy development environment using PlatformIO and Visual Studio Code.
- Implement scanning for 16 analogue keys and basic debouncing.
- Implement fixed song data and manually step through positions.
- Output MIDI over USB and TRS‑A with simple CC messages to verify timing and latency.
- Document the experiment results to inform later design decisions.

## Phase 2 – Local Pitch Collection and User Interface

- Develop the Local Pitch Collection (LPC) engine that derives playable notes from the current chord context.
- Add a small OLED display to show the current song, section, bar and chord, along with the active LPC.
- Implement navigation controls (encoder or buttons) to move forward or backward through the song.
- Integrate the LPC engine with the key scanner so that pressing a key sends the appropriate note or CC for the current context.
- Begin adding a lightweight synthesizer using the Teensy Audio Library to enable standalone sound generation.

## Phase 3 – Changes Import and Presets

- Implement loading of song data exported from Changes, including structure and chord progressions.
- Support multiple songs and set lists with selection via the UI.
- Add presets for LPC mapping, velocity curves and performance surface behaviour.
- Refine the internal synthesiser with multiple voices and basic effects.
- Add program change and additional control messages to integrate with external instruments.

## Phase 4 – Connectivity and Hardware Refinement

- Add a secondary microcontroller (e.g. ESP32) for wireless configuration via smartphone or web browser.
- Design a custom PCB with integrated analogue sensors (e.g. hall‑effect switches) and audio output circuitry.
- Improve power management and add battery support for portable use.
- Finalise enclosure design, focusing on ergonomics and performance usability.
- Conduct extended field testing in live session environments and iterate on hardware and firmware based on feedback.
