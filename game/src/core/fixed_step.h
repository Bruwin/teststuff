// Fixed-step accumulator. Turns wall-clock nanoseconds into whole simulation
// ticks, so the sim always advances in equal steps regardless of frame time
// (PLAN.md section 4.5). Integer-only and free of OS calls, which is why it can
// be tested against synthetic time in a unit test instead of a real clock.
#pragma once

#include <cstdint>

#include "core/log.h"

namespace fct {

class FixedStepClock {
public:
    // A stall longer than this is treated as a hitch, not as work to catch up on:
    // running 400 ticks after a breakpoint is never what the player wants.
    static constexpr std::int64_t kMaxCatchUpNs = 250'000'000;  // 250 ms

    FixedStepClock(std::int64_t step_ns, int max_ticks_per_frame) {
        FCT_ASSERT(step_ns > 0);
        FCT_ASSERT(max_ticks_per_frame > 0);
        step_ns_ = step_ns;
        max_ticks_per_frame_ = max_ticks_per_frame;
    }

    // Returns how many ticks to run now. The first call only establishes the
    // baseline, so a frame never runs with a bogus delta.
    int advance(std::int64_t now_ns) {
        if (!started_) {
            started_ = true;
            last_ns_ = now_ns;
            return 0;
        }

        std::int64_t delta_ns = now_ns - last_ns_;
        last_ns_ = now_ns;
        if (delta_ns < 0) {
            delta_ns = 0;  // a non-monotonic source must not rewind the sim
        }
        if (delta_ns > kMaxCatchUpNs) {
            delta_ns = kMaxCatchUpNs;
        }

        accumulator_ns_ += delta_ns;
        int ticks = static_cast<int>(accumulator_ns_ / step_ns_);
        if (ticks > max_ticks_per_frame_) {
            dropped_ticks_ += static_cast<std::uint64_t>(ticks - max_ticks_per_frame_);
            ticks = max_ticks_per_frame_;
            accumulator_ns_ %= step_ns_;  // drop the backlog rather than spiral
        } else {
            accumulator_ns_ -= static_cast<std::int64_t>(ticks) * step_ns_;
        }

        tick_count_ += static_cast<std::uint64_t>(ticks);
        return ticks;
    }

    // Fraction of a step already elapsed, for render interpolation.
    float alpha() const {
        return static_cast<float>(accumulator_ns_) / static_cast<float>(step_ns_);
    }

    std::uint64_t tick_count() const { return tick_count_; }
    std::uint64_t dropped_ticks() const { return dropped_ticks_; }
    std::int64_t step_ns() const { return step_ns_; }

private:
    std::int64_t step_ns_ = 0;
    int max_ticks_per_frame_ = 1;
    std::int64_t last_ns_ = 0;
    std::int64_t accumulator_ns_ = 0;
    std::uint64_t tick_count_ = 0;
    std::uint64_t dropped_ticks_ = 0;
    bool started_ = false;
};

// Convenience: the sim runs at a fixed 30 Hz (PLAN.md section 4.5).
inline constexpr std::int64_t kSimStepNs = 1'000'000'000 / 30;

}  // namespace fct
