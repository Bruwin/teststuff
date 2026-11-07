// Time source. Monotonic only: sim pacing must never see a wall-clock jump
// (NTP corrections, DST) turn into a burst of ticks.
#pragma once

#include <cstdint>

namespace fct::platform {

// Nanoseconds since an unspecified monotonic origin.
std::int64_t monotonic_ns();

// Sleeps at least the requested duration. Precision is the OS scheduler's.
void sleep_for_ns(std::int64_t duration_ns);

}  // namespace fct::platform
