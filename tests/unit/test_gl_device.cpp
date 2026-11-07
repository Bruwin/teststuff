#include <cstdint>
#include <cstring>
#include <memory>
#include <string>
#include <vector>

#include "core/log.h"
#include "harness.h"
#include "rhi/capture.h"
#include "rhi/gl/gl_device.h"
#include "rhi/gl/gl_loader.h"
#include "rhi/rhi.h"

namespace {

using fct::gl::GLenum;
using fct::gl::GLint;
using fct::gl::GLsizei;
using fct::gl::GLuint;

struct DrawRecord {
    GLenum mode = 0;
    int first = 0;
    int count = 0;
};

std::vector<DrawRecord> g_draws;
std::vector<std::string> g_requested;
int g_clears = 0;
int g_uploads = 0;

void reset_records() {
    g_draws.clear();
    g_requested.clear();
    g_clears = 0;
    g_uploads = 0;
}

fct::rhi::CommandBuffer two_primitives() {
    fct::rhi::CommandBuffer commands;
    const std::uint32_t red = fct::rhi::pack_rgba(255, 0, 0, 255);
    const fct::rhi::Vertex a{-1.0f, -1.0f, 0.0f, 1.0f, red};
    const fct::rhi::Vertex b{1.0f, -1.0f, 0.0f, 1.0f, red};
    const fct::rhi::Vertex c{0.0f, 1.0f, 0.0f, 1.0f, red};
    commands.try_push_triangle(a, b, c);
    commands.try_push_line(a, c);
    return commands;
}

// The table is filled in three stages so no single builder outgrows its size: one
// for object lifetime and state, one for drawing, one for readback.
void fill_lifetime(fct::gl::GlApi& api) {
    api.viewport = [](GLint, GLint, GLsizei, GLsizei) {};
    api.clear_color = [](float, float, float, float) {};
    api.clear = [](std::uint32_t) { ++g_clears; };
    api.enable = [](GLenum) {};
    api.disable = [](GLenum) {};
    api.line_width = [](float) {};
    api.gen_buffers = [](GLsizei, GLuint* out) {
        if (out != nullptr) {
            *out = 1;
        }
    };
    api.bind_buffer = [](GLenum, GLuint) {};
    api.buffer_data = [](GLenum, std::ptrdiff_t, const void*, GLenum) { ++g_uploads; };
    api.destroy_buffers = [](GLsizei, const GLuint*) {};
    api.gen_vertex_arrays = [](GLsizei, GLuint* out) {
        if (out != nullptr) {
            *out = 2;
        }
    };
    api.bind_vertex_array = [](GLuint) {};
    api.destroy_vertex_arrays = [](GLsizei, const GLuint*) {};
}

void fill_program(fct::gl::GlApi& api) {
    api.create_shader = [](GLenum) -> GLuint { return 3; };
    api.shader_source = [](GLuint, GLsizei, const char* const*, const GLint*) {};
    api.compile_shader = [](GLuint) {};
    api.get_shader_iv = [](GLuint, GLenum, GLint* value) {
        if (value != nullptr) {
            *value = 1;
        }
    };
    api.destroy_shader = [](GLuint) {};
    api.create_program = []() -> GLuint { return 4; };
    api.attach_shader = [](GLuint, GLuint) {};
    api.link_program = [](GLuint) {};
    api.get_program_iv = [](GLuint, GLenum, GLint* value) {
        if (value != nullptr) {
            *value = 1;
        }
    };
    api.use_program = [](GLuint) {};
}

void fill_draw_and_readback(fct::gl::GlApi& api) {
    api.vertex_attrib_pointer = [](GLuint, GLint, GLenum, std::uint8_t, GLsizei, const void*) {};
    api.enable_vertex_attrib_array = [](GLuint) {};
    api.draw_arrays = [](GLenum mode, GLint first, GLsizei count) {
        g_draws.push_back(DrawRecord{mode, static_cast<int>(first), static_cast<int>(count)});
    };
    api.read_pixels = [](GLint, GLint, GLsizei width, GLsizei height, GLenum, GLenum, void* out) {
        auto* bytes = static_cast<std::uint8_t*>(out);
        for (GLsizei row = 0; row < height; ++row) {
            for (GLsizei column = 0; column < width; ++column) {
                const std::size_t index =
                    ((static_cast<std::size_t>(row) * static_cast<std::size_t>(width)) +
                     static_cast<std::size_t>(column)) * 4u;
                // Red carries the GL row index, bottom row first.
                bytes[index] = static_cast<std::uint8_t>(row);
                bytes[index + 1] = 0;
                bytes[index + 2] = 0;
                bytes[index + 3] = 255;
            }
        }
    };
    api.get_string = [](GLenum) -> const std::uint8_t* {
        return reinterpret_cast<const std::uint8_t*>("fake-gl");
    };
    api.flush = []() {};
}

fct::gl::GlApi fake_api(bool complete) {
    fct::gl::GlApi api;
    if (!complete) {
        return api;
    }
    fill_lifetime(api);
    fill_program(api);
    fill_draw_and_readback(api);
    return api;
}

void* any_proc(void*, const char* name) {
    g_requested.emplace_back(name);
    static int token = 0;
    return &token;
}

}  // namespace

