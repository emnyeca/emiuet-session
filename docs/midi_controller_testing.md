# MIDI Controller Testing

## 概要 (JA)

PCキーボードのCLIだけでなく、市販のMIDIパッドコントローラーで Emiuet Session
R&D Core を演奏テストするための adapter とハーネスです。MIDI入力は
`apps/desktop_debug` 側の **adapter** として実装し、**core は MIDI ライブラリに
依存しません**。`mido` / `python-rtmidi` は optional dependency で、実ポートを開く
ときだけ遅延importされます。未インストールでも pytest と既存CLIは動きます。

## Purpose

Map a hardware controller's pads/buttons to the engine's 8 performance slots and
control commands, so the R&D core can be played for real. The mapping is data
(a JSON profile), so swapping controllers is a profile change, not code.

## Dependencies

The core has no dependencies. The controller harness needs the optional extras:

```sh
pip install -r requirements-midi.txt      # mido + python-rtmidi
# or: pip install -e ".[midi]"
```

If they are not installed, `--list-ports` and live mode print a clear install
hint; the `--self-test` mode and all unit tests still run.

## Listing ports

```sh
python -m apps.desktop_debug.midi_controller_harness --list-ports
```

## Running the harness

```sh
python -m apps.desktop_debug.midi_controller_harness \
  --midi-in "MIDI PAD-01" \
  --profile apps/desktop_debug/controller_profiles/ccp16.json
```

- `--midi-in` accepts an exact port name, a case-insensitive substring, or an
  index from `--list-ports`.
- `--layout-orientation two-row|alternating` chooses the display.
- `--self-test` feeds synthetic messages and needs no hardware -- use it to see
  the mapping + engine output and to sanity-check a profile.

## Reading the log

Each incoming message prints:

```
RAW    : note_on ch=1 note=36 velocity=100      <- exactly what arrived
MAPPED : slot 0 press                            <- the resolved action
CORE   : NoteOn  ch1 n 60 v100                   <- abstract MIDI the engine emits
[seg 1/4 step 1/1]  Dm7 > G7    OCT+0  NORM  (two-row)
  color: .E  .G  .B  .C+1
  core : #C  #D  #F  #A
  dbg  : D Dorian prio1 retry0 lpc=[...] active=[60]
  midi : NoteOn  ch1 n 60 v100
```

`RAW` shows the channel **1-based** (mido reports 0-based internally). Use `RAW`
to discover your controller's real note/CC numbers, then edit the profile.

## Controller profile JSON

```json
{
  "name": "My controller",
  "midi_channel": 1,
  "note_mappings": {
    "36": { "type": "slot", "slot": 0 },
    "45": { "type": "command", "command": "next_segment" }
  },
  "control_mappings": {
    "21": { "type": "command", "command": "next_segment" }
  }
}
```

- `midi_channel` is 1-based; omit it to accept any channel.
- `note_mappings` keys are MIDI note numbers; `control_mappings` keys are CC
  numbers.
- Action `type` is `slot` (with `slot` 0..7) or `command`.
- Commands: `next_segment`, `previous_segment`, `register_up`, `register_down`,
  `register_reset`, `approach_plus`, `approach_minus`, `profile_cycle`, `panic`.

### Note vs CC mapping

| | Pressed | Released |
|---|---|---|
| **Note** | `note_on` velocity > 0 | `note_off`, or `note_on` velocity 0 |
| **CC** | value ≥ 64 | value < 64 |

`approach_plus` / `approach_minus` use both edges (hold to engage). All other
commands fire once on press and ignore the release edge.

## Troubleshooting

- **No ports listed** — check the cable/driver; for USB connect before launching.
  On macOS a virtual port may need the controller's own driver.
- **Bluetooth MIDI visible but no input** — pair/connect in the OS MIDI settings
  first; prefer **USB** for R&D testing (BLE specifics are out of scope here).
- **Note On arrives but no Note Off** — the pad is in **Toggle** mode; switch it
  to **Momentary** (see ccp16_mapping.md). Otherwise a note stays held.
- **Nothing happens / `(channel N ignored)`** — the controller's channel differs
  from the profile's `midi_channel`; match them or omit `midi_channel`.
- **Wrong notes trigger** — the profile's note numbers don't match the device;
  read the `RAW` log and edit the profile.
- **`velocity 0` Note On** — handled: it is treated as a Note Off (slot release).
- **Toggle/latched pads** — not assumed anywhere; use Momentary.
