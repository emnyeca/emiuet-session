# Performance Model と 8-Slot Layout

ここでは 3 つのモデル（Song / HarmonicAnalysis / PerformanceModel）の違い、8 キーへの
配置アルゴリズム、そして「slot voicing 重複除去（slot voicing de-duplication）」を
説明します。重複除去は**ボイシング上の調整**であり、和声解析を書き換えるものでは
ありません。

## 3 つの異なるモデル

| Model | 何か | 誰が作るか |
|-------|------|-----------|
| `Song` (`model/song.py`) | structure / meter / tempo / bar 内の chord symbol | EUB Changes import |
| `HarmonicAnalysis` (`model/analysis.py`) | chord ごとの理論: chord tone, LPC, scale, pitch ごとの role/weight | EUB Changes analysis |
| `PerformanceModel` (`model/performance.py`) | 演奏用の 8-slot layout、segment/step にまとめたもの | Emiuet Session Model Builder |

これらは意図的に分けています。Song は*曲が何か*、Analysis は*音が何を意味するか*、
PerformanceModel は*8 キーでどう弾くか*を表します。

### Segment と Step

- **Segment** — **Next** 1 回で進む単位。
- **Step** — segment の*内部*での chord change。step は tempo に従って自動進行する。

速いテンポでは、1 つの segment が複数の step を持って自動で進む一方、演奏者は心地よい
頻度で Next を押せます。

## HarmonicAnalysis: Changes の export contract

`HarmonicStep` は、Changes の exporter に埋めてほしい形です: chord symbol, root,
quality, chord tones, LPC, 選択した scale + priority, retry/fallback level, そして
`PitchCandidate` のリスト。各 candidate は `pitch_class`, `label`（degree）, `role`,
`weight`, `stability`, `tension` を持ちます。

`PitchRole` ∈ {core, tension, altered_tension, approach, avoid, color}。role と weight
が slot 配置を決めます。

## 8-slot layout: 2 段 4 列 (`model/layout.py`)

演奏面は 2 段で読みます（`LayoutOrientation.TWO_ROW_CORE_COLOR`、R&D の既定）。

```
□ □ □ □   colour / tension line  (slots 1 3 5 7)
■ ■ ■ ■   core / high-importance line  (slots 0 2 4 6)
```

- 各**ラインは低→高に昇順**（`■` 昇順、`□` 昇順）。
- 交互に読んだ 1 列の並びは昇順である**必要はない**。
- 旧来の 1 列 `ALTERNATING_ROW`（`■ □ ■ □ ■ □ ■ □`）も引き続きサポート。slot index と
  note 割り当ては同一で、表示だけが違います。

### アルゴリズム

1. excluded role（approach）を除外し、NORMAL では suppressed role（avoid）も除外。
2. core 候補と colour 候補を weight で sort（tie-break は stability、次に pitch class、
   決定的に）。
3. core line に 4 つ、colour line に最大 4 つの音を取る。colour line は colour 専用で、
   7-note scale で足りないときだけ chord tone を借りる（colour fill 参照）。
4. 音を配置し、octave を選ぶ:
   - **初期 step**（previous layout なし、`InitialLayoutOrder.ANCHOR_LOW_TO_HIGH`）:
     各ラインを C anchor（MIDI 60）から低→高に並べる。
   - **後続 step**: previous layout からの**スロットごとの register 跳躍の合計を最小化**
     する割り当てを選ぶ（≤24 通りの順列）。これで ii-V-I などが滑らかに voice-lead する。
     （厳密なライン昇順は初期 layout の性質。後続 step は voice leading を優先する。）
5. **slot voicing 重複除去**のセーフティネット（後述）。

weight / policy はすべて `LayoutPolicy` にあり、magic number を散らしていません。builder
は決定的なので layout は test 可能です。

### colour fill（scale が colour line に足りないとき）

7-note scale は non-chord tone が 3 つしかないため、4 つ目の colour slot は chord tone を
借りる必要があります。core line が既に鳴らしている音を重複させる代わりに、借りた音は
**colour line の上に続く最も近い昇順の音**として置きます（upper-octave extension）。
同じ pitch class を別 octave に置くことは許容され（8 キー面では音楽的に有用）、fill 音は
公称の register span を超えてもかまいません。

例（Dm7、決定的な出力）:

```
□ E   G   B   C+1      colour line  (64 67 71 72)
■ C   D   F   A        core line    (60 62 65 69)
```

仕様の図解では colour line を `B E G C+1` と書いていますが、実装は `E G B C+1` を
出力します — pitch-class 集合は同じ `{B, E, G, C}` で、各ラインは厳密に昇順、`C+1` は
借りた upper-octave extension（死にキーの重複ではない）です。

### slot voicing 重複除去

配置の結果、2 つのキーが**完全に同じ MIDI note** になる場合（主に voice-lead する後続
step）、重複除去 pass（`LayoutPolicy.dedupe_voicing`、既定 on）が:

- **優先度の高い** slot の音を保つ（core position が先、次に weight、次に index）。
- **優先度の低い / colour** slot を whole octave 単位で空いている in-range の音へずらす。
  ただし**演奏可能な音が空くときだけ**動かす。
- pitch class や role は決して変えない。

これは voicing / 演奏性の調整であって、**和声解析の変更ではありません**。同じ pitch
class の別 octave は許容し、完全重複の MIDI note だけを除去します。

## sample fixture の仮定

組み込みの `Dm7 | G7 | Cmaj7 | A7alt` fixture（`fixtures/sample.py`）は、実際の Changes
export に接続するまでの placeholder です。仮定は以下の通り（明記）。

- weight / stability / tension の値は手置きで、Changes 出力ではない。
- LPC は素直な親 scale（Dorian / Mixolydian / Ionian / Altered）。
- 11th は G7 と Cmaj7 で `avoid`（NORMAL では suppress）。
- **A7alt** の core は土台の A7 chord tone（A C# E G）として扱い、altered 音は
  `altered_tension` / `color` で表現する。strict な altered scale は natural 5th を
  省くが、8 キー面のため core tone として残している。Changes の理論仕様とズレる場合は
  exporter が正本であり、この fixture は再生成すべき。
