#include "KeyScanner.h"

namespace emiuet {

void KeyScanner::begin() {
  pinMode(kMuxS0Pin, OUTPUT);
  pinMode(kMuxS1Pin, OUTPUT);
  pinMode(kMuxS2Pin, OUTPUT);
  pinMode(kMuxS3Pin, OUTPUT);
  pinMode(kMuxAnalogPin, INPUT);

  analogReadResolution(10);
  analogReadAveraging(4);

  for (uint8_t i = 0; i < kKeyCount; ++i) {
    const uint16_t initial = readChannel(i);
    keys_[i].raw = initial;
    keys_[i].filtered = initial;
    keys_[i].ccValue = map(initial, 0, kAnalogMax, 0, 127);
  }
}

bool KeyScanner::update() {
  const uint32_t now = micros();
  if (now - lastScanUs_ < kScanIntervalUs) {
    return false;
  }
  lastScanUs_ = now;

  for (uint8_t i = 0; i < kKeyCount; ++i) {
    KeyState &state = keys_[i];
    state.changed = false;
    state.ccChanged = false;

    state.raw = readChannel(i);
    state.filtered = static_cast<uint16_t>((state.filtered * 7UL + state.raw) / 8UL);

    const bool wasPressed = state.pressed;
    if (!state.pressed && state.filtered >= kPressThreshold) {
      state.pressed = true;
    } else if (state.pressed && state.filtered <= kReleaseThreshold) {
      state.pressed = false;
    }
    state.changed = wasPressed != state.pressed;

    const uint8_t nextCc = static_cast<uint8_t>(map(state.filtered, 0, kAnalogMax, 0, 127));
    if (abs(static_cast<int>(nextCc) - static_cast<int>(state.ccValue)) >= kAnalogDeadband) {
      state.ccValue = nextCc;
      state.ccChanged = true;
    }
  }

  ++scanCount_;
  return true;
}

const KeyState &KeyScanner::key(uint8_t index) const {
  return keys_[index];
}

uint8_t KeyScanner::maxPressureCc() const {
  uint8_t maxValue = 0;
  for (uint8_t i = 0; i < kKeyCount; ++i) {
    if (keys_[i].pressed && keys_[i].ccValue > maxValue) {
      maxValue = keys_[i].ccValue;
    }
  }
  return maxValue;
}

void KeyScanner::selectChannel(uint8_t channel) {
  digitalWrite(kMuxS0Pin, channel & 0x01);
  digitalWrite(kMuxS1Pin, channel & 0x02);
  digitalWrite(kMuxS2Pin, channel & 0x04);
  digitalWrite(kMuxS3Pin, channel & 0x08);
}

uint16_t KeyScanner::readChannel(uint8_t channel) {
  selectChannel(channel);
  delayMicroseconds(5);
  return analogRead(kMuxAnalogPin);
}

} // namespace emiuet
