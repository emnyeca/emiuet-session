# Roadmap

This document outlines the planned phases for the Emiuet Session project.  The roadmap is high level and subject to change as the project evolves.
このドキュメントはEmiuet Sessionプロジェクトの予定フェーズを示します。計画は大まかであり、プロジェクトの進行に応じて変更される可能性があります。

## Phase 1 – Basic Prototype

Status: in progress. Initial firmware, breadboard wiring notes, experiment log, and KiCad testboard project have been added.

- Firmware: `platformio.ini`, `src/`, `include/`
- Wiring and bring-up: `docs/phase1_breadboard.md`
- Experiment results: `docs/experiments/phase1_results.md`
- KiCad testboard project: `kicad/phase1-testboard/`

- Set up the Teensy development environment using PlatformIO and Visual Studio Code.
- Implement scanning for 16 (largest) analogue keys and basic debouncing.
- Implement fixed song data and manually step through positions.
- Output MIDI over USB and TRS‑A with simple CC messages to verify timing and latency.
- Document the experiment results to inform later design decisions.

- PlatformIOとVisual Studio Codeを使用してTeensyの開発環境を構築します。
- アナログキー16個(最大構成)のスキャンと簡易デバウンスを実装します。
- 固定楽曲データを用意し、手動で曲の位置を進めます。
- USBおよびTRS‑A経由で簡単なCCメッセージを送信し、タイミングとレイテンシを検証します。
- 実験結果を記録し、後続の設計判断に反映させます。

## Phase 2 – Local Pitch Collection and User Interface

- Develop the Local Pitch Collection (LPC) engine that derives playable notes from the current chord context.
- Add a small OLED display to show the current song, section, bar and chord, along with the active LPC.
- Implement navigation controls (encoder or buttons) to move forward or backward through the song.
- Integrate the LPC engine with the key scanner so that pressing a key sends the appropriate note or CC for the current context.
- Begin adding a lightweight synthesizer using the Teensy Audio Library to enable standalone sound generation.

- 現在の和声コンテキストから演奏可能な音を導出するLocal Pitch Collection (LPC) エンジンを開発します。
- 小型OLEDディスプレイを追加し、現在の曲、セクション、小節、コード、およびアクティブなLPCを表示します。
- エンコーダまたはボタンで曲の前後に移動できるナビゲーション機能を実装します。
- LPCエンジンとキー読み取りを統合し、押したキーが現在コンテキストに合わせたノートまたはCCを送信するようにします。
- 単体動作用にTeensy Audio Libraryを使用した軽量シンセサイザーの実装を開始します。

## Phase 3 – Changes Import and Presets

- Implement loading of song data exported from Changes, including structure and chord progressions.
- Support multiple songs and set lists with selection via the UI.
- Add presets for LPC mapping, velocity curves and performance surface behaviour.
- Refine the internal synthesiser with multiple voices and basic effects.
- Add program change and additional control messages to integrate with external instruments.

- 楽曲構造とコード進行を含むChangesからの楽曲データ読み込みを実装します。
- UIから複数の曲やセットリストを選択できるようにします。
- LPCマッピング、ベロシティカーブ、演奏面の挙動に関するプリセットを追加します。
- 内蔵シンセサイザーを複数ボイスと基本エフェクトで改良します。
- 外部機器との統合のためにProgram Changeや追加のコントロールメッセージを追加します。

## Phase 4 – Connectivity and Hardware Refinement

- Add a secondary microcontroller (e.g. ESP32) for wireless configuration via smartphone or web browser.
- Design a custom PCB with integrated analogue sensors (e.g. hall‑effect switches) and audio output circuitry.
- Improve power management and add battery support for portable use.
- Finalise enclosure design, focusing on ergonomics and performance usability.
- Conduct extended field testing in live session environments and iterate on hardware and firmware based on feedback.

- スマートフォンやウェブブラウザから設定できるように、無線設定用のサブMCU（例えばESP32）を追加します。
- アナログセンサー（例: Hall‑effectスイッチ）とオーディオ出力回路を統合したカスタムPCBを設計します。
- 電源管理を改善し、携帯利用のためのバッテリーサポートを追加します。
- 人間工学と操作性に焦点を当てた筐体設計を完成させます。
- ライブセッション環境で長期テストを行い、ハードウェアとファームウェアをフィードバックに基づいて反復改善します。
