# Functional requirements

## Core features

- **Load song data from Changes.**  A song definition includes structure, chords, tempo and meter.
- **Navigate the current position.**  The player can move forward or backward through the song.  A display shows the current bar and chord.
- **Display the current chord.**  The UI always indicates which chord is active.
- **Generate the Local Pitch Collection.**  For each chord the instrument calculates the set of allowed notes.
- **Map the LPC to the performance surface.**  Only notes from the LPC are playable at any moment.
- **Internal sound generation.**  A lightweight synthesizer on the hardware produces audio.
- **MIDI output.**  The device sends note and CC messages over USB and TRS MIDI.

- **Changesから楽曲データを読み込む。** 楽曲定義はChangesの仕様に基づきます。
- **現在位置をナビゲートする。** 演奏者は現在コードを前後に移動でき、ディスプレイに現在地が表示されます。
- **現在のコードを表示する。** UIは常にどのコードが有効かを示します。LPCに影響するコードが前後にあれば、それも示します。
- **Local Pitch Collectionを生成する。** 各コードに対して演奏可能な音の集合を計算します。
- **LPCを演奏面にマッピングする。** 現在のLPCに含まれる音のみが演奏可能です。
- **内部音源でのサウンド生成。** ハードウェア上の軽量シンセサイザーで音声を生成します。
- **MIDI出力。** デバイスはUSBおよびTRS MIDI経由でNoteとCCメッセージを送信します。

## Input

- 8-16 analog performance keys
- Rotary encoder for navigation
- Function buttons
- Optional footswitch input port

- アナログ性能キー8-16個
- ナビゲーション用ロータリーエンコーダ
- ファンクションボタン
- オプションのフットスイッチ入力ポート

## Output

- Internal synthesizer
- USB MIDI
- TRS MIDI Type‑A

- 内蔵シンセサイザー
- USB MIDI
- TRS MIDI Type‑A

## Display

- Current song name
- Current section
- Current bar number
- Current chord and scale
- Active LPC
- Option: Possible other LPC

- 現在の曲名
- 現在のセクション
- 現在の小節番号
- 現在のコードとスケール
- アクティブなLPC
- オプション: 他のLPC候補


