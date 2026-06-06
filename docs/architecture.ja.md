# アーキテクチャ

## システム概要

```
Changes
    ↓
Song model
    ↓
Position engine
    ↓
Chord context
    ↓
Local Pitch Collection engine
    ↓
Performance engine
    ↓
Synth engine / MIDI output
```

## モジュール

- **Song manager:** 楽曲定義とメタデータを読み込み保持します。
- **Position manager:** 現在の小節と拍を追跡し、ナビゲーションを処理します。
- **LPC engine:** 和音からLocal Pitch Collectionを導出します。
- **Key scanner:** アナログセンサーを読み取り、フィルタリングとノートイベント検出を行います。
- **Synth engine:** TeensyのAudio Libraryを用いてオーディオを生成します。
- **MIDI engine:** ノートとコントロールメッセージをフォーマットして送信します。
- **UI engine:** ディスプレイ、エンコーダ、LEDおよびユーザーインタラクションを制御します。

## データフロー

1. ユーザーが曲を選択します。
2. Song managerが構造とコードを読み込みます。
3. Position managerが小節カウンターを曲の頭に設定します。
4. 各処理フレームで次のステップを実行します：
   - Key scannerがセンサーを読み取り、ノートイベントを検出します。
   - LPC engineが現在のコードから演奏可能な音のリストを生成します。
   - Performance engineがセンサーイベントをノート番号とベロシティにマッピングします。
   - Synth engineがノートを再生し、必要に応じてMIDI engineがメッセージを送信します。
   - UI engineがディスプレイとLEDを更新します。
