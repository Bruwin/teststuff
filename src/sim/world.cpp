#include "sim/world.h"

#include <cstdint>

#include "core/hash.h"

namespace fct::sim {

World::World(std::uint32_t seed) : seed_(seed) {
    clock_ = fct::Fix::from_int(0);
    hash_state_ = fct::hash_combine(fct::kHashSeed, static_cast<std::uint64_t>(seed_) + 1);
}

void World::tick() {
    ++tick_;

    // Derived from the tick counter, never accumulated. Adding 1/30 s per tick in
    // Q16.16 truncates 65536/30 and drifts: after 30 ticks the clock read 0.999 s,
    // which is exactly the kind of state divergence the golden tests exist to
    // catch. Deriving time from an integer counter is exact and still integer-only.
    const std::int64_t scaled =
        (static_cast<std::int64_t>(tick_) * fct::Fix::kOne) / kTicksPerSecond;
    clock_ = fct::Fix::from_raw(static_cast<std::int32_t>(scaled));

    // Tick order v1 step 1: clock. Later steps (research, power, fluids,
    // machines, logistics, alerts) are appended in this order, never reordered.
    hash_state_ = fct::hash_combine(hash_state_, 0xA5A5A5A5ull);
    hash_state_ = fct::hash_combine(hash_state_, tick_);
    hash_state_ = fct::hash_combine(hash_state_, static_cast<std::uint64_t>(clock_.raw()));
}

std::uint64_t World::hash() const {
    return fct::hash_combine(hash_state_, static_cast<std::uint64_t>(kTickOrderVersion));
}

}  // namespace fct::sim
