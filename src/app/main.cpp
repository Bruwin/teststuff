// Entry point. Three modes, all sharing the same fixed-step clock:
//
//   --ticks N     run N sim ticks as fast as possible (determinism harness)
//   --frames N    run N synthetic frames of --frame-ns each (loop harness, no OS
//                 timing, so it is reproducible in tests and on CI)
//   --window      real loop paced by the platform clock (needs a real window)
//
// The first two must stay working on a machine with no display and no SDL3:
// verify.sh and CI depend on it.
#include <cstdlib>
#include <cstring>
#include <memory>

#include "core/fixed_step.h"
#include "core/log.h"
#include "core/version.h"
#include "platform/platform.h"
#include "render/render.h"
#include "rhi/rhi.h"
#include "sim/world.h"

namespace {

constexpr std::int32_t kMaxTicksPerFrame = 4;

struct Options {
    int ticks = 30;
    int frames = 0;
    std::int64_t frame_ns = 16'666'667;  // 60 Hz
    bool window = false;
};

std::int64_t parse_i64(const char* text, std::int64_t fallback) {
    const long long value = std::atoll(text);
    return value > 0 ? static_cast<std::int64_t>(value) : fallback;
}

Options parse_options(int argc, char** argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const char* arg = argv[i];
        const bool has_value = i + 1 < argc;
        if (std::strcmp(arg, "--ticks") == 0 && has_value) {
            options.ticks = static_cast<int>(parse_i64(argv[++i], options.ticks));
        } else if (std::strcmp(arg, "--frames") == 0 && has_value) {
            options.frames = static_cast<int>(parse_i64(argv[++i], options.frames));
        } else if (std::strcmp(arg, "--frame-ns") == 0 && has_value) {
            options.frame_ns = parse_i64(argv[++i], options.frame_ns);
        } else if (std::strcmp(arg, "--window") == 0) {
            options.window = true;
        }
    }
    return options;
}

std::uint32_t world_seed() { return 0xC0FFEEu; }

// A frame's clear colour, derived from its index: cheap, deterministic, and it
// makes a stalled present visible instead of a static picture.
fct::rhi::ClearColor clear_for_frame(int frame) {
    fct::rhi::ClearColor color;
    color.r = 0.04f;
    color.g = 0.05f;
    color.b = 0.07f + static_cast<float>(frame % 64) / 512.0f;
    return color;
}

int run_ticks(int ticks) {
    fct::sim::World world(world_seed());
    for (int i = 0; i < ticks; ++i) {
        world.tick();
    }
    FCT_LOG_INFO("ticks=%llu hash=%016llx", static_cast<unsigned long long>(world.tick_count()),
                 static_cast<unsigned long long>(world.hash()));
    return 0;
}

// The M3 scene: one triangle inside a debug box, in clip space. It is submitted
// through the RHI every frame and drawn by the reference rasteriser, so this is
// the geometry the GL backend will replay once it exists.
fct::rhi::CommandBuffer build_scene_commands() {
    const std::uint32_t fill = fct::rhi::pack_rgba(255, 176, 59, 255);
    const std::uint32_t outline = fct::rhi::pack_rgba(235, 238, 245, 255);

    const fct::rhi::Vertex a{-0.60f, -0.55f, 0.0f, 1.0f, fill};
    const fct::rhi::Vertex b{0.60f, -0.55f, 0.0f, 1.0f, fill};
    const fct::rhi::Vertex c{0.00f, 0.62f, 0.0f, 1.0f, fill};
    const fct::rhi::Vertex box_tl{-0.75f, 0.75f, 0.0f, 1.0f, outline};
    const fct::rhi::Vertex box_tr{0.75f, 0.75f, 0.0f, 1.0f, outline};
    const fct::rhi::Vertex box_br{0.75f, -0.75f, 0.0f, 1.0f, outline};
    const fct::rhi::Vertex box_bl{-0.75f, -0.75f, 0.0f, 1.0f, outline};

    fct::rhi::CommandBuffer commands;
    FCT_ASSERT(commands.try_push_triangle(a, b, c));
    FCT_ASSERT(commands.try_push_line(box_tl, box_tr));
    FCT_ASSERT(commands.try_push_line(box_tr, box_br));
    FCT_ASSERT(commands.try_push_line(box_br, box_bl));
    FCT_ASSERT(commands.try_push_line(box_bl, box_tl));
    return commands;
}

// One frame through the RHI: match the window size, clear, submit, present. Kept
// out of the loop so the loop reads as a loop.
void draw_frame(fct::rhi::SwapChain* chain, const fct::rhi::CommandBuffer& commands, int frame,
                int width_px, int height_px) {
    if (chain == nullptr) {
        return;
    }
    if (chain->try_resize(width_px, height_px)) {
        FCT_LOG_DEBUG("swap chain resized to %dx%d", width_px, height_px);
    }
    chain->clear(clear_for_frame(frame));
    chain->try_submit(commands);
    chain->try_present();
}

struct PreviewShot {
    int covered_px = 0;
    std::uint64_t digest = 0;
};

