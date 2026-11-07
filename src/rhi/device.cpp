#include "rhi/rhi.h"

#include <memory>

#include "core/log.h"
#include "rhi/null_device.h"

namespace fct::rhi {

std::unique_ptr<Device> create_device(const DeviceDesc& desc) {
    // M2 ships the contract and the headless backend; the GL backend (rhi/gl,
    // M2b) needs SDL3 plus a GL loader, neither of which exists in every build.
    // Requesting it is not an error -- the loop runs either way -- but the log
    // says what actually happened rather than implying a GPU was used.
    if (desc.prefer == Backend::kGl) {
        FCT_LOG_DEBUG("rhi: GL backend unavailable in this build, using headless");
    }
    std::unique_ptr<Device> device = std::make_unique<NullDevice>();
    const DeviceInfo info = device->info();
    FCT_LOG_INFO("rhi: %s device '%s' for '%s'", info.is_headless ? "headless" : "hardware",
                 info.name, desc.app_name);
    return device;
}

}  // namespace fct::rhi
