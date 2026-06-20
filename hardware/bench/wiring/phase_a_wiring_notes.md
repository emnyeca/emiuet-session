# Phase A — Wiring Notes / 配線メモ

Practical guidance for assembling the Phase A bench.
Phase A ベンチを組むときの実務メモです。

## Electrical safety / 電気的注意

- **Use 3.3 V logic only.** すべての論理は 3.3V のみ。
- **Do not connect any 5 V signal to a Teensy GPIO pin.** Teensy 4.1 GPIO is
  **not 5 V tolerant** and 5 V will damage it.
  5V 信号を Teensy の GPIO に接続しないでください。Teensy 4.1 の GPIO は **5V トレラントではありません**。

## Key matrix / キーマトリクス

- **One diode per key** (1N4148 or equivalent) for anti-ghosting.
  1 キーにつき 1 個のダイオード（アンチゴースト用）。
- Keep matrix wiring **short** to reduce noise and crosstalk.
  マトリクス配線は **短く** 保つ。
- **Prefer a universal (perf) board for the 16-key section.** It is mechanically
  stable and survives repeated key presses better than a breadboard.
  16 キー部は **ユニバーサル基板を推奨**。
- Keep the orientation of all key diodes consistent (see the atopile scaffold and
  firmware for the assumed scan direction).

## Breadboard usage / ブレッドボードの使用

- A breadboard is **acceptable only for early OLED / encoder tests**, where
  connections are few and forces are low.
  ブレッドボードは **OLED / エンコーダの初期テストのみ** 許容。
- Do not rely on a breadboard for the 16-key matrix long term.

## Replaceability / 差し替え性

- **Keep the key input board replaceable.** The performance keys are on a
  separate, swappable section so that a later Hall-effect input board can replace
  the scanner layer **without** changing the performance logic.
  **キー入力ボードは差し替え可能に保つ。** 後でホールエフェクト入力基板に交換しても、
  スキャナ層だけを置き換えて演奏ロジックは変更しないで済むようにする。

## Onboard resources / オンボード機能

- Use the **Teensy 4.1 onboard microSD slot** — no external SD wiring in Phase A.
- **USB MIDI** uses the Teensy onboard USB — it is the primary MIDI path in Phase A.

## Reserved pins / 予約ピン

- Pins **0 / 1 (Serial1 RX/TX)** are reserved for **TRS MIDI (Phase B)** — leave free.
- Audio Shield critical pins **7, 8, 20, 21, 23** — leave free in Phase A (Phase D).
