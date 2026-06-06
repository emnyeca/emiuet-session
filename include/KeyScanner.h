#pragma once

#include <Arduino.h>
#include "Phase1Config.h"

namespace emiuet {

struct KeyState {
  uint16_t raw = 0;
  uint16_t filtered = 0;
  uint8_t ccValue = 0;
  bool pressed = false;
  bool changed = false;
  bool ccChanged = false;
};

class KeyScanner {
public:
  void begin();
  bool update();
  const KeyState &key(uint8_t index) const;
  uint8_t maxPressureCc() const;
  uint16_t scanCount() const { return scanCount_; }

private:
  void selectChannel(uint8_t channel);
  uint16_t readChannel(uint8_t channel);

  KeyState keys_[kKeyCount];
  uint32_t lastScanUs_ = 0;
  uint16_t scanCount_ = 0;
};

} // namespace emiuet
