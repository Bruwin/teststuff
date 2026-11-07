// merge_station_demo.cpp — 120 s line simulation that drives MergeStation.
//
// A roller line meets a side lane at the merge. Items are 0.4 m long and travel
// at 0.30 m/s; they accumulate behind the gate blade when it is closed. One
// main-line item is scanned as bad and must leave through the diverter's reject
// port; two side-lane items must merge into gaps between main-line items.
//
// Set MERGE_TRACE=1 to print a one-second sample of poses and item positions.
//
// Every photo-eye in the simulation sits where the asset geometry puts it, so
// the controller only ever sees the four beams the models actually carry. The
// simulation asserts the interlocks the assets cannot enforce on their own:
//
//   * the chain never rises under a main-line item,
//   * the side item never crosses the throat together with a main item,
//   * no item passes a closed blade,
//   * joint values stay inside limits_m and never exceed the slew rates.
//
// Build and run:  g++ -std=c++17 -O2 -Wall -Wextra engine/merge_station_demo.cpp
//
// Station-local x positions, metres, from the module voxel layouts:
//   gate      0.0 .. 1.0     blade 0.4375 .. 0.5, eyes 0.19 / 0.78
//   diverter  1.0 .. 3.0     eye 1.47, pusher plate 1.81 .. 2.19
//   merge     3.0 .. 5.0     entry beam 3.94, throat beam 4.25,
//                            chain strip 4.50 .. 4.91

#include "merge_station.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

namespace {

constexpr float kBedSpeed = 0.30f;    // roller line
constexpr float kChainSpeed = 0.25f;  // pop-up transfer pull
constexpr float kItemLen = 0.40f;
constexpr float kItemGap = 0.06f;
constexpr float kEyeLen = 0.09f;

constexpr float kBladeX = 0.44f;       // blade front face, no passing beyond
constexpr float kBladeClear = -0.26f;  // blade low enough to let an item through
constexpr float kEntryEye = 0.19f;
constexpr float kExitEye = 0.78f;
constexpr float kDiverterEye = 1.47f;
constexpr float kMergeEntryEye = 3.94f;  // merge-entry beam [3.94 .. 4.03]
constexpr float kPusherZone0 = 1.81f;
constexpr float kPusherZone1 = 2.19f;
constexpr float kThroatEye = 4.25f;
constexpr float kStrip0 = 4.50f;
constexpr float kStrip1 = 4.91f;
constexpr float kSideEntry = 4.13f;  // side lane hands over at the chamfer
// The chain keeps driving the item until its tail is past the strip, so the
// handover happens at strip end (4.91) + one item length.
constexpr float kSideExit = 5.40f;
constexpr float kExitLine = 6.40f;

constexpr float kSpawnEvery = 2.60f;
constexpr float kStopFeeding = 40.0f;
constexpr float kRejectId = 2;  // the scanner flags the second main item

struct Item {
    float x;       // leading edge
    float prev_x;
    int id;
    bool flagged;
};

int failures = 0;

void fail(const char* what, float t) {
    ++failures;
    if (failures <= 12) std::printf("  FAIL  %-44s at %6.2f s\n", what, t);
    else if (failures == 13) std::printf("  ... further failures suppressed\n");
}

// `x` is always the leading edge of an item, so its body spans [x-len, x].
bool in_zone(float item_x, float zone0, float zone1) {
    return item_x > zone0 && item_x - kItemLen < zone1;
}

}  // namespace

