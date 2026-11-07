#include "harness.h"
#include "sim/world.h"

namespace {

std::uint64_t run_ticks(std::uint32_t seed, std::uint64_t ticks) {
    fct::sim::World world(seed);
    for (std::uint64_t i = 0; i < ticks; ++i) {
        world.tick();
    }
    return world.hash();
}

}  // namespace

TEST_CASE(world_hash_is_reproducible_for_the_same_seed) {
    // This is the property that saves, replays and co-op all rest on (SIM-03).
    CHECK_EQ(run_ticks(1, 300), run_ticks(1, 300));
}

TEST_CASE(world_hash_differs_for_a_different_seed) {
    CHECK(run_ticks(1, 300) != run_ticks(2, 300));
}

TEST_CASE(world_hash_depends_on_tick_count) {
    CHECK(run_ticks(7, 10) != run_ticks(7, 11));
}

TEST_CASE(world_clock_advances_one_tick_at_a_time) {
    fct::sim::World world(0);
    CHECK_EQ(world.tick_count(), static_cast<std::uint64_t>(0));
    CHECK_EQ(world.clock().raw(), 0);

    world.tick();
    CHECK_EQ(world.tick_count(), static_cast<std::uint64_t>(1));
    CHECK_EQ(world.clock().raw(), fct::Fix::from_ratio(1, fct::sim::kTicksPerSecond).raw());

    for (int i = 1; i < fct::sim::kTicksPerSecond; ++i) {
        world.tick();
    }
    CHECK_EQ(world.clock().to_int(), 1);
}

TEST_CASE(world_tick_order_version_is_pinned) {
    // Bumping this is an AGT-06 event: it invalidates every save and golden.
    CHECK_EQ(fct::sim::kTickOrderVersion, static_cast<std::uint32_t>(1));
}
