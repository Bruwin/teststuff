#include <cstdint>
#include <memory>

#include "core/log.h"
#include "harness.h"
#include "render/render.h"
#include "rhi/rhi.h"

namespace {

constexpr std::uint32_t kBlack = fct::rhi::pack_rgba(0, 0, 0, 255);
constexpr std::uint32_t kWhite = fct::rhi::pack_rgba(255, 255, 255, 255);
constexpr std::uint32_t kAmber = fct::rhi::pack_rgba(255, 176, 59, 255);

void discard(fct::LogLevel, const char*, int, const char*) {}

void silence() { fct::log_set_sink(&discard); }

fct::rhi::ClearColor black_clear() {
    fct::rhi::ClearColor color;
    color.a = 1.0f;
    return color;
}

fct::rhi::Vertex at(float x, float y, std::uint32_t rgba) {
    return fct::rhi::Vertex{x, y, 0.0f, 1.0f, rgba};
}

fct::render::Framebuffer make_target(int width_px, int height_px) {
    fct::render::Framebuffer target;
    target.try_resize(width_px, height_px);
    target.clear(black_clear());
    return target;
}

}  // namespace

TEST_CASE(render_triangle_fills_the_centre_and_spares_the_corner) {
    fct::render::Framebuffer target = make_target(8, 8);
    fct::rhi::CommandBuffer commands;
    CHECK(commands.try_push_triangle(at(-1.0f, -1.0f, kAmber), at(1.0f, -1.0f, kAmber),
                                     at(0.0f, 1.0f, kAmber)));

    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);

    CHECK_EQ(target.pixel_rgba(4, 4), kAmber);
    CHECK_EQ(target.pixel_rgba(0, 0), kBlack);
    CHECK(target.covered_pixels() > 0);
    CHECK(target.covered_pixels() < 8 * 8);
}

TEST_CASE(render_triangle_outside_the_viewport_draws_nothing) {
    fct::render::Framebuffer target = make_target(8, 8);
    fct::rhi::CommandBuffer commands;
    CHECK(commands.try_push_triangle(at(2.0f, 2.0f, kAmber), at(3.0f, 2.0f, kAmber),
                                     at(2.5f, 3.0f, kAmber)));

    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);

    CHECK_EQ(target.covered_pixels(), 0);
}

TEST_CASE(render_degenerate_triangle_draws_nothing) {
    fct::render::Framebuffer target = make_target(8, 8);
    fct::rhi::CommandBuffer commands;
    CHECK(commands.try_push_triangle(at(0.0f, 0.0f, kAmber), at(0.0f, 0.0f, kAmber),
                                     at(0.0f, 0.0f, kAmber)));

    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);

    CHECK_EQ(target.covered_pixels(), 0);
}

TEST_CASE(render_triangle_behind_the_eye_is_rejected) {
    fct::render::Framebuffer target = make_target(8, 8);
    fct::rhi::CommandBuffer commands;
    const fct::rhi::Vertex behind{-1.0f, -1.0f, 0.0f, 0.0f, kAmber};
    CHECK(commands.try_push_triangle(behind, at(1.0f, -1.0f, kAmber), at(0.0f, 1.0f, kAmber)));

    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);

    CHECK_EQ(target.covered_pixels(), 0);
}

TEST_CASE(render_line_paints_both_ends_of_the_middle_row) {
    fct::render::Framebuffer target = make_target(8, 8);
    fct::rhi::CommandBuffer commands;
    CHECK(commands.try_push_line(at(-1.0f, 0.0f, kWhite), at(1.0f, 0.0f, kWhite)));

    const fct::render::Rasterizer rasterizer;
    rasterizer.draw(commands, target);

    CHECK_EQ(target.pixel_rgba(0, 4), kWhite);
    CHECK_EQ(target.pixel_rgba(4, 4), kWhite);
    CHECK_EQ(target.pixel_rgba(7, 4), kWhite);
    CHECK_EQ(target.pixel_rgba(7, 0), kBlack);
}

TEST_CASE(render_command_digest_tracks_geometry_and_colour) {
    fct::rhi::CommandBuffer first;
    fct::rhi::CommandBuffer identical;
    fct::rhi::CommandBuffer recoloured;

    CHECK(first.try_push_triangle(at(-1.0f, -1.0f, kAmber), at(1.0f, -1.0f, kAmber),
                                  at(0.0f, 1.0f, kAmber)));
    CHECK(identical.try_push_triangle(at(-1.0f, -1.0f, kAmber), at(1.0f, -1.0f, kAmber),
                                      at(0.0f, 1.0f, kAmber)));
    CHECK(recoloured.try_push_triangle(at(-1.0f, -1.0f, kWhite), at(1.0f, -1.0f, kAmber),
                                       at(0.0f, 1.0f, kAmber)));

    CHECK_EQ(first.digest(), identical.digest());
    CHECK(first.digest() != recoloured.digest());

    first.reset();
    CHECK(first.is_empty());
    CHECK(first.digest() != identical.digest());
}

TEST_CASE(render_commands_reach_the_device_and_are_counted) {
    silence();
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    const std::unique_ptr<fct::rhi::SwapChain> chain = device->try_create_swap_chain({});
    CHECK(chain != nullptr);

    fct::rhi::CommandBuffer commands;
    CHECK(commands.try_push_triangle(at(-1.0f, -1.0f, kAmber), at(1.0f, -1.0f, kAmber),
                                     at(0.0f, 1.0f, kAmber)));
    CHECK(commands.try_push_line(at(-1.0f, 1.0f, kWhite), at(1.0f, 1.0f, kWhite)));
    CHECK(commands.try_push_line(at(-1.0f, -1.0f, kWhite), at(-1.0f, 1.0f, kWhite)));

    CHECK(chain->try_submit(commands));
    CHECK_EQ(chain->submitted_buffers(), std::uint64_t{1});
    CHECK_EQ(chain->vertices_submitted(), std::uint64_t{7});
}

TEST_CASE(render_framebuffer_rejects_invalid_sizes_and_keeps_its_state) {
    fct::render::Framebuffer target;
    CHECK(!target.try_resize(0, 4));
    CHECK(!target.try_resize(-3, 4));
    CHECK(!target.try_resize(4, fct::render::kMaxFramebufferPx + 1));
    CHECK_EQ(target.width_px(), 1);
    CHECK_EQ(target.height_px(), 1);

    CHECK(target.try_resize(16, 9));
    CHECK_EQ(target.width_px(), 16);
    CHECK_EQ(target.height_px(), 9);
    CHECK(!target.contains(16, 0));
}

TEST_CASE(render_cleared_target_reports_no_coverage) {
    fct::render::Framebuffer target = make_target(16, 16);
    CHECK_EQ(target.covered_pixels(), 0);

    const std::uint64_t before = target.digest();
    const fct::render::Rasterizer rasterizer;
    const fct::rhi::CommandBuffer empty;
    rasterizer.draw(empty, target);

    CHECK_EQ(target.digest(), before);
    CHECK_EQ(target.pixel_rgba(-1, 0), 0u);
}
