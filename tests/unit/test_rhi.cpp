#include "core/log.h"
#include "harness.h"
#include "rhi/rhi.h"
#include "rhi/swap_chain_state.h"

namespace {

void discard(fct::LogLevel, const char*, int, const char*) {}

void silence() { fct::log_set_sink(&discard); }

fct::rhi::SwapChainDesc desc_for(int width_px, int height_px) {
    fct::rhi::SwapChainDesc desc;
    desc.width_px = width_px;
    desc.height_px = height_px;
    return desc;
}

}  // namespace

TEST_CASE(rhi_device_is_created_and_reports_a_headless_backend) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    CHECK(device != nullptr);
    CHECK_EQ(device->info().backend, fct::rhi::Backend::kNull);
    CHECK(device->info().is_headless);
}

TEST_CASE(rhi_swap_chain_rejects_degenerate_sizes) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    CHECK(device->try_create_swap_chain(desc_for(0, 480)) == nullptr);
    CHECK(device->try_create_swap_chain(desc_for(640, 0)) == nullptr);
    CHECK(device->try_create_swap_chain(desc_for(-16, 16)) == nullptr);
    CHECK(device->try_create_swap_chain(desc_for(fct::rhi::kMaxSwapChainPx + 1, 16)) == nullptr);
}

TEST_CASE(rhi_swap_chain_accepts_the_size_range_it_documents) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    const std::unique_ptr<fct::rhi::SwapChain> chain =
        device->try_create_swap_chain(desc_for(1, fct::rhi::kMaxSwapChainPx));
    CHECK(chain != nullptr);
    CHECK_EQ(chain->width_px(), 1);
    CHECK_EQ(chain->height_px(), fct::rhi::kMaxSwapChainPx);
    CHECK_EQ(chain->format(), fct::rhi::Format::kBgra8Unorm);
}

TEST_CASE(rhi_clear_and_present_are_counted) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    const std::unique_ptr<fct::rhi::SwapChain> chain =
        device->try_create_swap_chain(desc_for(640, 480));
    CHECK(chain != nullptr);

    fct::rhi::ClearColor color;
    color.b = 0.25f;
    for (int frame = 0; frame < 7; ++frame) {
        chain->clear(color);
        CHECK(chain->try_present());
    }

    CHECK_EQ(chain->clears_issued(), std::uint64_t{7});
    CHECK_EQ(chain->frames_presented(), std::uint64_t{7});
}

TEST_CASE(rhi_resize_rejects_out_of_range_and_keeps_the_size) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    const std::unique_ptr<fct::rhi::SwapChain> chain =
        device->try_create_swap_chain(desc_for(800, 600));
    CHECK(chain != nullptr);

    CHECK(!chain->try_resize(0, 600));
    CHECK(!chain->try_resize(800, -1));
    CHECK(!chain->try_resize(fct::rhi::kMaxSwapChainPx + 1, 600));
    CHECK_EQ(chain->width_px(), 800);
    CHECK_EQ(chain->height_px(), 600);

    CHECK(chain->try_resize(1024, 768));
    CHECK_EQ(chain->width_px(), 1024);
    CHECK_EQ(chain->height_px(), 768);
}

TEST_CASE(rhi_frame_digest_is_deterministic_and_colour_sensitive) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});

    const std::unique_ptr<fct::rhi::SwapChain> first =
        device->try_create_swap_chain(desc_for(320, 240));
    const std::unique_ptr<fct::rhi::SwapChain> second =
        device->try_create_swap_chain(desc_for(320, 240));
    CHECK(first != nullptr);
    CHECK(second != nullptr);

    fct::rhi::ClearColor base;
    base.r = 0.1f;
    base.g = 0.2f;
    base.b = 0.3f;
    for (int frame = 0; frame < 4; ++frame) {
        first->clear(base);
        first->try_present();
        second->clear(base);
        second->try_present();
    }
    CHECK_EQ(first->frame_digest(), second->frame_digest());

    fct::rhi::ClearColor other = base;
    other.b = 0.31f;
    second->clear(other);
    second->try_present();
    CHECK(first->frame_digest() != second->frame_digest());
}

TEST_CASE(rhi_lost_surface_stops_presenting_without_counting) {
    fct::rhi::SwapChainDesc desc = desc_for(64, 64);
    fct::rhi::SwapChainState state(desc);

    CHECK(state.try_present());
    CHECK_EQ(state.frames_presented(), std::uint64_t{1});

    state.mark_lost();
    CHECK(!state.try_present());
    CHECK(!state.try_present());
    CHECK_EQ(state.frames_presented(), std::uint64_t{1});
    CHECK(state.is_lost());
}

TEST_CASE(rhi_swap_chain_digest_changes_when_the_surface_is_resized) {
    fct::rhi::SwapChainState state(desc_for(64, 64));
    const std::uint64_t before = state.frame_digest();
    CHECK(state.try_resize(128, 96));
    CHECK(state.frame_digest() != before);
    CHECK(!state.try_resize(0, 96));
    CHECK_EQ(state.frame_digest() != before, true);
}
