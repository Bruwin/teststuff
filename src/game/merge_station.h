// merge_station.h -- sequencing controller for a gate -> diverter -> merge line.
//
// Header-only, C++17, no dependencies, no allocation, no engine types. The
// station drives the three linear joints the asset set already exports:
//
//   conveyor_gate      joint "blade"     limits_m [-0.29, 0.00]   model axis z
//   conveyor_diverter  joint "pusher"    limits_m [ 0.00, 0.30]   model axis y
//   conveyor_merge     joint "transfer"  limits_m [ 0.00, 0.10]   model axis z
//
// Wire the pose onto the rig nodes (model space z -> glTF y, y -> -z):
//
//   gate_node.translation[1]     = station.pose().gate_m;      // 0 = closed
//   transfer_node.translation[1] = station.pose().transfer_m;  // 0 = down
//   pusher_node.translation[2]   = -station.pose().pusher_m;   // 0 = home
//
// Call step(dt, inputs) from the fixed update with the five photo-eye bits and
// the side-lane request; interlocks, dead reckoning and dwell timers are here.
//
// Behaviour:
//   idle    gate open, pusher home, chain down. Releases are implicit: the
//           blade only closes when the throat is busy or a side item has the
//           merge reserved.
//   hold    blade closed while an item waits at the gate and it is not safe to
//           feed it (throat occupied, downstream not ready, or the merge is
//           about to run). Leaves as soon as the lane is clear.
//   merge   blade closed and the chain raised until the side item is through,
//           then a short clear dwell so a trailing item cannot ride down with
//           the deck.
//   reject  entered from any state when a flagged item trips the diverter
//           eye, so a rejected item is diverted even while the gate is
//           holding the line. The plate waits diverter_lead_s for the item to
//           reach it, stays out for reject_dwell_s, then retracts; the gate is
//           closed throughout.
//   fault   a side item waited longer than watchdog_s; chain stays down and
//           the gate reopens. Clears when the side lane empties.
//
// The transfer must never rise under a main-line item, and the merge throat
// beam sits only 0.25 m before the chain strip, far too late to react on its
// own. The merge entry beam (0.9 m into the merge module) re-anchors an item's
// position on the way in; the short stretches between beams are covered by
// dead-reckoned timers. Their defaults assume a 0.30 m/s bed and the 2 m module
// layout in the asset set; see MergeStationConfig.

#pragma once

#include <algorithm>
#include <cmath>

namespace factory {

struct MergeStationConfig {
    // Joint ranges in metres -- copies of assets/rigs/*.json limits_m.
    float gate_open_m = -0.29f;
    float gate_closed_m = 0.00f;
    float pusher_stroke_m = 0.30f;
    float transfer_up_m = 0.10f;

    // Actuator speeds, metres of joint travel per second.
    float gate_speed_mps = 0.58f;      // full stroke in ~0.50 s
    float pusher_speed_mps = 0.60f;    // full stroke in ~0.50 s
    float transfer_speed_mps = 0.25f;  // full stroke in ~0.40 s

    // Dead reckoning for the stretches with no photo-eye, at 0.30 m/s.
    float blind_window_s = 2.30f;  // gate exit 0.83 m -> diverter eye 1.50 m
    // Diverter eye exit 1.56 m -> merge-entry beam 3.94 m, 2.38 m at 0.30 m/s.
    float diverter_to_entry_s = 8.00f;
    // Merge-entry beam exit 4.03 m -> far end of the chain deck 4.91 m, 0.88 m
    // at 0.30 m/s. Sized to the far end, not the near one: an item that has
    // just cleared the beam still has its whole body to bring past the deck.
    float entry_to_strip_s = 3.00f;
    // Throat beam 4.34 m -> far end of the deck 4.91 m, 0.57 m at 0.30 m/s: the
    // beam cannot see the last half metre of the deck. 2.05 s leaves a few
    // centimetres of margin on the tail rather than a knife edge.
    float strip_clear_s = 2.05f;

    float diverter_lead_s = 1.15f;     // eye -> plate travel time at bed speed
    float reject_dwell_s = 1.00f;      // plate held out before retracting
    float side_clear_dwell_s = 0.30f;  // throat must stay clear this long
    float watchdog_s = 20.0f;          // side item starved -> fault
};

// One instance per placed station. Inputs are the only state it reads.
class MergeStation {
public:
    struct Inputs {
        bool gate_entry = false;    // conveyor_gate upstream eye  (0.19 m)
        bool gate_exit = false;     // conveyor_gate downstream eye (0.78 m)
        bool diverter_eye = false;  // conveyor_diverter eye        (1.47 m)
        bool merge_entry = false;   // conveyor_merge entry beam    (3.94 m)
        bool throat = false;        // conveyor_merge throat beam   (4.25 m),
                                    //   or the transfer's chain-occupied signal
        bool side_waiting = false;  // side item queued or inside the transfer
        bool reject_item = false;   // scanner verdict for the item at diverter_eye
        bool downstream_ready = true;  // merge `out` port can accept
    };

