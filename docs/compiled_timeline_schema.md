# Compiled Timeline Schema（EUB Changes ⇔ Emiuet Session の契約）

EUB Changes が Digitone II 用に compile した step timeline を、Emiuet Session が
**そのまま読む**ための JSON schema です。Emiuet Session 側で SPEED / LENGTH / tempo を
再解釈しません。tick 境界は export 時点で確定済みとします。

- schema 名: `emnyeca.emiuet_session.compiled_timeline`
- `schema_version`: 2（v1 に `contexts` / `resolver_core` / `hard_context` を追加）
- 正本 fixture: `tests/fixtures/dm7_g7_cmaj7_a7_contrast_timeline.json`
  （Changes exporter の出力期待値であり、Emiuet importer の入力でもある）

## トップレベル

```json
{
  "schema": "emnyeca.emiuet_session.compiled_timeline",
  "schema_version": 2,
  "timeline_basis": "digitone_step",
  "clock": { "ppqn": 24, "original_tempo": 120.0, "digitone_tempo": 60.0, "meter": "4/4" },
  "form": { "loop": true, "start_tick": 0, "end_tick": 96 },
  "steps": [ ... ]
}
```

- `timeline_basis` は Auto Follow では `digitone_step` を期待。`original_song` や不明な
  basis では Emiuet Session が警告を出す。
- `clock.original_tempo` は表示・参考用。進行計算には使わない（MIDI Clock の tick と
  step の `start_tick`/`end_tick` だけで決まる）。

## step

```json
{
  "id": "step_002",
  "source_step_index": 2,
  "start_tick": 48,
  "end_tick": 72,
  "chord": "Cmaj7",
  "default_context_role": "progression",
  "mod_context_role": "contrast",
  "contexts": {
    "progression": { ... },
    "contrast": { ... }
  }
}
```

- `start_tick < end_tick`、step 間で tick は単調増加。
- `default_context_role`: 通常時の context（`progression`）。
- `mod_context_role`: MOD 中の context（`contrast`）。

## context

```json
{
  "role": "contrast",
  "display": "G7 HW",
  "scale_name": "Half-Whole Diminished",
  "scale_root": "G",
  "selection_policy": "contrast_priority",
  "hard_context": ["G", "B", "D", "F"],
  "resolver_core": ["G", "B", "D", "F"],
  "lpc": ["G", "Ab", "Bb", "B", "Db", "D", "E", "F"]
}
```

- `hard_context`: EUB Changes 内部の和声制約・拡張音込みの文脈。Emiuet 側では当面
  **debug / display / inspection 用**で、resolver には使わない。
- `resolver_core`: Solo Mode の `Resolve` / `Core Up` / `Core Down` が向かう安定音。
  拡張コードでも基本骨格（概ね 4 和音）に寄せる。
- `lpc`: `LPC Up` / `LPC Down` が辿る Local Pitch Collection。
- **必須条件**: `resolver_core ⊆ lpc`（含まない context は不正）。
- `progression`: 前後文脈込みの通常 context。`contrast`: MOD 用の対比 context
  （単純 reverse ではなく Contrast Priority で選ぶ）。

## context が無い場合

`contexts.contrast` を省略または `null` にできる。Emiuet Session は contrast の無い step
では progression context へ fallback する。

## Emiuet Session 側の対応

- `contexts.progression` → 通常の `ChordContext`。
- `contexts.contrast` → Contrast MOD 中の `ChordContext`。
- `ChordContext.core` ← `resolver_core`、`ChordContext.lpc` ← 選択中 context の `lpc`。
- import 時に schema / `schema_version` / `timeline_basis == digitone_step` / steps 非空 /
  tick 単調増加 / `start_tick < end_tick` / `default_context_role` 存在 / progression 存在 /
  `resolver_core ⊆ lpc`（contrast があれば contrast も）を検証する。

詳細は `docs/auto_follow.md`（Auto Follow）, `docs/harmonic_ahead.md`（Harmonic Ahead）,
本書（schema）を参照。
