# Emiuet Session
Part of the EUB (Emnyeca's Utility Build Series) project.

Emiuet Session is a standalone improvisation instrument designed for jazz sessions, machine-live performance and harmonic exploration.

## Project Status

Prototype phase.

Two parallel tracks:

**Phase 1 — Teensy breadboard prototype** (hardware input + MIDI output bring-up)

- Firmware: `platformio.ini`, `src/`, `include/`
- Breadboard wiring: `docs/phase1_breadboard.md`
- Experiment log: `docs/experiments/phase1_results.md`
- KiCad testboard project: `kicad/phase1-testboard/`

**R&D core — performance model & playable engine** (portable Python, GUI/MIDI-lib free)

- Engine + models: `emiuet_session/` · Desktop debug harness: `apps/desktop_debug/`
- Tests: `pytest` from the repo root · Demo: `python -m apps.desktop_debug --demo`
- Play it from a MIDI controller (optional `mido`): `python -m apps.desktop_debug.midi_controller_harness --self-test`
- Design docs: `docs/emiuet_session_architecture.md`,
  `docs/emiuet_performance_model.md`, `docs/segment_policy.md`,
  `docs/rd_core_desktop_harness.md`, `docs/midi_controller_testing.md`,
  `docs/midi_output_testing.md`, `docs/ccp16_mapping.md`,
  `docs/solo_mode.md`, `docs/relative_melodic_resolver.md`
- The C++ (Teensy/ESP32) port is a later phase that mirrors this structure.

## Documentation

### User Documentation

- docs/vision.md
- docs/requirements.md
- docs/glossary.md

### Developer Documentation

- docs/architecture.md
- docs/hardware.md
- docs/midi.md
- docs/roadmap.md
- docs/phase1_breadboard.md

### AI Worker Documentation

- docs/ai_worker_guidelines.ja.md

## Governance

AI contributors must follow:

- ai-governance/AI-WORKING-POLICY.md
- ai-governance/AI-WORKING-CHARTER.md

These documents take precedence over local project instructions.

## License

TBD
