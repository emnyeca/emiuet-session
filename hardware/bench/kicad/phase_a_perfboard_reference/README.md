# Phase A Perfboard Reference (KiCad) / Phase A ユニバーサル基板リファレンス

A **hand-wiring reference schematic** for the Emiuet Session bench, Phase A.
Emiuet Session ベンチ Phase A 用の **手配線リファレンス回路図** です。

> ⚠️ This is **NOT a production PCB**. It exists to help you wire a Teensy 4.1 +
> 16-key matrix + encoder + display on a **universal (perf) board / jumper wires**
> for the Phase A smoke test. There is no board layout, no footprints assigned, no
> JLCPCB BOM/CPL, no enclosure, and no final dimensions.
>
> ⚠️ これは **完成・量産 PCB ではありません**。Phase A の smoke test 用に、
> Teensy 4.1 + 16 キーマトリクス + エンコーダ + ディスプレイを **ユニバーサル基板 /
> ジャンパ線** で手配線するための参照です。基板レイアウト・フットプリント・JLCPCB
> BOM/CPL・筐体・最終寸法は含みません。

## What it is for / 位置づけ

- This schematic is **authoritative only for Phase A hand wiring**, not for final
  hardware design. 本回路図は **Phase A の手配線についてのみ** 基準であり、最終ハード
  設計の基準ではありません。
- Use it **together with**:
  - [`../../wiring/phase_a_pinout.md`](../../wiring/phase_a_pinout.md) — pin table & scan policy
  - [`../../wiring/phase_a_wiring_notes.md`](../../wiring/phase_a_wiring_notes.md) — assembly notes
  - [`../../atopile/`](../../atopile/) — machine-readable wiring-intent scaffold

## How to open / 開き方

- Built and validated with **KiCad 10.0.3** (schematic format `version 20250114`).
- Open `phase_a_perfboard_reference.kicad_pro` in KiCad, then open the schematic
  (eeschema). `phase_a_perfboard_reference.kicad_pro` を KiCad で開いてください。

## What the schematic contains / 含まれるもの

- `U1` — generic **Teensy 4.1** header (box symbol, explicit pin labels, **no
  footprint**; not a verified Teensy footprint).
- **4×4 digital key matrix**: 16 switches `SW_R0C0..SW_R3C3`, 16 diodes
  `D_R0C0..D_R3C3`, nets `KEY_ROW0..3` / `KEY_COL0..3`.
- `J_ENC` — EC11 push encoder (A / B / push + GND).
- `J_OLED` — I2C OLED connector (option A).
- `J_LCD` — SPI LCD connector (option B).
- `+3V3` / `GND` nets.
- Teensy pins **0/1 (Serial1 RX1/TX1)** shown only as **reserved labels**
  (`MIDI_RX1_RSVD` / `MIDI_TX1_RSVD`) for future TRS MIDI (Phase B).

Connections are expressed with **net labels** on each pin (matrix junctions wired
pin-to-pin). This keeps the sheet readable for hand wiring: every pin shows the net
it belongs to. 接続は各ピンの **ネットラベル** で表現しています（マトリクスの接合は
ピン同士で結線）。配線時にどのピンがどのネットかが一目で分かります。

## Key matrix scan assumption / キーマトリクスのスキャン前提

- Columns use **`INPUT_PULLUP`** (idle HIGH).
- Rows are scanned **one row LOW at a time**.
- A pressed key reads **LOW on its column**.
- Diode orientation in this schematic: **anode → COLUMN, cathode → ROW**, consistent
  with the above. ダイオードは **アノード→COLUMN / カソード→ROW**。

## Before soldering — verify / 半田付け前に確認

1. **Diode orientation** matches the firmware scanner (see scan assumption above).
   ダイオードの向きが firmware scanner と一致していること。
2. **Connector pin order** of your actual OLED / LCD / encoder module — pin order
   **varies by module**; the connectors here are generic. 実際のモジュールのピン順は
   **製品ごとに異なる** ため要確認。
3. **Display module voltage** — OLED / LCD `VCC` must be **3.3 V** unless the module
   is explicitly verified 5 V-safe. Teensy 4.1 GPIO is **NOT 5 V tolerant**; never
   connect 5 V to a Teensy GPIO. ディスプレイの `VCC` は原則 **3.3V**。

## Not included (by design) / 意図的に含めないもの

TRS MIDI circuit (jack / optocoupler / transistor / current-loop) · Audio Shield
wiring · Hall-effect key circuit · CD74HC4067 analog key mux · battery / power
management · final PCB dimensions · JLCPCB BOM/CPL · production PCB assumptions.

## ERC notes / ERC について

ERC is intentionally not "zero": a few **warnings are expected** for a reference
sheet — the reserved `MIDI_*_RSVD` labels are single-pin (reserved on purpose), and
the custom `EmiuetBench:Teensy4_1_Bench` symbol is embedded rather than in a global
library. There are **no electrical errors**. これらの warning は参照回路図として
**想定内** です（予約ラベルと埋め込みカスタムシンボル）。

## Regeneration / 再生成

This schematic was authored programmatically for coordinate accuracy by
[`_gen_sch.py`](_gen_sch.py) (one-shot; reads standard symbols from the local KiCad
10 libraries). The `.kicad_sch` / `.kicad_pro` are normal KiCad files and can be
edited by hand from here on — the script is kept only for transparent regeneration.
本回路図は座標精度のため [`_gen_sch.py`](_gen_sch.py) で生成しました。以降は通常の
KiCad ファイルとして手編集できます。
