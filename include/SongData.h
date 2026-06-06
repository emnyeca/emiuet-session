#pragma once

#include <Arduino.h>

namespace emiuet {

struct SongStep {
  const char *section;
  uint16_t bar;
  const char *chord;
};

class SongPosition {
public:
  void begin();
  void next();
  void previous();
  const SongStep &current() const;
  uint8_t index() const { return index_; }
  uint8_t count() const;

private:
  uint8_t index_ = 0;
};

} // namespace emiuet
