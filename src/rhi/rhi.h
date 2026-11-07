// Public API of the RHI module (MOD-06). Backend selection happens here and
// nowhere else: call sites ask for a device and get whatever this machine can
// actually run.
#pragma once

#include <memory>

#include "rhi/device.h"
#include "rhi/swap_chain.h"

namespace fct::rhi {

// Never returns null and never fails. A machine without a GPU is a supported
// configuration (CI, containers), so an unavailable backend degrades to the
// headless one and says so in the log instead of returning an error the caller
// cannot act on.
std::unique_ptr<Device> create_device(const DeviceDesc& desc);

}  // namespace fct::rhi