// What the frame would look like, drawn in software: the only way to say more
// than "the calls were made" on a machine with no GPU.
PreviewShot rasterize_preview(const fct::rhi::CommandBuffer& commands, int last_frame) {
    PreviewShot shot;
    fct::render::Framebuffer target;
    if (!target.try_resize(320, 180)) {
        return shot;
    }
    target.clear(clear_for_frame(last_frame));
    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);
    shot.covered_px = target.covered_pixels();
    shot.digest = target.digest();
    return shot;
}

// Synthetic frame loop: no clock reads, no sleeps, fully reproducible. Each frame
// is submitted through the RHI exactly as the window loop does, so this mode
// exercises the same clear and present path on a machine with no GPU.
int run_frames(const Options& options) {
    fct::sim::World world(world_seed());
    fct::FixedStepClock clock(fct::kSimStepNs, kMaxTicksPerFrame);

    fct::rhi::DeviceDesc device_desc;
    device_desc.prefer = fct::rhi::Backend::kNull;  // no surface to draw on here
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device(device_desc);
    const std::unique_ptr<fct::rhi::SwapChain> swap_chain =
        device->try_create_swap_chain(fct::rhi::SwapChainDesc{});
    if (swap_chain == nullptr) {
        FCT_LOG_ERROR("could not create a swap chain");
        return 1;
    }    const fct::rhi::CommandBuffer commands = build_scene_commands();

    std::int64_t now_ns = 0;
    for (int frame = 0; frame < options.frames; ++frame) {
        now_ns += options.frame_ns;
        const int steps = clock.advance(now_ns);
        for (int step = 0; step < steps; ++step) {
            world.tick();
        }
        swap_chain->clear(clear_for_frame(frame));
        if (!swap_chain->try_submit(commands)) {
            FCT_LOG_WARN("frame %d was rejected by the swap chain", frame);
        }
        swap_chain->try_present();
    }

    const PreviewShot shot = rasterize_preview(commands, options.frames - 1);
    FCT_LOG_INFO(
        "frames=%d ticks=%llu dropped=%llu alpha=%.3f hash=%016llx presents=%llu digest=%016llx "
        "covered=%d frame=%016llx",
        options.frames, static_cast<unsigned long long>(clock.tick_count()),
        static_cast<unsigned long long>(clock.dropped_ticks()),
        static_cast<double>(clock.alpha()),
        static_cast<unsigned long long>(world.hash()),
        static_cast<unsigned long long>(swap_chain->frames_presented()),
        static_cast<unsigned long long>(swap_chain->frame_digest()), shot.covered_px,
        static_cast<unsigned long long>(shot.digest));
    return 0;
}

int run_window() {
    fct::platform::Window window;
    fct::platform::WindowDesc desc;
    desc.title = "factory engine";
    if (!window.open(desc)) {
        FCT_LOG_ERROR("could not open a window");
        return 1;
    }
    if (window.is_headless()) {
        FCT_LOG_WARN("no SDL3 in this build: running 600 synthetic frames instead");
        Options fallback;
        fallback.frames = 600;
        return run_frames(fallback);
    }

    fct::sim::World world(world_seed());
    fct::FixedStepClock clock(fct::kSimStepNs, kMaxTicksPerFrame);
    fct::platform::InputSnapshot input{};

    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    fct::rhi::SwapChainDesc chain_desc;
    chain_desc.width_px = window.width();
    chain_desc.height_px = window.height();
    const std::unique_ptr<fct::rhi::SwapChain> swap_chain =
        device->try_create_swap_chain(chain_desc);
    const fct::rhi::CommandBuffer commands = build_scene_commands();

    int frame = 0;
    while (window.is_open() && !input.quit) {
        window.poll(input);
        if (fct::platform::is_pressed(input, fct::platform::Key::kEscape)) {
            break;
        }

        const int steps = clock.advance(fct::platform::monotonic_ns());
        for (int step = 0; step < steps; ++step) {
            world.tick();
        }

        draw_frame(swap_chain.get(), commands, frame, window.width(), window.height());
        window.present();
        ++frame;
        // One clear and one triangle per frame: yield rather than spin at 100 %.
        fct::platform::sleep_for_ns(1'000'000);
    }

    device->wait_idle();
    FCT_LOG_INFO("window closed after %llu ticks, %llu frames presented",
                 static_cast<unsigned long long>(clock.tick_count()),
                 static_cast<unsigned long long>(swap_chain == nullptr
                                                     ? 0
                                                     : swap_chain->frames_presented()));
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    fct::log_set_level(fct::LogLevel::kInfo);
    const Options options = parse_options(argc, argv);

    FCT_LOG_INFO("factory engine %s", fct::build_summary());
    FCT_LOG_INFO("tick order v%u, %d hz", fct::sim::kTickOrderVersion,
                 static_cast<int>(fct::sim::kTicksPerSecond));

    if (options.window) {
        return run_window();
    }
    if (options.frames > 0) {
        return run_frames(options);
    }
    return run_ticks(options.ticks);
}
