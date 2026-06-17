# Relative Melodic Resolver (v0)

Solo Mode の中核。ジェスチャーと直前の状態から、次に出す MIDI note を**決定的**に
求めます。実装は `emiuet_session/core/solo.py`（pure、MIDI library 非依存）。

## 入力と出力

入力:

- `gesture: SoloGesture`（8 種）
- `last_output_note: int | None`（SoloCursor が保持）
- `current_lpc`: 現在の LPC pitch classes
- `current_core`: 現在のコードの core 構成音（chord tones）pitch classes
- `pending_octave_shift: int`, `pending_skip_count: int`
- `anchor_midi`（既定 60 = C4）
- `phrase_direction`（Resolve の tie-break 用）

出力 (`SoloResolution`):

- `note`: MIDI note number
- `pitch_class`
- `reason`: DisplayState / ログ用の trace 文字列

## SoloCursor

直前の出力を保持する状態。

```text
SoloCursor:
  last_output_note: int | None
  last_output_pitch_class: int | None
  last_gesture: SoloGesture | None
  phrase_direction: up | down | none
```

- 必須は `last_output_note`。
- `phrase_direction` は Up 系ジェスチャーで `up`、Down 系で `down`、REPEAT / RESOLVE では
  維持。Resolve の tie-break にのみ使います。

## PendingNoteModifiers

```text
PendingNoteModifiers:
  octave_shift: int   # 次の発音に *12 で加算
  skip_count: int     # 次の Core/LPC で N 番目に近い候補
```

- 発音後に必ず reset。
- スタック可: Skip を 3 回 → `skip_count=3`、Octave Up を 2 回 → `octave_shift=+2`。
- skip は Core/LPC の上下にのみ適用。Chromatic / Repeat / Resolve には適用しない。
- octave は解決後に `note += octave_shift * 12`（その後 0..127 にクランプ）。

## 初回発音ルール（last_output_note が None）

`anchor_midi = 60`（C4）を基準にします。

- **Repeat / Resolve**: anchor に最も近い core tone。
- **方向系（Core/LPC の Up/Down）**: anchor から **strict に**上 / 下へ。
- **Chromatic Up/Down**: `anchor ± 1`。

Dm7（core = C D F A）、anchor C4 の期待値:

| gesture | 初回出力 |
|---|---|
| Repeat | C4 (60) |
| Resolve | C4 (60) |
| Core↑ | D4 (62) |
| Core↓ | A3 (57) |
| LPC↑ | D4 (62) |
| LPC↓ | B3 (59) |
| Chromatic↑ | C#4 (61) |
| Chromatic↓ | B3 (59) |

> 実装方針: 方向系は初回も「anchor から strict に上/下」とする（deterministic）。よって
> Core↓ 初回は A3、Core↑ 初回は D4。Repeat/Resolve は anchor 近傍の core（C4）。

## gesture ごとの解決ルール（2 回目以降）

`ref = last_output_note` とする。

- **Repeat**: `ref` を再発音。
- **Core↑ / LPC↑**: `ref` より strictly 上で、pitch class が core / LPC に含まれる最も近い
  note。skip_count があれば N 番目。必要なら octave をまたぐ。
- **Core↓ / LPC↓**: 上記の下方向版。
- **Chromatic↑**: `ref + 1`。**Chromatic↓**: `ref - 1`（skip 非適用、octave は適用）。
- **Resolve**:
  - `ref` が既に core pitch class 上 → Repeat（`ref` を返す）。
  - そうでなければ、上方向の最近 core と下方向の最近 core のうち近い方へ解決。
  - tie（同距離）の tie-break: 1) `phrase_direction` があればその方向, 2) なければ下方向,
    3) それでも決まらなければ anchor に近い方。

trace 例:

```text
CORE_UP last=60 candidates=[62, 65, 69, 72, ...] skip=0 -> 62
LPC_UP  last=62 candidates=[64, 65, 67, ...] skip=0 -> 64
RESOLVE resolve last=64 up=[65] down=[62] dir=none -> 65
CORE_UP last=60 candidates=[62, 65, 69, ...] skip=2 -> 69 +1*12 = 81
```

## 今後の拡張候補（v0 では未実装）

```text
GUIDE_TONE_NEAREST
APPROACH_FROM_BELOW / APPROACH_FROM_ABOVE
LEAP_UP / LEAP_DOWN
BASS_ROOT / BASS_FIFTH
InitialLayoutOrder 系の初回方針切替
phrase_direction を使ったより高度な解決
```
