# MIDI specification

Emiuet Session sends and receives standard MIDI messages.
Emiuet Sessionは標準MIDIメッセージを送受信します。

## Channels

- **Note output channel:** Configurable (default 1).  All Note On/Off messages use this channel.
- **Control Change channel:** Configurable (default 1).  CC messages are typically sent on the same channel.

- **ノート出力チャンネル:** 設定可能（デフォルト1）。すべてのNote On/Offメッセージはこのチャンネルを使用します。
- **コントロールチェンジチャンネル:** 設定可能（デフォルト1）。通常CCメッセージは同じチャンネルで送信します。

## Note mapping

## Note mapping
* Each physical key is mapped to a note number derived from the current Local Pitch Collection.
* Velocity is typically calculated from the initial pressure or key travel speed.
* In modes designed for performance with Digitone II, the system controls the Level of the target track, allowing the keys to behave like a pseudo-keyboard.


- 各物理キーは、現在のLocal Pitch Collectionから導出されたノート番号にマッピングされます。
- 通常、ベロシティは初期圧力や打鍵速度から算出します。
- Digitone2での演奏を想定したモードでは、対象トラックのLevelを操作して疑似的なキーボードとして振舞います。

## Control Change

- **CC95** (default for Digitone II) conveys overall pressure or a user‑defined expression parameter.
- Additional CC numbers may be assigned to individual keys or sensors.
- Firmware should send CC messages only when values change or at a minimum interval to avoid flooding.
- **CC95**（Digitone2向けデフォルト）は全体の圧力やユーザー定義の表現パラメータを伝達します。
- 追加のCC番号を個々のキーやセンサーに割り当てることができます。
- ファームウェアは値が変化したときや最小間隔でのみCCメッセージを送信し、過剰なデータ送信を避けるべきです。

## Program Change

Future firmware may implement Program Change to switch internal synth presets or external instruments.
将来のファームウェアではProgram Changeを実装し、内蔵シンセプリセットや外部機器の切り替えを可能にする予定です。

## Connectivity

- **USB‑MIDI:** Class‑compliant device for computers and mobile devices.
- **TRS MIDI Type‑A:** Compatible with standard DIN MIDI using an adaptor.
- **BLE‑MIDI (optional):** If an ESP32 or similar module is included, wireless MIDI may be supported.

- **USB‑MIDI:** コンピューターやモバイル機器向けのクラスコンプライアントデバイス。
- **TRS MIDI Type‑A:** 標準DIN MIDIアダプターを介して互換性があります。
- **BLE‑MIDI（オプション）:** ESP32などのモジュールが含まれる場合、無線MIDIをサポートできます。

## Timing

The total latency from key press to MIDI transmission should remain under 5 ms for USB and under 8 ms for TRS.
鍵を押してからMIDIを送信するまでの合計レイテンシはUSBで5 ms未満、TRSで8 ms未満を維持する必要があります。