TEST_CASE(gl_incomplete_api_is_rejected) {
    reset_records();
    CHECK(fct::rhi::gl::GlDevice::try_create(fake_api(false), "test") == nullptr);
}

TEST_CASE(gl_device_reports_a_hardware_backend) {
    reset_records();
    const std::unique_ptr<fct::rhi::gl::GlDevice> device =
        fct::rhi::gl::GlDevice::try_create(fake_api(true), "test");
    CHECK(device != nullptr);
    CHECK_EQ(device->info().backend, fct::rhi::Backend::kGl);
    CHECK(!device->info().is_headless);
    CHECK(std::strcmp(device->info().name, "fake-gl") == 0);
}

TEST_CASE(gl_submit_uploads_once_and_draws_each_primitive) {
    reset_records();
    const std::unique_ptr<fct::rhi::gl::GlDevice> device =
        fct::rhi::gl::GlDevice::try_create(fake_api(true), "test");
    CHECK(device != nullptr);
    const std::unique_ptr<fct::rhi::SwapChain> chain = device->try_create_swap_chain({});
    CHECK(chain != nullptr);

    const fct::rhi::CommandBuffer commands = two_primitives();
    chain->clear({});
    CHECK(chain->try_submit(commands));
    CHECK(chain->try_present());

    CHECK_EQ(g_clears, 1);
    CHECK_EQ(g_uploads, 1);  // one buffer upload for the whole frame
    CHECK_EQ(g_draws.size(), std::size_t{2});
    CHECK_EQ(g_draws[0].mode, fct::gl::kTriangles);
    CHECK_EQ(g_draws[0].count, 3);
    CHECK_EQ(g_draws[1].mode, fct::gl::kLines);
    CHECK_EQ(g_draws[1].first, 3);
    CHECK_EQ(g_draws[1].count, 2);
    CHECK_EQ(chain->vertices_submitted(), std::uint64_t{5});
}

TEST_CASE(gl_capture_flips_the_bottom_up_readback) {
    reset_records();
    fct::rhi::SwapChainDesc desc;
    desc.width_px = 2;
    desc.height_px = 3;
    const std::unique_ptr<fct::rhi::gl::GlDevice> device =
        fct::rhi::gl::GlDevice::try_create(fake_api(true), "test");
    CHECK(device != nullptr);
    const std::unique_ptr<fct::rhi::SwapChain> chain = device->try_create_swap_chain(desc);
    CHECK(chain != nullptr);

    fct::rhi::CapturedFrame frame;
    CHECK(chain->try_capture(frame));
    CHECK(frame.is_valid());
    // GL row 0 is the bottom; row 0 of the captured frame must be the top.
    CHECK_EQ(frame.pixels[0], fct::rhi::pack_rgba(2, 0, 0, 255));
    CHECK_EQ(frame.pixels[4], fct::rhi::pack_rgba(0, 0, 0, 255));
}

TEST_CASE(gl_loader_asks_for_every_entry_point_it_needs) {
    g_requested.clear();
    fct::rhi::gl::GlApi api;
    const fct::rhi::gl::GlProcLoader loader{&any_proc, nullptr};
    CHECK(fct::rhi::gl::try_load_api(loader, api));

    bool asked_for_draw = false;
    bool asked_for_readback = false;
    for (const std::string& name : g_requested) {
        asked_for_draw = asked_for_draw || name == "glDrawArrays";
        asked_for_readback = asked_for_readback || name == "glReadPixels";
    }
    CHECK(asked_for_draw);
    CHECK(asked_for_readback);
}

TEST_CASE(gl_loader_rejects_a_loader_that_finds_nothing) {
    fct::rhi::gl::GlApi api;
    const fct::rhi::gl::GlProcLoader empty{[](void*, const char*) -> void* { return nullptr; },
                                          nullptr};
    CHECK(!fct::rhi::gl::try_load_api(empty, api));
    const fct::rhi::gl::GlProcLoader unusable{nullptr, nullptr};
    CHECK(!fct::rhi::gl::try_load_api(unusable, api));
}

TEST_CASE(gl_headless_chain_has_no_surface_to_capture) {
    const std::unique_ptr<fct::rhi::Device> device = fct::rhi::create_device({});
    const std::unique_ptr<fct::rhi::SwapChain> chain = device->try_create_swap_chain({});
    CHECK(chain != nullptr);
    fct::rhi::CapturedFrame frame;
    CHECK(!chain->try_capture(frame));
    CHECK(!frame.is_valid());
}
