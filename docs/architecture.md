# Architecture

## System overview

```
Changes
    ↓
Song model
    ↓
Position engine
    ↓
Chord context
    ↓
Local Pitch Collection engine
    ↓
Performance engine
    ↓
Synth engine / MIDI output
```

## Modules

- **Song manager:** Loads and stores song definitions and metadata.
- **Position manager:** Tracks the current bar and beat and handles navigation.
- **LPC engine:** Derives Local Pitch Collections from chords.
- **Key scanner:** Reads analog sensors, applies filtering and detects note events.
- **Synth engine:** Generates audio on the Teensy via the Audio Library.
- **MIDI engine:** Formats and sends MIDI note and control messages.
- **UI engine:** Drives the display, encoders, LEDs and user interaction.

- **Song manager:** 楽曲定義とメタデータを読み込み保持します。
- **Position manager:** 現在の小節と拍を追跡し、ナビゲーションを処理します。
- **LPC engine:** 和音からLocal Pitch Collectionを導出します。
- **Key scanner:** アナログセンサーを読み取り、フィルタリングとノートイベント検出を行います。
- **Synth engine:** TeensyのAudio Libraryを用いてオーディオを生成します。
- **MIDI engine:** ノートとコントロールメッセージをフォーマットして送信します。
- **UI engine:** ディスプレイ、エンコーダ、LEDおよびユーザーインタラクションを制御します。

## Data flow

1. The user selects a song.
2. The song manager loads its structure and chords.
3. The position manager sets the bar counter to the start.
4. During each processing frame:
   - The key scanner reads sensors and detects key events.
   - The LPC engine generates a list of playable notes based on the current chord.
   - The performance engine maps sensor events to note numbers and velocities.
   - The synth engine plays the notes and/or the MIDI engine sends messages.
   - The UI engine updates the display and LEDs.

   1. ユーザーが曲を選択します。
2. Song managerが構造とコードを読み込みます。
3. Position managerが小節カウンターを曲の頭に設定します。
4. 各処理フレームで次のステップを実行します：
   - Key scannerがセンサーを読み取り、ノートイベントを検出します。
   - LPC engineが現在のコードから演奏可能な音のリストを生成します。
   - Performance engineがセンサーイベントをノート番号とベロシティにマッピングします。
   - Synth engineがノートを再生し、必要に応じてMIDI engineがメッセージを送信します。
   - UI engineがディスプレイとLEDを更新します。
