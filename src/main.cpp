#include <Arduino.h>

#include "Button.h"
#include "KeyScanner.h"
#include "MidiEngine.h"
#include "SongData.h"

using namespace emiuet;

KeyScanner keyScanner;
MidiEngine midiEngine;
SongPosition songPosition;
Button stepForward(kStepForwardPin);
Button stepBack(kStepBackPin);

uint32_t lastCcMs = 0;
uint32_t lastSerialReportMs = 0;
uint8_t lastPressure = 255;

void printSongPosition() {
  const SongStep &step = songPosition.current();
  Serial.print("position=");
  Serial.print(songPosition.index());
  Serial.print("/");
  Serial.print(songPosition.count());
  Serial.print(" section=");
  Serial.print(step.section);
  Serial.print(" bar=");
  Serial.print(step.bar);
  Serial.print(" chord=");
  Serial.println(step.chord);
}

void reportKeys() {
  Serial.print("scan=");
  Serial.print(keyScanner.scanCount());
  Serial.print(" pressure=");
  Serial.print(keyScanner.maxPressureCc());
  Serial.print(" keys=");
  for (uint8_t i = 0; i < kKeyCount; ++i) {
    const KeyState &key = keyScanner.key(i);
    Serial.print(i);
    Serial.print(':');
    Serial.print(key.filtered);
    Serial.print(key.pressed ? '*' : '-');
    if (i + 1 < kKeyCount) {
      Serial.print(',');
    }
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);

  keyScanner.begin();
  midiEngine.begin();
  songPosition.begin();
  stepForward.begin();
  stepBack.begin();

  delay(500);
  Serial.println("Emiuet Session Phase 1 prototype");
  printSongPosition();
  midiEngine.sendPosition(songPosition);
}

void loop() {
  midiEngine.flushUsb();

  if (stepForward.fell()) {
    songPosition.next();
    printSongPosition();
    midiEngine.sendPosition(songPosition);
  }

  if (stepBack.fell()) {
    songPosition.previous();
    printSongPosition();
    midiEngine.sendPosition(songPosition);
  }

  if (keyScanner.update()) {
    const uint32_t nowMs = millis();
    if (nowMs - lastCcMs >= kCcMinIntervalMs) {
      for (uint8_t i = 0; i < kKeyCount; ++i) {
        const KeyState &key = keyScanner.key(i);
        if (key.changed || (key.pressed && key.ccChanged)) {
          midiEngine.sendKeyCc(i, key.pressed ? key.ccValue : 0);
        }
      }

      const uint8_t pressure = keyScanner.maxPressureCc();
      if (pressure != lastPressure) {
        midiEngine.sendPressure(pressure);
        lastPressure = pressure;
      }
      lastCcMs = nowMs;
    }

    if (nowMs - lastSerialReportMs >= kSerialReportIntervalMs) {
      reportKeys();
      lastSerialReportMs = nowMs;
    }
  }
}
