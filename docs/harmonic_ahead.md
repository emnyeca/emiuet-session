# Harmonic Ahead

## 目的

ジャズで多用する「次コードへの先取りフレーズ」を Solo Mode 上で扱う機能です。現在の
timeline 位置（NOW）はそのままに、Solo resolver だけが**次の異なる Chord Context**を
参照します。

## 挙動（hold_until_arrival）

単発 pending ではなく、**次コード到達まで保持**します。

```text
Harmonic Ahead ON（PAD10）:
  target = 次の異なる Chord（既定）
  AIM = target chord context

AHEAD_ACTIVE 中:
  Solo resolver は target を参照する
  複数音フレーズを弾いても解除されない
  PAD10 を再度押しても 2 つ先へは進まない（ignore）

timeline が target step へ到達:
  Harmonic Ahead 自動 OFF（AIM = NOW へ戻る）
```

## Target Policy

```text
AheadTargetPolicy:
  next_distinct_chord   # 既定
  next_step
```

既定が `next_distinct_chord` の理由:

```text
| Dm7 | Dm7 | G7 |
```

現在が 1 つ目の Dm7 のとき、演奏者が期待する先取り先は次 Step の Dm7 ではなく G7 で
あることが多いためです。

## 標準 UX

- 標準は **ahead +1（次の異なる Chord）のみ**。
- 後取り・2 つ先は標準機能にしません。
- 実験用に「直前の異なる Chord」へ向ける `experimental_previous_context`（PAD9）を
  用意しますが、標準としては扱いません。

## 解除条件

- target chord へ timeline が到達（自動 OFF）
- Clear 操作（PAD12 = Clear Ahead / Clear Pending）
- Stop / Start / Panic
- Continue（続き再生で playhead は戻さないが、演奏中の一時状態は事故防止で clear）

## PAD 配置（Auto Follow 時、`ccp16_autofollow.json`）

```text
PAD5      PAD6      PAD7      PAD8
Resolve   Core↑     LPC↑      Chromatic↑

PAD1      PAD2      PAD3      PAD4
Repeat    Core↓     LPC↓      Chromatic↓

PAD9   Experimental Previous Context
PAD10  Harmonic Ahead
PAD11  Pending Skip +1
PAD12  Clear Ahead / Clear Pending
PAD13  Pending Octave Down
PAD14  Pending Octave Up
PAD15  Resync
PAD16  Panic
```

PAD10 は OFF 中のみ ON にし、AHEAD_ACTIVE 中は ignore（連打で 2 つ先へ進まない）。

## Solo Resolver との接続

```text
effective_context =
  harmonic_ahead.target_context   (Harmonic Ahead 中)
  current_context()               (それ以外)
```

Solo resolver はこの `effective_context` の core / lpc を見て次の音を決めます。表示は
NOW（timeline 現在）/ AIM（resolver 参照）/ NEXT（次の異なる Chord）を分けます
（`docs/auto_follow.md`）。
