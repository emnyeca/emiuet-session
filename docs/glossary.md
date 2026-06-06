# Glossary

This glossary collects key terms and concepts used throughout the Emiuet Session project.  It is intended as a quick reference for developers and collaborators.
この用語集はEmiuet Sessionプロジェクトで使用する主要な用語と概念をまとめたものです。開発者や協力者のための簡易リファレンスとして利用できます。

## Changes

Changes is a tool for creating and managing chord progressions and song structures.  Emiuet Session imports song data from Changes to determine the current section, bar and chord.
Changesはコード進行や曲の構造を作成・管理するためのツールです。Emiuet SessionはChangesから楽曲データを読み込み、現在のセクション、小節、コードを決定します。

## Local Pitch Collection (LPC)

The Local Pitch Collection is the set of notes derived from the current harmonic context.  It combines chord tones, modal notes and appropriate tensions.  The LPC changes as the song progresses.
Local Pitch Collectionは現在の和声コンテキストから導出される演奏可能な音の集合です。コードトーン、モード音、適切なテンションを組み合わせます。LPCは曲の進行に伴って変化します。

## Position

The current location within the song, including section, bar and beat.  Navigating the position allows the performer to move through the chord progression during a session.
曲中の現在位置を指します。セクション、小節、拍を含みます。位置を移動することで演奏者は進行をナビゲートできます。

## Performance Surface

The interface through which the performer plays notes and controls Emiuet Session.  In the prototype, this consists of some analogue keys; may use hall‑effect switches or other expressive sensors.
演奏者が音を奏で、Emiuet Sessionを操作するためのインターフェースです。プロトタイプでは数個のアナログキーで構成され、Hall‑effectスイッチや他の表現力豊かなセンサーを使用する計画です。

## Synth Engine

The internal sound generator based on the Teensy Audio Library.  It produces audio for standalone operation and can be configured with different timbres and effects.
Teensy Audio Libraryに基づいた内蔵音源です。単体動作のためのオーディオを生成し、さまざまな音色やエフェクトを設定できます。

## LPC Engine

The firmware component that converts chord and position information into the current Local Pitch Collection.  It applies rules for chord tones, scales, tensions and alterations.
ChordとPosition情報をLocal Pitch Collectionに変換するファームウェアのコンポーネントです。Chord Tone、スケール、テンション、アルタード処理のルールを適用します。


## Session

A live performance context in which the performer navigates harmony in real time.  Emiuet Session is designed to support jazz sessions and machine‑live improvisation.
演奏者がリアルタイムに和声をナビゲートするライブパフォーマンスの状況を指します。Emiuet Sessionはジャズセッションやマシンライブの即興演奏をサポートするために設計されています。


## TRS MIDI Type‑A

A 3.5 mm MIDI standard that uses tip and ring to transmit current‑loop MIDI signals.  Emiuet Session uses TRS MIDI Type‑A for direct connection to devices such as Digitone.
ティップとリングを使って電流ループMIDI信号を送る3.5 mmのMIDI規格です。Emiuet SessionはDigitoneなどの機器へ直接接続するためにTRS MIDI Type‑Aを使用します。