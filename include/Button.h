#pragma once

#include <Arduino.h>
#include "Phase1Config.h"

namespace emiuet {

class Button {
public:
  explicit Button(uint8_t pin) : pin_(pin) {}

  void begin() {
    pinMode(pin_, INPUT_PULLUP);
    stableState_ = digitalRead(pin_);
    lastReading_ = stableState_;
  }

  bool fell() {
    const bool reading = digitalRead(pin_);
    const uint32_t now = millis();

    if (reading != lastReading_) {
      lastReading_ = reading;
      lastChangeMs_ = now;
    }

    if ((now - lastChangeMs_) >= kButtonDebounceMs && reading != stableState_) {
      stableState_ = reading;
      return stableState_ == LOW;
    }

    return false;
  }

private:
  uint8_t pin_;
  bool stableState_ = HIGH;
  bool lastReading_ = HIGH;
  uint32_t lastChangeMs_ = 0;
};

} // namespace emiuet
