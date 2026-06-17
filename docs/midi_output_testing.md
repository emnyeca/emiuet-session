# MIDI Output での実音テスト

## 目的

`EmiuetCore` が返す抽象 MIDI イベント（NoteOn / NoteOff など）を、実際の MIDI OUT
port へ送信し、外部音源やソフトシンセを鳴らすための adapter とハーネス機能です。

入力（CCP16 → MIDI input adapter → InputFrame → EmiuetCore → 抽象 MIDI events）の続きとして、
その抽象 events を MIDI OUT へ流します。

## core への依存方針

出力 adapter は `apps/desktop_debug` 側に置き、**core は MIDI ライブラリに依存しません**。
core は抽象 `MidiEvent` を返すだけで、`apps/desktop_debug/midi_output.py` がそれを mido
message へ変換して送信します。`mido` は実 port を開くときだけ遅延 import されます。

## 依存ライブラリ

MIDI input と同じく optional extras です。

```sh
pip install -r requirements-midi.txt      # mido + python-rtmidi
# または: pip install -e ".[midi]"
```

## output port の一覧表示

```powershell
python -m apps.desktop_debug.midi_controller_harness --list-ports
# 出力だけ見たいとき:
python -m apps.desktop_debug.midi_controller_harness --list-outputs
```

表示例:

```text
MIDI input ports:
[0] H12MIDI-Pro 1
[1] MIDIIN2 (H12MIDI-Pro) 2

MIDI output ports:
[0] Microsoft GS Wavetable Synth 0
[1] H12MIDI-Pro 2
```

## ハーネスの起動（`--midi-out`）

`--midi-out` を指定すると、CORE event を表示しつつ実 MIDI OUT へ送信します。未指定の
場合は従来通り CORE 表示のみで送信しません。

PowerShell では複数行に分ける場合に行末のバッククォート `` ` `` を使います。

```powershell
python -m apps.desktop_debug.midi_controller_harness `
  --midi-in "H12MIDI-Pro 1" `
  --midi-out "H12MIDI-Pro 1" `
  --profile apps/desktop_debug/controller_profiles/ccp16.json
```

1 行版:

```powershell
python -m apps.desktop_debug.midi_controller_harness --midi-in "H12MIDI-Pro 1" --midi-out "H12MIDI-Pro 1" --profile apps/desktop_debug/controller_profiles/ccp16.json
```

- `--midi-out` は port 名・部分一致・index のいずれでも指定できます。
- `--dry-run` は実送信せず OUT ログだけ出します（フォーマット確認・ハードウェアなしの
  確認用）。
- `--self-test` は synthetic message を流すモードです。`--dry-run` と併用すると OUT ログ
  まで確認できます（ハードウェア不要）。

### H12MIDI-Pro 経由で外部音源を鳴らす

想定接続:

```text
CCP16 MIDI OUT
→ H12MIDI-Pro MIDI IN 1
→ PC / Python harness
→ H12MIDI-Pro MIDI OUT 1
→ 外部音源 / Digitone II / ソフトシンセ
```

`--midi-in "H12MIDI-Pro 1"`、`--midi-out "H12MIDI-Pro 1"`（実際の port 名は
`--list-ports` で確認）。

### ソフトシンセ / 仮想 MIDI port を使う

ハードウェア音源がなくても、OS 内蔵シンセや仮想 MIDI port で音を確認できます。

- Windows 内蔵: `--midi-out "Microsoft GS Wavetable Synth 0"`
- 仮想 port（loopMIDI 等）を作り、DAW / ソフトシンセ側で受ける構成も可。

## ログの読み方（RAW / MAPPED / CORE / OUT）

```text
RAW    : note_on ch=10 note=36 velocity=127     <- 受信した生メッセージ
MAPPED : slot 0 press                            <- 解決したアクション
CORE   : NoteOn  ch1 n 60 v100                   <- engine が返す抽象 MIDI
OUT    : note_on ch=1 note=60 velocity=100 -> H12MIDI-Pro 1   <- 実送信したもの
```

NoteOff:

```text
RAW    : note_off ch=10 note=36 velocity=0
MAPPED : slot 0 release
CORE   : NoteOff ch1 n 60
OUT    : note_off ch=1 note=60 velocity=0 -> H12MIDI-Pro 1
```

ログ上の channel は**ユーザー向けに 1..16** で表示します。内部で mido へ送るときだけ
0..15 に変換します。

### channel 変換

| 表示 / EmiuetCore | mido 送信 |
|---|---|
| ch 1 | channel 0 |
| ch 16 | channel 15 |

変換は `to_mido_channel()`（1..16 以外は明確に reject）。`tests/test_midi_output.py` で
担保しています。

### velocity について（現時点の仕様）

**現時点では入力 velocity は core 出力に直接反映されず、core 側の velocity 設定
（既定 100）が使われます。** CCP16 の FULL LEVEL（velocity 127）を出力に通す velocity
passthrough は次以降の課題です。

## stuck note 対策（panic / 終了時）

実音段階では鳴りっぱなし（stuck note）対策が重要です。

- `panic` コマンド: active note へ NoteOff を送り、さらに使用 channel へ All Notes Off
  (CC 123) を送ります。
- 終了時（Ctrl+C / 正常終了）: active note へ NoteOff を送り、`--send-all-notes-off-on-exit`
  が有効（既定 on）なら使用 channel へ CC 123 も送ります。無効化は
  `--no-send-all-notes-off-on-exit`。
- CC 123 は**使用した channel のみ**へ送ります（全 16 channel へは送りません）。

```text
MAPPED : panic
CORE   : NoteOff ch1 n 60
OUT    : note_off ch=1 note=60 velocity=0 -> H12MIDI-Pro 1
OUT    : all_notes_off ch=1 -> H12MIDI-Pro 1
```

## Troubleshooting

- **input は来るが音が出ない / OUT ログは出るが音が出ない** — Python 側は送信できて
  います。MIDI ルーティングまたは音源側設定の可能性が高い。
- **MIDI output port を間違えている** — `--list-outputs` で正しい port 名を確認する。
- **H12 の routing が違う** — H12MIDI-Pro の入出力ルーティング設定を確認する。
- **音源側の MIDI channel が違う** — core 出力は既定 ch1。音源を ch1 で受けるか、音源側を
  合わせる。
- **音源側 track が mute / 受信 off** — DAW / 音源のトラック状態を確認する。
- **note off が来ず音が伸びる** — 入力パッドが Toggle モード。Momentary にする
  （ccp16_mapping.md 参照）。
- **Ctrl+C で終了したら音が残った** — 終了時 panic が動いているか確認。`--midi-out`
  指定時は終了時に NoteOff + CC 123 を送る。
- **Windows で port 名が想定と違う** — `--list-ports` の実際の名前を使う。index 指定でも可。
