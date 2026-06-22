# Phase A — Bill of Materials / 部品表

Development bench BOM. Quantities are for one bench rig, not for production.
これは開発ベンチ用の部品表です。量産用ではありません。

| # | Item | Qty | Notes |
|---|---|---:|---|
| 1 | Teensy 4.1 | 1 | main MCU, 3.3 V logic, onboard microSD + USB |
| 2 | Tact switches / temporary key switches | 16 | performance keys (matrix); replaceable later |
| 3 | Diodes 1N4148 (or equivalent) | 16 | one per key, anti-ghosting |
| 4 | Push rotary encoder (EC11-style) | 1 | A / B / push |
| 5a | 128×64 I2C OLED | 1 | display option A |
| 5b | 2-inch SPI LCD + EC11 module | 1 | display option B (alternative to 5a) |
| 6 | Universal board / breadboard / jumper wires | — | wiring substrate (see wiring notes) |
| 7 | microSD card | 1 | used in the Teensy 4.1 onboard slot |
| 8 | Logic analyzer | 0–1 | **optional**, for debugging I2C/SPI/matrix timing |

## Notes / 補足

- Item **5a or 5b** — choose one display option per bench session.
- **Hall-effect keys are NOT part of Phase A.** They are deferred to a later
  evaluation phase. The input layer is kept replaceable so that switching to
  Hall-effect sensing later does not require redesigning the performance logic.
- **ホールエフェクトキーは Phase A の対象外** です。後段の評価フェーズに延期します。
  入力層は差し替え可能に保ち、後でホールエフェクト方式へ移行しても演奏ロジックを作り直さずに済むようにします。
- No production parts (final connectors, enclosure hardware, production PCB) are
  listed here. See the phase plan in [`../README.md`](../README.md).