    struct Pose {
        float gate_m = 0.00f;      // 0 = closed, -0.29 = open
        float pusher_m = 0.00f;    // 0 = home, 0.30 = full stroke
        float transfer_m = 0.00f;  // 0 = chain down, 0.10 = raised
    };

    enum class State { idle, hold, merge, reject, fault };

    MergeStation() = default;
    explicit MergeStation(const MergeStationConfig& cfg) : cfg_(cfg) { reset(); }

    // Drop back to a safe start: blade closed, plate home, chain down.
    void reset() {
        state_ = State::idle;
        state_t_ = 0.0f;
        clear_t_ = 0.0f;
        gate_ = cfg_.gate_closed_m;
        pusher_ = 0.0f;
        transfer_ = 0.0f;
        blind_timer_ = 0.0f;
        diverter_timer_ = 0.0f;
        entry_timer_ = 0.0f;
        strip_timer_ = 0.0f;
        prev_exit_ = false;
        prev_eye_ = false;
        prev_entry_ = false;
        prev_throat_ = false;
        reject_latch_ = false;
    }

    void step(float dt, const Inputs& in) {
        if (!(dt > 0.0f)) return;

        update_edges(dt, in);
        const bool lane_clear = lane_is_clear(in);
        maybe_reject(in);

        // --- transitions --------------------------------------------------
        switch (state_) {
        case State::idle:
            if (in.side_waiting) {
                if (lane_clear && in.downstream_ready) enter(State::merge);
                else enter(State::hold);
            } else if (in.gate_entry && !in.downstream_ready) {
                enter(State::hold);
            }
            break;

        case State::hold:
            if (lane_clear && in.downstream_ready)
                enter(in.side_waiting ? State::merge : State::idle);
            break;

        case State::reject:
            if (state_t_ >= cfg_.diverter_lead_s + cfg_.reject_dwell_s && pusher_ <= 1e-4f) {
                reject_latch_ = false;
                enter(State::idle);
            }
            break;

        case State::merge:
            if (!in.side_waiting && !in.throat) {
                clear_t_ += dt;
                if (clear_t_ >= cfg_.side_clear_dwell_s) enter(State::idle);
            } else {
                clear_t_ = 0.0f;
            }
            if (state_t_ > cfg_.watchdog_s) enter(State::fault);
            break;

        case State::fault:
            if (!in.side_waiting && !in.throat) {
                clear_t_ += dt;
                if (clear_t_ >= 1.0f) enter(State::idle);
            } else {
                clear_t_ = 0.0f;
            }
            break;
        }

        drive_actuators(dt);
        state_t_ += dt;
    }

    Pose pose() const { return Pose{gate_, pusher_, transfer_}; }
    State state() const { return state_; }
    bool busy() const { return state_ != State::idle; }
    bool faulted() const { return state_ == State::fault; }
    const MergeStationConfig& config() const { return cfg_; }

private:
    // Falling edges start the clearance timers that keep the station from
    // believing a lane is empty the instant a beam clears.
    void update_edges(float dt, const Inputs& in) {
        if (!in.gate_exit && prev_exit_) blind_timer_ = cfg_.blind_window_s;
        if (!in.diverter_eye && prev_eye_) diverter_timer_ = cfg_.diverter_to_entry_s;
        if (!in.merge_entry && prev_entry_) entry_timer_ = cfg_.entry_to_strip_s;
        if (!in.throat && prev_throat_) strip_timer_ = cfg_.strip_clear_s;
        if (in.diverter_eye && !prev_eye_) reject_latch_ = in.reject_item;
        prev_exit_ = in.gate_exit;
        prev_eye_ = in.diverter_eye;
        prev_entry_ = in.merge_entry;
        prev_throat_ = in.throat;

        blind_timer_ = std::max(0.0f, blind_timer_ - dt);
        diverter_timer_ = std::max(0.0f, diverter_timer_ - dt);
        entry_timer_ = std::max(0.0f, entry_timer_ - dt);
        strip_timer_ = std::max(0.0f, strip_timer_ - dt);
    }

