#include "rhi/null_device.h"

#include <memory>

#include "core/log.h"
#include "rhi/swap_chain_state.h"

namespace fct::rhi {
namespace {

// The whole backend. It reuses SwapChainState, so its counters and digest are the
// same code the GL backend will run -- a test that passes here is testing the
// loop logic, not a mock of it.
class NullSwapChain final : public SwapChain {
public:
    explicit NullSwapChain(const SwapChainDesc& desc) : state_(desc) {}

    int width_px() const override { return state_.width_px(); }
    int height_px() const override { return state_.height_px(); }
    Format format() const override { return state_.format(); }

    bool try_resize(int width_px, int height_px) override {
        return state_.try_resize(width_px, height_px);
    }

    void clear(const ClearColor& color) override { state_.clear(color); }

    bool try_present() override { return state_.try_present(); }

    std::uint64_t frames_presented() const override { return state_.frames_presented(); }
    std::uint64_t clears_issued() const override { return state_.clears_issued(); }
    std::uint64_t frame_digest() const override { return state_.frame_digest(); }

private:
    SwapChainState state_;
};

}  // namespace

DeviceInfo NullDevice::info() const { return DeviceInfo{"null", Backend::kNull, true}; }

std::unique_ptr<SwapChain> NullDevice::try_create_swap_chain(const SwapChainDesc& desc) {
    if (!is_valid(desc)) {
        FCT_LOG_ERROR("rhi: rejecting swap chain '%s' at %dx%d", desc.debug_name, desc.width_px,
                      desc.height_px);
        return nullptr;
    }
    FCT_LOG_DEBUG("rhi: headless swap chain '%s' at %dx%d", desc.debug_name, desc.width_px,
                  desc.height_px);
    return std::make_unique<NullSwapChain>(desc);
}

void NullDevice::wait_idle() {}

}  // namespace fct::rhi
