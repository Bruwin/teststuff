// World: the deterministic simulation root. M0 holds only the clock and the state
// hash; lanes, machines and power land in M6+. The tick order is frozen and
// versioned (SIM-06): changing it changes every save, so it needs a decision
// record and human approval (AGT-06).
#pragma once

#include <cstdint>

#include "core/fixed.h"

namespace fct::sim {

// Bump when the order or meaning of a tick step changes.
inline constexpr std::uint32_t kTickOrderVersion = 1;
inline constexpr std::int32_t kTicksPerSecond = 30;

class World {
public:
    explicit World(std::uint32_t seed);

    // One fixed step. Called only by app/, never by render or ui.
    void tick();

    std::uint64_t tick_count() const { return tick_; }
    fct::Fix clock() const { return clock_; }
    std::uint32_t seed() const { return seed_; }

    // Order-independent of pointers by construction: walks integers only.
    std::uint64_t hash() const;

private:
    std::uint32_t seed_ = 0;
    std::uint64_t tick_ = 0;
    fct::Fix clock_;
    std::uint64_t hash_state_ = 0;
};

}  // namespace fct::sim
