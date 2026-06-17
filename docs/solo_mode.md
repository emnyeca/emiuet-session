# Solo Mode

## 目的

Solo Mode は Emiuet Session の主軸候補となる演奏言語です。8 キーを「小さな鍵盤」
として固定音に割り当てるのではなく、**旋律ジェスチャー**として扱い、直前に出した音・
現在の LPC・現在のコードの core 構成音から次の音を**相対的に**決めます。

## なぜ固定 slot 方式から移行するか

実機（CCP16 → Digitone II）で触った結果、固定 slot 方式（キーごとに現在コード/LPC 上の
固定ノートを割り当てる）は、8 キーが小さな鍵盤になってしまい、直感的なソロ演奏に
向きませんでした。少ないキーで旋律を動かすには、「どの音か」を毎回選ぶより「上へ / 下へ /
解決」のような**動き**でキーを押せる方が自然です。

そこで Solo Mode では、キー = 音名ではなく、キー = 旋律の動き（ジェスチャー）とします。

## PerformanceMode の役割分担

- **ChordMode**: 既存の固定 slot / 2 段 4 列コード配置。コード構成音やハーモニーの
  確認、固定 slot 方式との比較用に**残します**（壊しません）。
- **SoloMode**: 本ドキュメントの相対メロディ方式。今後の主軸。
- **BassistMode**: 予約のみ（Root / Fifth / walking bass 等の将来モード）。v0 では未実装。

Mode の切替は誤爆防止のため**実機キーではなく CLI option (`--mode`)** で行います。

## 8 キー配置（CCP16 PAD1〜8）

```
PAD5      PAD6      PAD7      PAD8
Resolve   Core↑     LPC↑      Chromatic↑

PAD1      PAD2      PAD3      PAD4
Repeat    Core↓     LPC↓      Chromatic↓
```

- **Repeat**: 直前音を再発音。
- **Core↑ / Core↓**: 直前音より上 / 下で最も近い core tone へ。
- **LPC↑ / LPC↓**: 直前音より上 / 下で最も近い LPC 内の音へ（core を含んでよい）。
- **Chromatic↑ / Chromatic↓**: 直前音から半音上 / 下へ。
- **Resolve**: 直前音から最も近い core tone へ解決。すでに core 上なら Repeat として扱う。

解決の詳細は `docs/relative_melodic_resolver.md` を参照。

## mono last-press-wins（同時押し方針）

Solo Mode では演奏キー同士の同時押しを和音にしません（`SoloPolyphonyPolicy: mono_last_press_wins`）。

- active なソロ音は原則 1 音。
- 新しい演奏キーを押すと、前のソロ音を NoteOff してから新しい音を NoteOn する（後押し優先）。
- release は、そのキーが**現在鳴っているソロ音を出したキーのとき**だけ NoteOff する。
  古いキーの release で現在の音を止めない。
- MOD / 制御キー + 演奏キーは許容。演奏キー + 演奏キーは和音にしない。

ChordMode の note lifecycle は従来どおり維持します。

## Pending Octave / Pending Skip

Register 系は常時状態ではなく、**次の発音にだけ適用される pending modifier** です
（詳細は relative_melodic_resolver.md）。

- **Pending Skip**: 押すごとに `skip_count += 1`。次の Core/LPC で「N 番目に近い候補」を選ぶ。
- **Pending Octave Up/Down**: 押すごとに `octave_shift ±= 1`。次の発音で `±12 * n`。
- 発音後、pending は reset されます。
- **Clear Pending / Reset Cursor**: pending と SoloCursor（直前音など）を初期化。

## Segment Navigation（wrap）

Next / Previous Segment は **wrap** を既定とします（`SegmentNavigationPolicy: wrap`）。

- 最後の segment で Next → 最初へ。
- 最初の segment で Previous → 最後へ。

ChordMode / SoloMode 共通です。segment 変更時、現在鳴っているソロ音はそのまま保持し、
次に演奏キーを押した時点で新しい segment / LPC に基づいて解決します（held note を
再解釈しない）。

## 起動

```powershell
python -m apps.desktop_debug.midi_controller_harness --mode solo --midi-in "H12MIDI-Pro 1" --profile apps/desktop_debug/controller_profiles/ccp16_solo.json
```

ハードウェア無しの確認は `--self-test`（`--dry-run` で OUT ログも表示）:

```powershell
python -m apps.desktop_debug.midi_controller_harness --mode solo --self-test --dry-run
```
