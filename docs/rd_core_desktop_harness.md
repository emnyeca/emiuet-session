# R&D Core と Desktop Debug Harness

`EmiuetCore` を実際に動かして演奏状態・MIDI イベント・表示状態を確認するための
デスクトップ用 CLI ハーネスです。GUI には依存しません（将来 GUI へ拡張可能な構造）。
キー操作、segment 送り、register shift、approach、tempo 変更、panic を試せます。

## 実行

リポジトリルートから:

```sh
python -m apps.desktop_debug                            # 対話 (two-row)
python -m apps.desktop_debug --layout-orientation alternating
python -m apps.desktop_debug --demo                     # スクリプト実演
python -m apps.desktop_debug --script FILE
```

ハーネスは **adapter** です: 入力したコマンドを `InputFrame` に変換して `EmiuetCore` に
渡し、出力された MIDI イベントと `DisplayState` を描画します。GUI フロントエンドも同じ
やり方で engine を再利用できます。

## コマンド

| Command | 効果 |
|---------|------|
| `1`..`8` | キーを trigger (NoteOn + NoteOff) |
| `hold N` / `rel N` | slot N を sustain / release（0 始まり） |
| `next` / `prev` | segment 移動 |
| `up` / `down` / `reset` | register shift |
| `mode octave\|fifth\|fourth\|custom N` | register step サイズ設定 |
| `app+` / `app-` / `app0` | approach up / down / clear |
| `profile` | performance profile を cycle |
| `tempo BPM` | tempo 変更（step timing を再計算） |
| `tick MS` | 仮想時間を進める（step 自動進行を駆動） |
| `panic` | active note を全 off |
| `orientation [two-row\|alternating]` | layout 表示を切替 / 表示 |
| `layout` | 現在の表示を出す |
| `state` | 現在状態を再表示 |
| `help` / `quit` | ヘルプ / 終了 |

## 出力の読み方（two-row、既定）

```
[seg 1/4 step 1/1]  Dm7 > G7    OCT+0  NORM  (two-row)
  color: .E  .G  .B  .C+1
  core : #C  #D  #F  #A
  dbg  : D Dorian prio1 retry0 lpc=[2, 4, 5, 7, 9, 11, 0] active=[]
  midi : NoteOn  ch1 n 60 v100
```

- 1 行目 — segment/step の進行、current → next chord、register label、profile、現在の
  表示名。
- colour line（上、`.`）と core line（下、`#`）。各ラインは左→右に昇順。`C+1` は C anchor
  の register より 1 octave 上（借りた upper extension）。
- `dbg` — 選択 scale、priority、retry level、LPC、active note。
- `midi` — この frame で出した抽象イベント。

`orientation alternating` は 1 列表示（`keys : 1#C  2.E  3#D ...`）に切り替えます。note の
値は同一で、読み方だけが変わります。

## demo が示すもの

`--demo` は固定スクリプトを流し、ロード、キー trigger、segment 変更をまたいで held note が
（発音時の音高のまま）生き残ること、register shift モード、approach 付き trigger、tempo
変更、panic を実演します。非対話で動くので、engine の簡易スモークテストにもなります。

## MIDI コントローラー入力

generic MIDI input adapter とコントローラーハーネスを別途用意しています。市販の MIDI
パッドコントローラー（例: CCP16BK）を 8 演奏キー + 8 制御キーとして接続できます。core は
MIDI ライブラリに依存しません（adapter 側のみ optional に `mido` を使用）。詳細は
`docs/midi_controller_testing.md` と `docs/ccp16_mapping.md` を参照。

## 今後の adapter

同じ `OutputFrame` で virtual MIDI-out port や GUI shell を駆動できます。これらは core を
変えずに追加できるため、まず演奏可能・テスト可能な core を優先し、後続作業として残して
います。
