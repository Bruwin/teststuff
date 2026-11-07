// OpenGL 4.6 backend. It replays rhi::CommandBuffer exactly as the reference
// rasteriser does, through an injected entry point table -- which is why this
// compiles and is unit-tested on machines that have neither GL nor a driver.
#pragma once

#include <memory>

#include "rhi/device.h"
#include "rhi/gl/gl_api.h"

namespace fct::rhi::gl {

// The entry point table lives in fct::gl (it is the driver's namespace, not the
// RHI's); the alias keeps the backend readable.
using GlApi = fct::gl::GlApi;

class GlDevice final : public Device {
public:
    explicit GlDevice(const GlApi& api);

    // Null when the table is incomplete or the shaders do not build: a device that
    // cannot draw is worse than no device, because callers stop looking for one.
    static std::unique_ptr<GlDevice> try_create(const GlApi& api, const char* app_name);

    DeviceInfo info() const override;
    std::unique_ptr<SwapChain> try_create_swap_chain(const SwapChainDesc& desc) override;
    void wait_idle() override;

    unsigned program() const { return program_; }
    const GlApi& api() const { return api_; }

private:
    GlApi api_;
    unsigned program_ = 0;
    const char* app_name_ = "factory";
};

}  // namespace fct::rhi::gl
