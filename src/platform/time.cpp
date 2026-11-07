#include "platform/time.h"

#include <chrono>
#include <thread>

namespace fct::platform {
namespace {

using SteadyClock = std::chrono::steady_clock;

}  // namespace

std::int64_t monotonic_ns() {
    return static_cast<std::int64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(SteadyClock::now().time_since_epoch())
            .count());
}

void sleep_for_ns(std::int64_t duration_ns) {
    if (duration_ns > 0) {
        std::this_thread::sleep_for(std::chrono::nanoseconds(duration_ns));
    }
}

}  // namespace fct::platform
