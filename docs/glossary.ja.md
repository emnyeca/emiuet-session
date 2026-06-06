# 用語集

この用語集はEmiuet Sessionプロジェクトで使用する主要な用語と概念をまとめたものです。開発者や協力者のための簡易リファレンスとして利用できます。

## Changes

Changesはコード進行や曲の構造を作成・管理するためのツールです。Emiuet SessionはChangesから楽曲データを読み込み、現在のセクション、小節、コードを決定します。

## Local Pitch Collection (LPC)

Local Pitch Collectionは現在の和声コンテキストから導出される演奏可能な音の集合です。コードトーン、モード音、適切なテンションを組み合わせ、Avoid Noteを排除します。LPCは曲の進行に伴って変化します。

## Position

曲中の現在位置を指します。セクション、小節、拍を含みます。位置を移動することで演奏者は進行をナビゲートできます。

## Performance Surface

演奏者が音を奏で、Emiuet Sessionを操作するためのインターフェースです。プロトタイプでは16個のアナログキーで構成され、将来的にはHall‑effectスイッチや他の表現力豊かなセンサーを使用する計画です。

## Synth Engine

Teensy Audio Libraryに基づいた内蔵音源です。単体動作のためのオーディオを生成し、さまざまな音色やエフェクトを設定できます。

## LPC Engine

ChordとPosition情報をLocal Pitch Collectionに変換するファームウェアのコンポーネントです。Chord Tone、スケール、テンション、アルタード処理のルールを適用します。

## Session

演奏者がリアルタイムに和声をナビゲートするライブパフォーマンスの状況を指します。Emiuet Sessionはジャズセッションやマシンライブの即興演奏をサポートするために設計されています。

## TRS MIDI Type‑A

ティップとリングを使って電流ループMIDI信号を送る3.5 mmのMIDI規格です。Emiuet SessionはDigitoneなどの機器へ直接接続するためにTRS MIDI Type‑Aを使用します。
