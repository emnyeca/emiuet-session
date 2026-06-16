# CCP16BK Mapping

## 概要 (JA)

CCP16BK は16パッドのMIDIパッドコントローラーで、各パッドは Note / CC / Program、
Momentary / Toggle を本体で設定できます。Emiuet Session R&D では **Note +
Momentary** を基本推奨とし、16パッドを **8演奏キー + 8制御キー**として使います。
パッドのMIDI値は本体設定や初期値で異なり得るため、`ccp16.json` は「初期仮profile」
です。実機の RAW ログで note 番号を確認し、profile を修正してください。

## Why CCP16 for R&D

It is a compact 16-pad controller (USB-B, BLE MIDI, TRS Type-A MIDI I/O) whose
pads are freely assignable. Sixteen pads map cleanly onto Emiuet Session's
8 performance keys plus 8 control keys, letting us play the R&D core on real
hardware before any firmware work.

## Recommended pad roles

Emiuet Session's surface is two rows of four (TwoRowCoreColor):

```
□ □ □ □     colour line  (slots 1 3 5 7)
■ ■ ■ ■     core line    (slots 0 2 4 6)
```

Suggested 4x4 pad layout (top two rows = performance, bottom two = control):

```
[colour s1] [colour s3] [colour s5] [colour s7]      <- play
[core  s0 ] [core  s2 ] [core  s4 ] [core  s6 ]      <- play

[prev_seg ] [next_seg ] [reg_down ] [reg_up   ]      <- control
[approach-] [approach+] [panic    ] [reg_reset]      <- control
```

(Use `profile_cycle` instead of `register_reset` on the last control pad if you
prefer; just edit the profile.)

## Initial profile (`controller_profiles/ccp16.json`)

The bundled profile assumes channel 1 and notes 36–51:

| Notes | Role |
|---|---|
| 36 37 38 39 | core line: slots 0, 2, 4, 6 |
| 40 41 42 43 | colour line: slots 1, 3, 5, 7 |
| 44 45 | previous_segment, next_segment |
| 46 47 | register_down, register_up |
| 48 49 | approach_minus, approach_plus |
| 50 51 | panic, register_reset |

These note numbers are an **assumption**. CCP16 pad values depend on the unit's
settings, so verify before relying on them.

## Setting up the CCP16

1. Set the pads you will use to **Note** mode (not CC, not Program).
2. Set them to **Momentary** (not Toggle) so each press sends Note On and each
   release sends Note Off. Toggle mode leaves notes stuck on.
3. Put all pads on the **same MIDI channel** and match the profile's
   `midi_channel` (or omit `midi_channel` to accept any).
4. Connect via **USB** for R&D testing.

## Verifying note numbers with the raw log

1. Run the harness against the CCP16 (see midi_controller_testing.md).
2. Press each pad and read the `RAW` line, e.g.
   `RAW : note_on ch=1 note=38 velocity=120`.
3. If a pad's note differs from the table, edit `ccp16.json` so that note maps to
   the intended slot/command, and re-run. No code changes are needed.

Because everything is profile-driven, the same harness works with any other
16-pad controller by pointing `--profile` at a different JSON (see
`generic_16pad.json`, which routes the 8 control keys through CC buttons).
