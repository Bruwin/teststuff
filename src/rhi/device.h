// The device contract: what a backend must provide to the rest of the engine.
// Backends live beside it (null_device.h now, gl/ at M2b) and are reached only
// through rhi/rhi.h, so no call site names one.
#pragma once

#include <cstdint>
#include <memory>

#include "rhi/swap_chain.h"

namespace fct::rhi {

enum class Backend : std::uint8_t {
    kNull = 0,  // no GPU work; deterministic bookkeeping only
    kGl,        // OpenGL 4.6 core
};

struct DeviceDesc {
    const char* app_name = "factory";
    // Preference, not a requirement: a machine without GL still gets a device.
    Backend prefer = Backend::kGl;
};

struct DeviceInfo {
    const char* name = "unknown";
    Backend backend = Backend::kNull;
    bool is_headless = true;
};

class Device {
public:
    Device() = default;
    virtual ~Device() = default;
    Device(const Device&) = delete;
    Device& operator=(const Device&) = delete;
    Device(Device&&) = delete;
    Device& operator=(Device&&) = delete;

    virtual DeviceInfo info() const = 0;

    // Null only when desc fails validation. A backend that cannot present still
    // returns a chain, so the loop has one shape everywhere.
    virtual std::unique_ptr<SwapChain> try_create_swap_chain(const SwapChainDesc& desc) = 0;

    // Blocks until submitted work has finished. Also the teardown hook: a chain
    // must not be destroyed while the GPU may still be reading it.
    virtual void wait_idle() = 0;
};

}  // namespace fct::rhi
