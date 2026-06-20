# Phase A — Pinout / ピン配置

Teensy 4.1 development bench, Phase A.
All signals are **3.3 V**. Teensy 4.1 GPIO is **not 5 V tolerant**.

すべての信号は **3.3V** です。Teensy 4.1 の GPIO は **5V トレラントではありません**。

## Key matrix (4×4) / キーマトリクス

| Function | Teensy 4.1 pin | Direction | Notes |
|---|---:|---|---|
| Key Row 0 | 24 | output (scan) | one diode per key for anti-ghosting |
| Key Row 1 | 25 | output (scan) | |
| Key Row 2 | 26 | output (scan) | |
| Key Row 3 | 27 | output (scan) | |
| Key Col 0 | 28 | input (`INPUT_PULLUP`) | reads LOW when a key in that column is pressed |
| Key Col 1 | 29 | input (`INPUT_PULLUP`) | |
| Key Col 2 | 30 | input (`INPUT_PULLUP`) | |
| Key Col 3 | 31 | input (`INPUT_PULLUP`) | |

16 keys = 4 rows × 4 columns, each key with one series diode (1N4148 or equiv.).

### Scan policy (Phase A) / スキャン方針

- Columns use **`INPUT_PULLUP`** (idle HIGH).
- Rows are scanned **one row at a time, driven LOW**; all other rows stay inactive.
- A pressed key is read on its **column as LOW** (active-low).
- This assumption must stay consistent with the **diode direction** described in
  [`../atopile/src/bench_key_matrix_4x4.ato`](../atopile/src/bench_key_matrix_4x4.ato)
  (per-key `row -> switch -> diode (anode -> cathode) -> col`).

- Columns は **`INPUT_PULLUP`**（待機時 HIGH）を使用します。
- Rows は **1 行ずつ LOW に駆動** して scan します。
- 押された key は **column 側で LOW** として読まれます（アクティブ LOW）。
- この前提は [`../atopile/src/bench_key_matrix_4x4.ato`](../atopile/src/bench_key_matrix_4x4.ato)
  に記述された **diode direction** と整合させてください。

## Rotary encoder (push) / ロータリーエンコーダ

| Function | Teensy 4.1 pin | Notes |
|---|---:|---|
| Encoder A | 36 | quadrature A |
| Encoder B | 37 | quadrature B |
| Encoder Push | 38 | momentary push switch |

## Display option A — 128×64 I2C OLED / I2C OLED

| Function | Teensy 4.1 pin | Notes |
|---|---:|---|
| SDA | 18 | I2C data (Wire) |
| SCL | 19 | I2C clock (Wire) |
| VCC | 3.3 V | — |
| GND | GND | — |

## Display option B — 2-inch SPI LCD + EC11 module / SPI LCD

| Function | Teensy 4.1 pin | Notes |
|---|---:|---|
| SCK / SCL | 13 | SPI clock |
| MOSI / SDA | 11 | SPI data |
| CS | 10 | chip select (if available) |
| RES | 32 | reset |
| DC | 33 | data/command |
| BLK | 34 | backlight enable |
| VCC | 3.3 V | — |
| GND | GND | — |

> Option A and Option B are **alternatives**. Use one display at a time on the bench.
> オプション A と B は **択一** です。ベンチでは同時に 1 つの表示器を使用します。

## Power / 電源

| Function | Teensy 4.1 pin | Notes |
|---|---:|---|
| Logic supply | 3.3 V | all peripherals run at 3.3 V |
| Ground | GND | common ground |

## Onboard resources / オンボード機能

- **microSD**: use the **Teensy 4.1 onboard microSD slot only** (no external SD wiring in Phase A).
- **USB MIDI**: use the **Teensy onboard USB** (USB MIDI is the primary MIDI path in Phase A).

## Reserved for Phase B (do not wire now) / Phase B 予約（今は配線しない）

| Function | Teensy 4.1 pin | Notes |
|---|---:|---|
| MIDI RX | 0 / RX1 | TRS MIDI IN — reserved, Phase B |
| MIDI TX | 1 / TX1 | TRS MIDI OUT — reserved, Phase B |

## Reserved / avoid for Phase A / Phase A では避けるピン

Audio Shield critical pins — **do not use in Phase A** (Phase D): **7, 8, 20, 21, 23**.
No Audio Shield wiring is added in Phase A.