int main() {
    factory::MergeStation station;
    const factory::MergeStationConfig cfg = station.config();

    std::vector<Item> line;  // leader first
    auto sort_line = [&line] {
        std::sort(line.begin(), line.end(),
                  [](const Item& a, const Item& b) { return a.x > b.x; });
    };

    int next_id = 1;
    float next_spawn = 0.0f;
    const float side_arrivals[] = {6.0f, 32.0f};
    std::size_t next_side = 0;
    bool side_active = false;
    float side_x = 0.0f;
    int merged = 0, rejected = 0, delivered = 0;

    const float dt = 0.01f;
    const float t_end = 120.0f;
    float prev_gate = station.pose().gate_m;
    float prev_pusher = station.pose().pusher_m;
    float prev_transfer = station.pose().transfer_m;
    factory::MergeStation::State prev_state = station.state();

    std::printf("time    state transitions (pose after the step)\n");
    const bool trace = std::getenv("MERGE_TRACE") != nullptr;
    int trace_tick = 0;

    for (float t = 0.0f; t <= t_end; t += dt) {
        // --- feeding -------------------------------------------------------
        if (t >= kStopFeeding) next_spawn = 1e9f;
        if (t >= next_spawn) {
            line.push_back(Item{-0.50f, -0.50f, next_id, next_id == kRejectId});
            sort_line();
            ++next_id;
            next_spawn += kSpawnEvery;
        }
        if (next_side < 2 && !side_active && t >= side_arrivals[next_side]) {
            side_active = true;
            side_x = kSideEntry;
            ++next_side;
            std::printf("[%6.2f s] side item queued at %.2f m\n", t, side_x);
        }

        // --- photo-eyes (exactly the four beams the assets carry) ----------
        auto blocked = [&line](float s) {
            for (const Item& it : line)
                if (it.x > s && it.x - kItemLen < s + kEyeLen) return true;
            return false;
        };
        bool reject_here = false;
        for (const Item& it : line)
            if (it.flagged && in_zone(it.x, kDiverterEye, kDiverterEye + kEyeLen))
                reject_here = true;

        // the side item only occupies the throat once the chain has taken it
        const bool side_in_throat = side_active && station.pose().transfer_m > 0.06f;

        factory::MergeStation::Inputs in;
        in.gate_entry = blocked(kEntryEye);
        in.gate_exit = blocked(kExitEye);
        in.diverter_eye = blocked(kDiverterEye);
        in.merge_entry = blocked(kMergeEntryEye);
        in.throat = blocked(kThroatEye) || side_in_throat;
        in.side_waiting = side_active;
        in.reject_item = reject_here;
        in.downstream_ready = true;

        station.step(dt, in);
        const factory::MergeStation::Pose p = station.pose();

        if (trace && ++trace_tick % 100 == 0) {
            std::printf("  %6.2f %-6s blade %6.3f plate %5.3f chain %5.3f |", t,
                        factory::merge_state_name(station.state()), p.gate_m, p.pusher_m,
                        p.transfer_m);
            for (const Item& it : line) std::printf(" %d@%.2f%s", it.id, it.x, it.flagged ? "*" : "");
            if (side_active) std::printf(" side@%.2f", side_x);
            std::printf("\n");
        }

        if (station.state() != prev_state) {
            std::printf("[%6.2f s] %-6s -> %-6s   blade %6.3f  plate %5.3f  chain %5.3f\n",
                        t, factory::merge_state_name(prev_state),
                        factory::merge_state_name(station.state()), p.gate_m, p.pusher_m,
                        p.transfer_m);
            prev_state = station.state();
        }

        // --- actuator sanity ----------------------------------------------
        if (std::fabs(p.gate_m - prev_gate) > cfg.gate_speed_mps * dt + 1e-4f)
            fail("gate slew exceeded", t);
        if (std::fabs(p.pusher_m - prev_pusher) > cfg.pusher_speed_mps * dt + 1e-4f)
            fail("pusher slew exceeded", t);
        if (std::fabs(p.transfer_m - prev_transfer) > cfg.transfer_speed_mps * dt + 1e-4f)
            fail("transfer slew exceeded", t);
        if (p.gate_m < cfg.gate_open_m - 1e-4f || p.gate_m > cfg.gate_closed_m + 1e-4f)
            fail("blade outside limits_m", t);
        if (p.pusher_m < -1e-4f || p.pusher_m > cfg.pusher_stroke_m + 1e-4f)
            fail("pusher outside limits_m", t);
        if (p.transfer_m < -1e-4f || p.transfer_m > cfg.transfer_up_m + 1e-4f)
            fail("transfer outside limits_m", t);
        prev_gate = p.gate_m;
        prev_pusher = p.pusher_m;
        prev_transfer = p.transfer_m;

        // --- the roller line ----------------------------------------------
        float limit = 1e9f;  // leader runs free, followers stack up behind
        for (Item& it : line) {
            // the blade only holds items that have not passed it yet
            float item_limit = limit;
            if (p.gate_m > kBladeClear && it.prev_x <= kBladeX)
                item_limit = std::min(item_limit, kBladeX - 0.002f);
            const float target = std::min(it.x + kBedSpeed * dt, item_limit);
            if (target > it.x) it.x = target;
            limit = it.x - (kItemLen + kItemGap);

            if (it.prev_x < kBladeX && it.x > kBladeX + 0.005f && p.gate_m > kBladeClear)
                fail("item pushed through a closed blade", t);
            it.prev_x = it.x;
            if (it.flagged && it.x > kThroatEye - kItemLen)
                fail("flagged item reached the merge", t);
        }

        // --- the pop-up chain transfer ------------------------------------
        if (side_active && p.transfer_m > 0.06f) {
            side_x = std::min(side_x + kChainSpeed * dt, kSideExit);
            if (side_x >= kSideExit) {
                line.push_back(Item{kSideExit, kSideExit, next_id++, false});
                sort_line();
                side_active = false;
                ++merged;
                std::printf("[%6.2f s] side item merged into the flow\n", t);
            }
        }

        if (p.transfer_m > 0.02f) {
            for (const Item& it : line)
                if (in_zone(it.x, kStrip0, kStrip1))
                    fail("chain raised under a main-line item", t);
            if (side_active)
                for (const Item& it : line)
                    if (in_zone(it.x, kSideEntry, kStrip1))
                        fail("side item collided in the throat", t);
        }

        // --- pusher ejection ----------------------------------------------
        if (p.pusher_m >= 0.28f) {
            for (std::size_t i = 0; i < line.size(); ++i) {
                if (line[i].flagged && in_zone(line[i].x, kPusherZone0, kPusherZone1)) {
                    std::printf("[%6.2f s] item %d ejected at the reject port (plate %.2f m)\n",
                                t, line[i].id, p.pusher_m);
                    line.erase(line.begin() + static_cast<std::ptrdiff_t>(i));
                    ++rejected;
                    break;
                }
            }
        }

        // --- items that left the station ----------------------------------
        for (std::size_t i = line.size(); i-- > 0;) {
            if (line[i].x > kExitLine) {
                ++delivered;
                line.erase(line.begin() + static_cast<std::ptrdiff_t>(i));
            }
        }
    }

    std::printf("\ndelivered %d, side merges %d, rejected %d, final state %s\n", delivered,
                merged, rejected, factory::merge_state_name(station.state()));

    if (merged != 2) fail("expected two side-lane merges", t_end);
    if (rejected != 1) fail("expected one rejection", t_end);
    if (!line.empty()) fail("line did not drain", t_end);
    if (station.state() != factory::MergeStation::State::idle)
        fail("station not idle at the end", t_end);

    if (failures > 0) {
        std::printf("%d check(s) FAILED\n", failures);
        return 1;
    }
    std::printf("all checks passed\n");
    return 0;
}
