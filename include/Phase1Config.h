#pragma once

#include <Arduino.h>

namespace emiuet {

constexpr uint8_t kKeyCount = 16;

// CD74HC4067 address pins. These are ordinary GPIO pins on Teensy 4.1.
constexpr uint8_t kMuxS0Pin = 2;
constexpr uint8_t kMuxS1Pin = 3;
constexpr uint8_t kMuxS2Pin = 4;
constexpr uint8_t kMuxS3Pin = 5;

// CD74HC4067 SIG output connected to a Teensy analog input.
constexpr uint8_t kMuxAnalogPin = A0;

// Manual navigation buttons. Wire each switch to GND; internal pull-ups are used.
constexpr uint8_t kStepForwardPin = 6;
constexpr uint8_t kStepBackPin = 7;

// TRS MIDI Type-A uses the UART TX path through the standard MIDI current-loop
// output circuit. Breadboard wiring is documented in docs/phase1_breadboard.md.
constexpr uint8_t kTrsMidiTxPin = 1; // Serial1 TX on Teensy 4.1
constexpr uint32_t kTrsMidiBaud = 31250;

constexpr uint8_t kMidiChannel = 1;
constexpr uint8_t kPressureCc = 95;
constexpr uint8_t kPositionCc = 20;
constexpr uint8_t kKeyBaseCc = 40;

constexpr uint16_t kAnalogMax = 1023;
constexpr uint16_t kPressThreshold = 620;
constexpr uint16_t kReleaseThreshold = 520;
constexpr uint16_t kAnalogDeadband = 3;
constexpr uint32_t kScanIntervalUs = 1000;
constexpr uint32_t kCcMinIntervalMs = 8;
constexpr uint32_t kSerialReportIntervalMs = 100;
constexpr uint32_t kButtonDebounceMs = 20;

} // namespace emiuet
