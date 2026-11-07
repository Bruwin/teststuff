#include <cstdint>

#include "core/fixed_step.h"
#include "harness.h"

namespace {

constexpr std::int64_t kStep = 33'333'333;  // 1/30 s in ns, truncated the same way the app does

std::uint64_t as_u64(int value) { return static_cast<std::uint64_t>(value); }

}  // namespace

TEST_CASE(fixed_step_first_advance_only_establishes_a_baseline) {
    fct::FixedStepClock clock(kStep, 4);
    CHECK_EQ(clock.advance(1'000'000'000), 0);
    CHECK_EQ(clock.tick_count(), as_u64(0));
}

TEST_CASE(fixed_step_does_not_run_on_zero_length_frames) {
    fct::FixedStepClock clock(kStep, 4);
    clock.advance(0);
    for (int frame = 0; frame < 10; ++frame) {
        CHECK_EQ(clock.advance(0), 0);
    }
    CHECK_EQ(clock.tick_count(), as_u64(0));
}

TEST_CASE(fixed_step_runs_exactly_one_tick_per_step_of_time) {
    fct::FixedStepClock clock(kStep, 4);
    std::int64_t now_ns = 0;
    clock.advance(now_ns);
    for (int tick = 0; tick < 10; ++tick) {
        now_ns += kStep;
        CHECK_EQ(clock.advance(now_ns), 1);
    }
    CHECK_EQ(clock.tick_count(), as_u64(10));
    CHECK(clock.alpha() < 0.01f);
}

TEST_CASE(fixed_step_holds_thirty_ticks_per_second_of_wall_time) {
    // 3600 frames of 16.6667 ms is 59.9999976 s, so 1799 whole ticks: the clock
    // must not invent the tick that has not happened yet.
    fct::FixedStepClock clock(kStep, 8);
    std::int64_t now_ns = 0;
    clock.advance(now_ns);

    std::uint64_t total = 0;
    for (int frame = 0; frame < 3600; ++frame) {
        now_ns += 16'666'666;
        total += as_u64(clock.advance(now_ns));
    }
    CHECK_EQ(total, as_u64(1799));
    CHECK(clock.alpha() > 0.99f);
    CHECK(clock.alpha() < 1.0f);
}

TEST_CASE(fixed_step_reports_a_partial_step_as_alpha) {
    fct::FixedStepClock clock(kStep, 4);
    clock.advance(0);
    CHECK_EQ(clock.advance(kStep / 2), 0);
    CHECK(clock.alpha() > 0.49f);
    CHECK(clock.alpha() < 0.51f);
}

TEST_CASE(fixed_step_drops_the_backlog_beyond_the_catch_up_cap) {
    // A 500 ms stall is clamped to the 250 ms hitch window, then capped at four
    // ticks per frame; the remaining three are counted, not silently lost.
    fct::FixedStepClock clock(kStep, 4);
    clock.advance(0);
    CHECK_EQ(clock.advance(500'000'000), 4);
    CHECK_EQ(clock.dropped_ticks(), as_u64(3));
}

TEST_CASE(fixed_step_ignores_a_backwards_clock) {
    fct::FixedStepClock clock(kStep, 4);
    clock.advance(1'000'000'000);
    CHECK_EQ(clock.advance(500'000'000), 0);
    CHECK_EQ(clock.tick_count(), as_u64(0));
    CHECK_EQ(clock.alpha(), 0.0f);
}

TEST_CASE(fixed_step_tick_counter_matches_the_ticks_returned) {
    fct::FixedStepClock clock(kStep, 4);
    std::int64_t now_ns = 0;
    clock.advance(now_ns);
    std::uint64_t returned = 0;
    for (int frame = 0; frame < 100; ++frame) {
        now_ns += 7'000'000;  // irregular frame times, ~7 ms
        returned += as_u64(clock.advance(now_ns));
    }
    CHECK_EQ(clock.tick_count(), returned);
}
