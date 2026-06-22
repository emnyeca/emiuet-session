# Emiuet Session — Bench Phase A / ベンチ Phase A

This document summarizes the rationale for the Teensy 4.1 development bench,
Phase A. The hardware artifacts live under
[`hardware/bench/`](../../hardware/bench/).

このドキュメントは Teensy 4.1 開発ベンチ Phase A の設計意図をまとめます。
ハードウェア成果物は [`hardware/bench/`](../../hardware/bench/) 以下にあります。

## Purpose / 目的

Phase A exists to validate **Emiuet Session firmware on real Teensy 4.1 hardware**
with a minimal, replaceable rig — not to produce a finished instrument. It covers:

- Teensy 4.1 firmware bring-up
- 16 performance keys (initial 4×4 matrix)
- one push rotary encoder
- a display (I2C OLED or SPI LCD)
- the onboard microSD slot
- USB MIDI over the onboard USB

Phase A は **実機 Teensy 4.1 上でファームウェアを検証する** ための最小・差し替え可能なリグです。
完成楽器を作る段階ではありません。

## Why tact switches are acceptable first / まずタクトスイッチで良い理由

Tact (or temporary) switches are cheap, available, and trivial to wire as a digital
matrix. They let firmware bring-up (scanning, debounce, note mapping, MIDI output)
proceed immediately, **before** committing to a final, costlier, alignment-sensitive
key technology. The key section is built to be replaceable, so nothing about this
early choice locks in the final feel.

タクトスイッチは安価で入手しやすく、デジタルマトリクスとして簡単に配線できます。
最終的なキー方式を決める前に、スキャン・デバウンス・ノートマッピング・MIDI 出力の
立ち上げをすぐ進められます。キー部は差し替え可能なので、この初期選択は最終仕様を縛りません。

## Why Hall-effect sensing is deferred / ホールエフェクトを延期する理由

Hall-effect (analog/magnetic) keys give smooth, continuous travel but require
precise magnet alignment, per-key calibration, and more complex analog acquisition.
Bringing that complexity in before the firmware control flow is proven would slow
the bench down for no immediate benefit. Phase A proves the surrounding system; the
analog key front end can be evaluated later **as a replaceable input layer**.

ホールエフェクト方式は滑らかな連続ストロークを得られますが、磁石の位置合わせ・キーごとの
キャリブレーション・複雑なアナログ取得が必要です。ファームウェアの制御フローを実証する前に
その複雑さを持ち込むと、ベンチの進行を遅くするだけです。Phase A で周辺システムを実証し、
アナログキー入力は後で **差し替え可能な入力層** として評価します。

## Why KeyScanner should be abstracted / KeyScanner を抽象化する理由

Because the input technology will change (tact matrix → possibly Hall-effect), the
**KeyScanner** layer should expose a stable interface (key index → press/value
events) and hide how keys are physically read. Performance semantics (which note,
how it is voiced, chord/song logic) must live **above** the scanner, so swapping the
input layer does not touch the performance logic. The atopile scaffold mirrors this:
the wiring layer carries no performance-key semantics.

入力技術は変化する（タクトマトリクス → 将来ホールエフェクト）ため、**KeyScanner** 層は
安定したインターフェース（キー番号 → 押下/値イベント）を公開し、物理的な読み取り方法を隠すべきです。
演奏の意味（どのノートか、どう発音するか、コード/ソングのロジック）はスキャナの **上位** に置き、
入力層を差し替えても演奏ロジックに触れないようにします。

## Why USB MIDI is first / USB MIDI を先行する理由

The Teensy 4.1 provides USB MIDI on the onboard USB with no extra circuitry. It is
the fastest, most observable path to confirm that key/encoder events produce correct
MIDI, before any TRS hardware exists. It also needs no level-shifting or isolation,
keeping Phase A electrically simple and safe.

Teensy 4.1 はオンボード USB で追加回路なしに USB MIDI を提供します。TRS ハードウェアが無くても、
キー/エンコーダのイベントが正しい MIDI を生成することを最速・最も観測しやすく確認できます。
レベルシフトや絶縁も不要で、Phase A を電気的に単純・安全に保てます。

## Why TRS MIDI and Audio Shield are deferred / TRS MIDI と Audio Shield を延期する理由

- **TRS MIDI (Phase B):** requires correct 3.3 V-safe driver/opto-isolated front ends.
  Pins 0/1 (Serial1) are reserved now; the circuit is deferred so Phase A stays simple
  and avoids any risk of 5 V reaching a non-5 V-tolerant GPIO.
- **Audio Shield / I2S DAC (Phase D):** adds audio routing and claims several pins
  (7, 8, 20, 21, 23). It is unrelated to validating the control surface and MIDI path,
  so it is not routed in Phase A.

- **TRS MIDI（Phase B）:** 3.3V 安全なドライバ／オプト絶縁フロントエンドが必要です。今はピン 0/1
  （Serial1）を予約し、回路は延期して Phase A を単純に保ち、5V が非トレラント GPIO に届く危険を避けます。
- **Audio Shield / I2S DAC（Phase D）:** 音声経路を追加し複数ピン（7, 8, 20, 21, 23）を占有します。
  操作面と MIDI 経路の検証とは無関係なので、Phase A では配線しません。
