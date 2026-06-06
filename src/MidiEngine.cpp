#include "MidiEngine.h"

#include <MIDI.h>

MIDI_CREATE_INSTANCE(HardwareSerial, Serial1, TRSMIDI);

namespace emiuet {

void MidiEngine::begin() {
  Serial1.begin(kTrsMidiBaud);
  TRSMIDI.begin(MIDI_CHANNEL_OMNI);
}

void MidiEngine::sendKeyCc(uint8_t keyIndex, uint8_t value) {
  sendControlChange(kKeyBaseCc + keyIndex, value);
}

void MidiEngine::sendPressure(uint8_t value) {
  sendControlChange(kPressureCc, value);
}

void MidiEngine::sendPosition(const SongPosition &position) {
  sendControlChange(kPositionCc, position.index());
}

void MidiEngine::flushUsb() {
  while (usbMIDI.read()) {
  }
}

void MidiEngine::sendControlChange(uint8_t controller, uint8_t value) {
  usbMIDI.sendControlChange(controller, value, kMidiChannel);
  TRSMIDI.sendControlChange(controller, value, kMidiChannel);
}

} // namespace emiuet
