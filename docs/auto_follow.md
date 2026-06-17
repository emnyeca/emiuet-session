# Auto Follow

## 目的

Solo Mode を Digitone II / EUB Changes 連携の machine live 用インターフェースとして
実用化するためのモードです。手動 Advance に加えて、Digitone II の Transport /
MIDI Clock に追従して current harmonic step を自動更新します。

ソロに集中している間も現在位置を見失わないことが狙いです。手動 Advance は残しますが、
machine live の主導線は Auto Follow です。

## 同期の基準

Auto Follow は**原曲の小節・テンポではなく**、Digitone II 上の Step timeline に同期
します。詳細は `docs/digitone_step_timeline.md`。

```text
AdvanceMode:
  manual        # 既存の手動 segment advance
  auto_follow   # MIDI Clock + compiled timeline に追従
```

## Transport（FA / FB / FC / F8）

MIDI Realtime の受信は desktop adapter 側で行い、core へは抽象 `TransportEvent`
（START / CONTINUE / STOP / CLOCK）として渡します（core は mido 非依存）。

```text
TransportState: STOPPED / RUNNING
```

- **FA Start**: 頭から再生。`RUNNING`、playhead を 0 へ reset、harmonic ahead /
  pending / solo cursor を clear、全音 NoteOff。
- **FB Continue**: 続きから再生。**Start 扱いにしない**（playhead を reset しない）。
  事故防止のため harmonic ahead / pending は clear する。
- **FC Stop**: `STOPPED`、全音 NoteOff、harmonic ahead / pending を clear。
  `StopPolicy = reset_to_head`（既定）なら playhead を 0 へ。
- **F8 Clock**: `RUNNING` 中のみ tick を進める。`STOPPED` 中は進めない。

> Continue を Start 扱いすると同期が破綻するため、Transport テストで必ず保証します
> （`tests/test_transport.py`）。

## NOW / AIM / NEXT

DisplayState では以下を分けます。

- **NOW**: timeline 上の現在 Chord。
- **AIM**: Solo resolver が実際に参照している Chord Context（Harmonic Ahead 中は
  その target）。
- **NEXT**: 次に異なる Chord。

表示例（Harmonic Ahead 中）:

```text
AIM  G7   AHEAD
NOW  Dm7   t=0
NEXT G7
TR   running  auto_follow  SOLO
```

## CLI

```powershell
python -m apps.desktop_debug.midi_controller_harness `
  --mode solo `
  --advance-mode auto-follow `
  --clock-source midi-clock `
  --transport-source midi-transport `
  --timeline-basis digitone-step `
  --ahead-target next-distinct-chord `
  --midi-in "H12MIDI-Pro 1" `
  --midi-out "H12MIDI-Pro 1" `
  --profile apps/desktop_debug/controller_profiles/ccp16_autofollow.json
```

PowerShell で複数行に分ける場合は行末に `\` ではなくバッククォート `` ` `` を使います。

ハードウェアなしの確認:

```powershell
python -m apps.desktop_debug.midi_controller_harness --mode solo --advance-mode auto-follow --self-test --dry-run
```

`clock-source` / `transport-source` は v0 では midi-clock / midi-transport のみ実配線。
`timeline-basis` は digitone-step を期待（それ以外は警告）。

## 表示の間引き

F8 は高頻度なので、harness は clock のたびには全画面描画しません。NOW chord の変化・
note 発音・Harmonic Ahead 状態の変化・Transport イベントのときだけ描画します。

## Harmonic Ahead

次コード先取りフレーズ用。詳細は `docs/harmonic_ahead.md`。
