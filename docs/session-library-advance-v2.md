# Session Library / Advance Architecture v2

この文書は、Emiuet Session を将来的に Teensy 単独デバイス化するための責務境界だけを記録する。

## 基本方針

Changes で和声 context を compile し、Emiuet Session は軽く読む。
Emiuet Session 側では、演奏中に chord symbol parsing、scale selection、LPC 生成、Contrast Priority 生成、library 全体の再構築をしない。

## advance_mode と timeline_basis

`advance_mode` は現在 step の進め方を表す。

- `clock_song`: 原曲小節・拍に沿って MIDI Clock / internal clock で進む
- `manual`: PAD / footswitch / encoder などで手動 advance する
- `device_step`: Digitone II など外部機器用に compile された実 step timeline に追従する

`timeline_basis` は timeline の基準を表す。

- `original_song`: 原曲小節・拍を正とする
- `segment_map`: manual advance や構成単位を正とする
- `digitone_step`: Digitone II 用に変換された実 step を正とする

既存の実機確認済み `digitone_step` 経路は、`device_step + digitone_step` として扱う。

## Song / Timeline / Library

`SongPayload` は 1 曲分の payload で、複数の `SessionTimeline` を持てる。
`SongLibraryIndex` は起動時や選曲時に読む軽量 metadata で、payload 本体を含めない。

想定する読み込み単位は次の通り。

- 起動時: `SongLibraryIndex`
- 選曲時: 選んだ `SongPayload`
- 演奏時: 現在 song / 現在 timeline

## Runtime Song Transpose

`transpose_offset_semitones` は `-12..+12` に制限する。
transpose は MIDI output だけでなく、Solo resolver に渡す前の `ChordContext` に適用する。

対象は `resolver_core`、`lpc`、`scale_root`、display label、note output の基礎 context。

`runtime_transpose_policy` は timeline ごとに持つ。

- `allowed`: transpose を適用する
- `warn`: transpose を適用するが、外部機器とのズレを警告できる
- `locked`: transpose を適用しない

`device_step / digitone_step` は外部機器側の伴奏とズレる可能性があるため、既定で `locked` とする。

