# Hardware notes

This document records hardware choices and recommendations for Emiuet Session prototypes.
このドキュメントはEmiuet Sessionプロトタイプのハードウェア選定と推奨事項を記録します。

## Key switches

Emiuet Session uses analog key switches to capture continuous travel or pressure.  Two approaches are considered:

- **Hall‑effect switches (magnetic).**  Each key contains a magnet and a Hall sensor on the PCB.  The sensor output reflects the magnet position.  Pros: smooth linear response, long lifespan.  Cons: requires precise alignment.
- **Force‑sensitive resistors (FSR).**  Simple resistive sensors that change resistance with pressure.  Pros: inexpensive and easy to integrate.  Cons: non‑linear response and drift over time.

Emiuet Sessionはアナログキースイッチで連続的な打鍵や圧力を取得します。以下の2つの方式を検討しています。

- **Hall‑effectスイッチ（磁気式）** – 各キーに磁石が入っており、PCB上のホールセンサーで検出します。出力は磁石の位置を反映します。利点は滑らかで線形な応答と長寿命であり、欠点は位置合わせがシビアなことです。
- **Force‑sensitive resistor (FSR)** – 押圧に応じて抵抗値が変化する簡単な抵抗式センサーです。利点は安価で統合が容易なこと、欠点は応答が非線形で経時変化があることです。

## Microcontroller

Teensy 4.x boards are the primary target.  They offer high CPU speed, fast ADC sampling, built‑in USB‑MIDI and an audio library.  Smaller Teensy models or other MCUs can be used for simpler prototypes.
主なターゲットはTeensy 4.xです。高速なCPU、迅速なADCサンプリング、USB‑MIDI内蔵、およびAudio Libraryを利用できます。より小型のTeensyや他のMCUでも単純なプロトタイプには使用可能です。

## Multiplexing

Use CD74HC4067 16‑channel analog multiplexer chips to read many sensors with few analog pins.  Connect the multiplexer output to a single ADC input and use GPIO pins to select channels.
CD74HC4067 16チャネルアナログマルチプレクサを使用して、少ないアナログピンで多数のセンサーを読み取ります。マルチプレクサの出力を単一のADC入力に接続し、GPIOピンでチャネルを選択します。

## Power and I/O

- Power via USB‑C or an internal Li‑Po battery with a charger circuit.
- TRS Type‑A MIDI output jack.
- 3.5 mm stereo audio output (optionally balanced).
- Optional headphone amplifier.

- USB‑Cまたは充電回路付きLi‑Poバッテリーで電源供給します。
- TRS Type‑A MIDI出力ジャック。
- 3.5 mmステレオ音声出力（必要に応じてバランス出力）。
- オプションのヘッドフォンアンプ。


## Enclosure

Early prototypes can use PCB.  Final versions may use aluminium or wood.  Ensure that keys are firmly mounted and that LEDs are diffused for clear feedback.
初期プロトタイプにはPCBを使用できます。最終版ではアルミや木材を用いることができます。キーをしっかり固定し、LEDは拡散して見やすくする必要があります。