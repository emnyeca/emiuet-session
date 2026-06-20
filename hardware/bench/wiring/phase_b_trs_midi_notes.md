# Phase B — TRS MIDI Notes (Placeholder) / TRS MIDI メモ（プレースホルダ）

> **Phase B placeholder only.** No circuit is built in Phase A.
> **Phase B 用のプレースホルダのみ。** Phase A では回路を作りません。

## Intent / 方針

- TRS MIDI IN/OUT will use **Serial1**, on Teensy 4.1 pins **0 (RX1)** and **1 (TX1)**.
  TRS MIDI IN/OUT は **Serial1**（Teensy 4.1 ピン **0 = RX1 / 1 = TX1**）を使用します。
- These pins are **reserved** in Phase A and must be left unconnected until Phase B.
  これらのピンは Phase A では **予約** であり、Phase B まで未接続にします。

## Safety constraint / 安全上の制約

- **MIDI IN must not drive the Teensy RX pin with 5 V.** Use a proper opto-isolated
  (or 3.3 V-safe) MIDI input front end so the RX pin only ever sees ≤ 3.3 V.
  Teensy 4.1 GPIO is **not 5 V tolerant**.
  **MIDI IN で Teensy の RX を 5V で駆動しないこと。** RX が 3.3V を超えないよう、
  オプトカプラ絶縁（または 3.3V 対応）の MIDI 入力フロントエンドを使用します。

## Deferred / 延期事項

- The detailed TRS Type-A circuit (driver/current-limiting for OUT, opto-isolator
  for IN, jack tip/ring/sleeve assignment) is **intentionally deferred** to Phase B.
  詳細な TRS Type-A 回路は **意図的に Phase B へ延期** します。
- See [`../../../docs/phase1_breadboard.md`](../../../docs/phase1_breadboard.md) for the
  earlier TRS Type-A note from the analog breadboard prototype.
