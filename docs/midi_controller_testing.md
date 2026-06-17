# MIDI コントローラーでの演奏テスト

## 目的

PC キーボードの CLI だけでなく、市販の MIDI パッドコントローラーで Emiuet
Session R&D Core を実際に演奏テストするための adapter とハーネスです。

コントローラーのパッド/ボタンを、engine の 8 演奏 slot と制御コマンドへ割り当てる
ことで、R&D core を実機で弾けるようにします。割り当ては JSON の controller
profile で表現する **データ**なので、別のコントローラーへの対応は profile の差し替え
だけで済み、コード変更は不要です。

## core への依存方針

MIDI 入力は `apps/desktop_debug` 側の **adapter** として実装してあり、**core は
MIDI ライブラリに依存しません**（`emiuet_session/` に `mido` / `python-rtmidi` の
import はありません）。`mido` は実ポートを開くときだけ遅延 import されるため、
未インストールの環境でも pytest と既存 CLI は動作します。

## 依存ライブラリ

core には依存ライブラリがありません。コントローラーハーネスのみ optional extras が
必要です。

```sh
pip install -r requirements-midi.txt      # mido + python-rtmidi
# または: pip install -e ".[midi]"
```

未インストールの場合、`--list-ports` とライブ実行は install 手順を案内します。
`--self-test` モードと全 unit test はそのまま動きます。

## ポート一覧の表示

```sh
python -m apps.desktop_debug.midi_controller_harness --list-ports
```

## ハーネスの起動

```sh
  python -m apps.desktop_debug.midi_controller_harness --midi-in "H12MIDI-Pro 1" --profile apps/desktop_debug/controller_profiles/ccp16.json
```

- `--midi-in` は、正確なポート名・大文字小文字を無視した部分一致・`--list-ports`
  の index のいずれでも指定できます。
- `--layout-orientation two-row|alternating` で表示を選びます。
- `--self-test` は synthetic message を流すモードで、ハードウェア不要です。
  mapping と engine 出力の確認、profile の動作確認に使えます。
- `--midi-out` を付けると、engine の出力を実 MIDI OUT へ送って外部音源を鳴らせます
  （省略時はログのみ）。詳細は `docs/midi_output_testing.md` 参照。

## ログの読み方

受信メッセージごとに次を出力します。

```
RAW    : note_on ch=1 note=36 velocity=100      <- 受信した生メッセージ
MAPPED : slot 0 press                            <- 解決したアクション
CORE   : NoteOn  ch1 n 60 v100                   <- engine が出す抽象 MIDI
[seg 1/4 step 1/1]  Dm7 > G7    OCT+0  NORM  (two-row)
  color: .E  .G  .B  .C+1
  core : #C  #D  #F  #A
  dbg  : D Dorian prio1 retry0 lpc=[...] active=[60]
  midi : NoteOn  ch1 n 60 v100
```

`RAW` の channel は **1 始まり**で表示します（mido 内部は 0 始まり）。`RAW` を見れば
コントローラー実機の note / CC 番号が分かるので、その番号に合わせて profile を
編集します。

## controller profile JSON の書き方

```json
{
  "name": "My controller",
  "midi_channel": 1,
  "note_mappings": {
    "36": { "type": "slot", "slot": 0 },
    "45": { "type": "command", "command": "next_segment" }
  },
  "control_mappings": {
    "21": { "type": "command", "command": "next_segment" }
  }
}
```

- `midi_channel` は 1 始まり。省略すると任意の channel を受け付けます。
- `note_mappings` の key は MIDI note 番号、`control_mappings` の key は CC 番号。
- action `type` は `slot`（`slot` は 0..7）または `command`。
- `command` の種類: `next_segment`, `previous_segment`, `register_up`,
  `register_down`, `register_reset`, `approach_plus`, `approach_minus`,
  `profile_cycle`, `panic`。

### Note と CC の押下判定の違い

| | 押下 (press) | 解放 (release) |
|---|---|---|
| **Note** | `note_on` velocity > 0 | `note_off`、または `note_on` velocity 0 |
| **CC** | value ≥ 64 | value < 64 |

`approach_plus` / `approach_minus` は press と release の両方を使います（押している間
だけ有効）。それ以外の command は press で 1 回発火し、release は無視します。

## Troubleshooting

- **ポートが見えない** — ケーブル/ドライバを確認。USB は起動前に接続する。macOS では
  コントローラー専用ドライバが必要な場合がある。
- **Bluetooth MIDI で見えるが入力が来ない** — まず OS の MIDI 設定でペアリング/接続
  する。R&D テストでは **USB** を優先（BLE 固有問題は本書の対象外）。
- **Note On は来るが Note Off が来ない** — パッドが **Toggle** モード。**Momentary**
  に切り替える（ccp16_mapping.md 参照）。そのままだと note が鳴りっぱなしになる。
- **何も起きない / `(channel N ignored)`** — コントローラーの channel が profile の
  `midi_channel` と違う。合わせるか `midi_channel` を省略する。
- **意図しない音が鳴る** — profile の note 番号が実機と違う。`RAW` ログを見て profile
  を修正する。
- **velocity 0 の Note On が来る** — 対応済み。Note Off（slot release）として扱う。
- **Toggle / latch するパッド** — どこでも前提にしていない。Momentary を使う。
