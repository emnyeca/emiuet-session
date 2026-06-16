# Emiuet Session R&D アーキテクチャ

## なぜ存在するか

Emiuet Session は Emiuet の mini 版です。フルサイズのギター指板を再現するもの
ではなく、初心者が**少ないキー（8キー）**で、コード進行に追従しながらジャズ的な
即興を楽しむための小型演奏機です。

このドキュメントは、追加した **R&D core / Performance Model / Desktop harness** の
構造を説明します。既存の Phase 1（Teensy firmware）はそのまま残し、その横に GUI /
Arduino / MIDI ライブラリに依存しない演奏ロジックを Python で実装しました。R&D
レイヤーはデスクトップで実行・テストでき、後で firmware へ素直に移植できる形で音楽
ロジックを試作します。C++（Teensy / ESP32）への移植は、この構造をなぞる**後続
フェーズ**です。

## 責務分離（EUB Changes と Emiuet Session）

Emiuet Session は Changes の和声解析資産を**引き継ぎ**ますが、Changes のアプリや
UI を**埋め込みません**。

```
EUB Changes (既存, Python)             Emiuet Session (このリポジトリ)
--------------------------------      ---------------------------------------
- iReal Pro / song-form import        Model Builder:
- song normalisation                    - Song + HarmonicAnalysis を読む
- chord analysis                        - 8-slot Performance Model を構築
- LPC / scale candidates / priority     - step 間を voice-lead する
- chord tone / tension / colour info    - chord を manual segment にまとめる
        |                             Runtime (EmiuetCore):
        | export (HarmonicAnalysis)     - segment/step 状態, tempo timing
        v                               - 8 keys -> notes, register, approach
  HarmonicAnalysis model  ----------->  - note lifecycle, panic
                                        - 抽象 MIDI + DisplayState を返す
```

Changes は*理論*を計算し、Emiuet Session はそれを*演奏面*に変えて鳴らします。この
境界を保つことで Changes を独立に発展させられます。

## レイヤー構成（移植性のルール）

```
emiuet_session/
  core/      純粋な型 + helper   (GUI / MIDI library / platform I/O なし)
  model/     Song / Analysis / PerformanceModel + builder (layout, meter)
  runtime/   EmiuetCore.process(InputFrame) -> OutputFrame
  fixtures/  組み込みの sample song / analysis
apps/
  desktop_debug/   CLI harness（adapter であって core ではない）
tests/       pytest
docs/        本ドキュメント群
```

**core のルール:** `core/` / `model/` / `runtime/` は、GUI ツールキット・MIDI
ライブラリ・Arduino API・platform 固有 I/O を import してはいけません。engine は
抽象 `MidiEvent` と `DisplayState` を**返す**だけで、adapter がそれを変換します。
これにより同じロジックがデスクトップでも（C++ 移植後の）Teensy/ESP32 でも成立します。

## frame ループ

engine は 1 frame ずつ駆動します。

```
output = core.process(input_frame)
```

- `InputFrame` — key の press/release edge、register/approach/segment コマンド、
  tempo、profile、panic、現在時刻。held key 状態は engine が保持するので、adapter は
  edge を報告するだけです。
- `OutputFrame` — 出力すべき抽象 MIDI イベント + `DisplayState` のスナップショット。

## 主要な設計判断（非自明なもの）

- **固定オクターブではなく register shift。** 8 キーしかないため ±12 は跳躍が
  大きすぎることが多い。step サイズを選べる（Octave / FifthSlide / FourthSlide /
  CustomSemitone）。物理ボタンは Oct+/Oct- でも、ソフトは 12 を前提にしない。
  `core/register_shift.py` 参照。
- **Manual segment advance。** Next 1 回で音楽的に妥当な単位（*segment*）を進み、その
  内部の chord change（*step*）は tempo に従って自動進行する。速いテンポでも手動操作を
  ~1〜2 秒に保つ。`docs/segment_policy.md` 参照。
- **8-slot layout と voicing de-dup。** 偶数キーに core、奇数キーに colour/tension を
  置き、step 間で voice-lead しつつ、決定的な slot voicing 重複除去を行う。
  `docs/emiuet_performance_model.md` 参照。
- **安全な note lifecycle。** held note は release まで発音時の音高を保ち、layout/segment
  変更で再調律・再発音しない。panic は全て止める。これらは test で守る。

## firmware 移植計画

この Python が reference 実装です。C++ 移植は同じ構成（`include/emiuet/core`,
`src/core` …）をなぞります: `process()` のシグネチャ、抽象 `MidiEvent` モデル、
register-shift / approach / layout の policy、note lifecycle のルール。既存 Phase 1
firmware（`src/main.cpp`, `KeyScanner`, `MidiEngine`, `SongData`, `platformio.ini`）は
無変更で build 可能なままで、このレイヤーが成熟する間は検証済みのハードウェア I/O
bring-up として残ります。
