#pragma once

#include <Arduino.h>
#include "KeyScanner.h"
#include "SongData.h"

namespace emiuet {

class MidiEngine {
public:
  void begin();
  void sendKeyCc(uint8_t keyIndex, uint8_t value);
  void sendPressure(uint8_t value);
  void sendPosition(const SongPosition &position);
  void flushUsb();

private:
  void sendControlChange(uint8_t controller, uint8_t value);
};

} // namespace emiuet
