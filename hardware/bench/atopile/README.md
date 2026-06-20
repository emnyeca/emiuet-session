# atopile scaffold — Emiuet Session Teensy bench (Phase A)

This is a **minimal, wiring-intent** atopile project for the Teensy 4.1 development
bench. It captures *how the Phase A bench is wired* in a machine-readable form. It is
**not** a production board and intentionally avoids footprints, part numbers, JLCPCB
BOM/CPL, and final PCB dimensions.

これは Teensy 4.1 開発ベンチの **配線意図を機械可読にした最小の** atopile プロジェクトです。
量産基板ではなく、フットプリント・型番・JLCPCB BOM/CPL・最終 PCB 寸法は意図的に含めません。

## How to build / ビルド方法

```sh
cd hardware/bench/atopile
ato build
```

> `ato` (atopile) must be installed separately. See https://atopile.io for install
> instructions. This scaffold has been confirmed to **build successfully with
> atopile `0.15.7`** (`ato build` → success). The remaining warnings are about
> unspecified footprints / parts and are **expected** for a wiring-intent-only
> scaffold — see "Version note" below.
>
> `ato`（atopile）は別途インストールが必要です。このスキャフォールドは **atopile
> `0.15.7` で `ato build` の成功を確認済み** です。残る warnings は footprint / part
> 未指定に関するもので、配線意図のみの scaffold としては **想定内** です（下記
> 「Version note」参照）。

## Version note / バージョン注意

This scaffold builds on atopile `0.15.7`. atopile's `ato.yaml` schema and import
syntax have changed across releases, so on a **different** version the build may
need small adjustments:

1. Run `ato --version`.
2. Compare [`ato.yaml`](ato.yaml) keys against your version's expected schema and
   adjust if needed (e.g. `requires-atopile` vs `ato-version`, `builds.*.entry`).
3. This scaffold uses the current `from "<file>.ato" import <Name>` import form
   (one name per line); adjust to your version's syntax if it differs.

These files deliberately stay minimal so they are easy to repair against whatever
atopile version you have installed.

## Structure / 構成

| File | Responsibility |
|---|---|
| [`src/emiuet_session_bench.ato`](src/emiuet_session_bench.ato) | Top-level bench wiring (ties everything together) |
| [`src/teensy41_header.ato`](src/teensy41_header.ato) | Generic Teensy 4.1 header / pin representation |
| [`src/bench_key_matrix_4x4.ato`](src/bench_key_matrix_4x4.ato) | 4 rows × 4 cols, 16 switches, 16 diodes |
| [`src/bench_encoder.ato`](src/bench_encoder.ato) | EC11-style encoder A / B / push |
| [`src/bench_display_i2c_oled.ato`](src/bench_display_i2c_oled.ato) | 4-pin I2C OLED connector (option A) |
| [`src/bench_display_spi_lcd.ato`](src/bench_display_spi_lcd.ato) | SPI LCD connector (option B) |
| [`src/connectors.ato`](src/connectors.ato) | Generic interfaces and 2-terminal parts |
| `layout/` | reserved for atopile layout output |

## Design intent / 設計意図

- The wiring layer carries **no performance-key semantics** (no note/voicing/chord
  meaning). It only describes how pins, switches, diodes, and connectors join.
- A future **Hall-effect input board should replace the scanner layer**, not the
  performance logic. The `bench_key_matrix_4x4` module is the swappable scanner front
  end; nothing downstream of it is encoded here.
- Pins **0/1** are reserved for **TRS MIDI (Phase B)** and are not wired here.

- 配線層には **演奏キーの意味を持たせません**（ノート/発音/コードの意味を含めない）。
- 将来のホールエフェクト入力基板は **スキャナ層を置き換える** もので、演奏ロジックは置き換えません。
- ピン **0/1** は **TRS MIDI（Phase B）** 用に予約し、ここでは配線しません。

## SPI LCD + EC11 module / SPI LCD + EC11 モジュール

The 2-inch SPI LCD (display option B) is sometimes sold as a **single physical
module that already integrates an EC11 encoder**. In this atopile scaffold, the
display pins (`bench_display_spi_lcd`) and the encoder pins (`bench_encoder`) are
still kept as **separate logical interfaces**. This separation exists so the
firmware can keep its **display driver** and **encoder scanner** independent — it
does **not** imply the two are on separate physical boards.

2-inch SPI LCD（表示オプション B）は、**EC11 エンコーダを内蔵した一体型モジュール**
として販売されている場合があります。ただし、この atopile scaffold では display pins
（`bench_display_spi_lcd`）と encoder pins（`bench_encoder`）を **別々の logical
interface** として扱います。これは firmware 側で **display driver** と **encoder
scanner** を分離するための整理であり、物理基板が別であることを意味しません。
