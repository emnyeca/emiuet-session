# Glossary

This glossary collects key terms and concepts used throughout the Emiuet Session project.  It is intended as a quick reference for developers and collaborators.

## Changes

Changes is a tool for creating and managing chord progressions and song structures.  Emiuet Session imports song data from Changes to determine the current section, bar and chord.

## Local Pitch Collection (LPC)

The Local Pitch Collection is the set of notes derived from the current harmonic context.  It combines chord tones, modal notes and appropriate tensions while avoiding avoid notes.  The LPC changes as the song progresses.

## Position

The current location within the song, including section, bar and beat.  Navigating the position allows the performer to move through the chord progression during a session.

## Performance Surface

The interface through which the performer plays notes and controls Emiuet Session.  In the prototype, this consists of 16 analogue keys; future versions may use hall‑effect switches or other expressive sensors.

## Synth Engine

The internal sound generator based on the Teensy Audio Library.  It produces audio for standalone operation and can be configured with different timbres and effects.

## LPC Engine

The firmware component that converts chord and position information into the current Local Pitch Collection.  It applies rules for chord tones, scales, tensions and alterations.

## Session

A live performance context in which the performer navigates harmony in real time.  Emiuet Session is designed to support jazz sessions and machine‑live improvisation.

## TRS MIDI Type‑A

A 3.5 mm MIDI standard that uses tip and ring to transmit current‑loop MIDI signals.  Emiuet Session uses TRS MIDI Type‑A for direct connection to devices such as Digitone.
