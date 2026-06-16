# CCP16BK マッピング

## CCP16 を R&D に使う目的

CCP16BK は16パッドの MIDI パッドコントローラー（USB-B、BLE MIDI、TRS Type-A MIDI
I/O 対応）で、各パッドは自由に割り当てできます。16パッドは Emiuet Session の
8 演奏キー + 8 制御キーにちょうど対応するため、firmware 着手前に R&D core を実機で
弾くのに向いています。

## 16パッドの推奨役割

Emiuet Session の演奏面は 2 段 4 列（TwoRowCoreColor）です。

```
□ □ □ □     colour line  (slots 1 3 5 7)
■ ■ ■ ■     core line    (slots 0 2 4 6)
```

4x4 パッドの推奨レイアウト（上 2 段 = 演奏、下 2 段 = 制御）:

```
[colour s1] [colour s3] [colour s5] [colour s7]      <- 演奏
[core  s0 ] [core  s2 ] [core  s4 ] [core  s6 ]      <- 演奏

[prev_seg ] [next_seg ] [reg_down ] [reg_up   ]      <- 制御
[approach-] [approach+] [panic    ] [reg_reset]      <- 制御
```

（最後の制御パッドは好みで `register_reset` の代わりに `profile_cycle` にしてもよい。
profile を編集するだけ。）

## 初期 profile（`controller_profiles/ccp16.json`）

同梱 profile は channel 1、note 36–51 を仮定しています。

| Notes | 役割 |
|---|---|
| 36 37 38 39 | core line: slots 0, 2, 4, 6 |
| 40 41 42 43 | colour line: slots 1, 3, 5, 7 |
| 44 45 | previous_segment, next_segment |
| 46 47 | register_down, register_up |
| 48 49 | approach_minus, approach_plus |
| 50 51 | panic, register_reset |

これらの note 番号は **仮定**です。CCP16 のパッド値は本体設定で変わるため、実機で
確認してから使ってください。

## CCP16 側の設定

1. 使うパッドを **Note** モードにする（CC でも Program でもない）。
2. **Momentary** にする（Toggle にしない）。これで押下=Note On、解放=Note Off が
   送られる。Toggle だと note が鳴りっぱなしになる。
3. 全パッドを **同じ MIDI channel** にし、profile の `midi_channel` と一致させる
   （または `midi_channel` を省略して任意 channel を受け付ける）。
4. R&D テストでは **USB** 接続を使う。

## raw ログで note 番号を確認して profile を修正する

1. CCP16 に対してハーネスを起動する（midi_controller_testing.md 参照）。
2. 各パッドを押し、`RAW` 行を読む。例:
   `RAW : note_on ch=1 note=38 velocity=120`。
3. パッドの note がこの表と違う場合、その note が意図した slot / command を指すように
   `ccp16.json` を編集して再実行する。コード変更は不要。

すべて profile 駆動なので、`--profile` に別の JSON を指定すれば他の 16 パッド
コントローラーでも同じハーネスが使えます（制御キーを CC ボタンに割り当てた例として
`generic_16pad.json` を同梱）。

## ベンダーマニュアル

CCP16 本体マニュアルは `docs/vender/cp_ccp16.pdf`（`.gitignore` 対象、ローカル参照用）。