    // Every beam clear and every clearance timer expired.
    bool lane_is_clear(const Inputs& in) const {
        return !in.gate_exit && !in.diverter_eye && !in.merge_entry && !in.throat &&
               blind_timer_ <= 0.0f && diverter_timer_ <= 0.0f &&
               entry_timer_ <= 0.0f && strip_timer_ <= 0.0f;
    }

    // A flagged item at the diverter plate is a routing decision, not a
    // sequencing one: divert it whatever the rest of the station is doing.
    void maybe_reject(const Inputs& in) {
        if (state_ != State::reject && state_ != State::fault && in.diverter_eye &&
            reject_latch_) {
            enter(State::reject);
        }
    }

    void update_state(float dt, const Inputs& in, bool lane_clear) {
        switch (state_) {
        case State::idle:
            if (in.side_waiting) {
                if (lane_clear && in.downstream_ready) {
                    enter(State::merge);
                } else {
                    enter(State::hold);
                }
            } else if (in.gate_entry && !in.downstream_ready) {
                enter(State::hold);
            }
            break;

        case State::hold:
            if (lane_clear && in.downstream_ready)
                enter(in.side_waiting ? State::merge : State::idle);
            break;

        case State::reject:
            if (state_t_ >= cfg_.diverter_lead_s + cfg_.reject_dwell_s && pusher_ <= 1e-4f) {
                reject_latch_ = false;
                enter(State::idle);
            }
            break;

        case State::merge:
            if (!in.side_waiting && !in.throat) {
                clear_t_ += dt;
                if (clear_t_ >= cfg_.side_clear_dwell_s) enter(State::idle);
            } else {
                clear_t_ = 0.0f;
            }
            if (state_t_ > cfg_.watchdog_s) enter(State::fault);
            break;

        case State::fault:
            if (!in.side_waiting && !in.throat) {
                clear_t_ += dt;
                if (clear_t_ >= 1.0f) enter(State::idle);
            } else {
                clear_t_ = 0.0f;
            }
            break;
        }
    }

    void drive_actuators(float dt) {
        float gate_target = cfg_.gate_open_m;
        float pusher_target = 0.0f;
        float transfer_target = 0.0f;

        switch (state_) {
        case State::idle:
            break;
        case State::hold:
            gate_target = cfg_.gate_closed_m;
            break;
        case State::merge:
            gate_target = cfg_.gate_closed_m;
            transfer_target = cfg_.transfer_up_m;
            break;
        case State::reject:
            gate_target = cfg_.gate_closed_m;
            // strike only once the item has travelled from the eye to the plate
            pusher_target = (state_t_ >= cfg_.diverter_lead_s &&
                             state_t_ < cfg_.diverter_lead_s + cfg_.reject_dwell_s)
                                ? cfg_.pusher_stroke_m
                                : 0.0f;
            break;
        case State::fault:
            break;
        }

        gate_ = approach(gate_, gate_target, cfg_.gate_speed_mps, dt);
        pusher_ = approach(pusher_, pusher_target, cfg_.pusher_speed_mps, dt);
        transfer_ = approach(transfer_, transfer_target, cfg_.transfer_speed_mps, dt);
    }

    static float approach(float v, float target, float rate, float dt) {
        const float step = rate * dt;
        if (v < target) return std::min(v + step, target);
        if (v > target) return std::max(v - step, target);
        return v;
    }

    void enter(State s) {
        if (s == state_) return;
        state_ = s;
        state_t_ = 0.0f;
        clear_t_ = 0.0f;
    }

    MergeStationConfig cfg_{};
    State state_ = State::idle;
    float state_t_ = 0.0f;
    float clear_t_ = 0.0f;
    float gate_ = 0.0f;
    float pusher_ = 0.0f;
    float transfer_ = 0.0f;
    float blind_timer_ = 0.0f;
    float diverter_timer_ = 0.0f;
    float entry_timer_ = 0.0f;
    float strip_timer_ = 0.0f;
    bool prev_exit_ = false;
    bool prev_eye_ = false;
    bool prev_entry_ = false;
    bool prev_throat_ = false;
    bool reject_latch_ = false;
};

inline const char* merge_state_name(MergeStation::State s) {
    switch (s) {
    case MergeStation::State::idle: return "idle";
    case MergeStation::State::hold: return "hold";
    case MergeStation::State::merge: return "merge";
    case MergeStation::State::reject: return "reject";
    case MergeStation::State::fault: return "fault";
    }
    return "?";
}

inline const char* merge_station_name(const MergeStation& s) {
    return merge_state_name(s.state());
}

}  // namespace factory
