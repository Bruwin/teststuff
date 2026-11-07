// Headless backend: no GL, no window, no driver. It exists so the render loop can
// run, be timed and be asserted on in environments that have no display -- CI,
// containers, this repository's own gate -- and so the loop code has exactly one
// shape instead of an #ifdef around every present.
#pragma once

#include <memory>

#include "rhi/device.h"

namespace fct::rhi {

class NullDevice final : public Device {
public:
    NullDevice() = default;

    DeviceInfo info() const override;
    std::unique_ptr<SwapChain> try_create_swap_chain(const SwapChainDesc& desc) override;
    void wait_idle() override;
};

}  // namespace fct::rhi
