#include "SongData.h"

namespace emiuet {

namespace {

constexpr SongStep kFixedSong[] = {
    {"A", 1, "Dm7"},
    {"A", 2, "G7"},
    {"A", 3, "Cmaj7"},
    {"A", 4, "Cmaj7"},
    {"B", 5, "Fm7"},
    {"B", 6, "Bb7"},
    {"B", 7, "Ebmaj7"},
    {"B", 8, "A7alt"},
};

} // namespace

void SongPosition::begin() {
  index_ = 0;
}

void SongPosition::next() {
  index_ = (index_ + 1) % count();
}

void SongPosition::previous() {
  index_ = index_ == 0 ? count() - 1 : index_ - 1;
}

const SongStep &SongPosition::current() const {
  return kFixedSong[index_];
}

uint8_t SongPosition::count() const {
  return static_cast<uint8_t>(sizeof(kFixedSong) / sizeof(kFixedSong[0]));
}

} // namespace emiuet
