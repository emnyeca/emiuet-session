# Digitone Step Timeline（Auto Follow の同期基準）

## 要点

Auto Follow は、**原曲の小節・テンポではなく**、Digitone II へ送られた Pattern /
Step / SPEED / LENGTH に対応する **compiled timeline** に同期します。

EUB Changes は Digitone II のステップ数を最小化するため、原曲のテンポ・小節を
そのまま送らないことがあります。したがって Emiuet Session 側が「原曲 Tempo120 の
4/4 で 2 小節」と数えると、Digitone II 上の Step 進行とズレます。

## 例

原曲:

```text
Tempo 120 / 4/4
| Dm7 | G7 |   (2 小節)
```

EUB Changes が Digitone II 用に最小 Step 化:

```text
Digitone Pattern:
  Step 1 = Dm7
  Step 2 = G7
  SPEED 1/8, Tempo 60 など
```

このとき Emiuet Session の timeline も「2 つの compiled step」として解釈し、Auto
Follow は**原曲 2 小節分**ではなく、**Digitone 上で実際に進む 2 Step 分**を追います。

Digitone II の Step / LENGTH / SPEED の詳細は
`changes/docs/vendor/Digitone-2-User-Manual...pdf` を参照。

## データモデル（`emiuet_session/core/timeline.py`）

```text
TimelineBasis:
  original_song   # 参考用（Auto Follow では非推奨）
  digitone_step   # Auto Follow が期待する基準

CompiledHarmonicStep:
  id
  start_tick, end_tick   # Digitone Step 進行に一致するよう compile した tick 範囲
  chord_context          # chord / core_pcs / lpc
  source_step_index, source_label

CompiledTimeline:
  basis, steps[]
  original_tempo   # 表示・参考用
  digitone_tempo   # Digitone 側 Pattern/Syx のテンポ
  find_step_by_tick(tick)            # form をループして現在 step
  find_next_distinct_chord(step)     # 次に chord が変わる step
  find_next_step(step)
```

`original_tempo` は表示用で、進行計算には使いません。進行は MIDI Clock の tick と
compiled step の `start_tick`/`end_tick` だけで決まります。

## tick と進行

- MIDI Clock は 24 ppqn（4 分音符 = 24 clock）。
- F8 受信は RUNNING 中のみ playhead（tick）を進めます（重い処理はしない）。
- `find_step_by_tick(tick)` は tick を total（最後の step の end_tick）で割った余りに
  正規化し、`start_tick <= t < end_tick` の step を返します（パターンをループ）。

## 警告

`timeline_basis = original_song` や timeline 未ロードで Auto Follow を使うと、
DisplayState に警告を出します。同期ズレを隠さず、実機確認時に原因が見えることを優先
します。

```text
WARN: Auto Follow expects a Digitone-step-aligned timeline.
      Current timeline_basis is original_song.
      Chord cursor may not sync with Digitone II.
```

## 現状の入力元

EUB Changes exporter との接続は本 PR の範囲外です。R&D 用に、サンプル fixture から
compiled timeline を作る `sample_compiled_timeline(ticks_per_step=24)` を同梱しています
（各コード = 1 Digitone step、tick ベース）。将来、Changes export の
`compiled_harmonic_steps` をそのまま `CompiledTimeline` に流し込めるよう設計しています。
