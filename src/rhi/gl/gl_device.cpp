#include "rhi/gl/gl_device.h"

#include <cstddef>
#include <cstdint>
#include <memory>
#include <vector>

#include "core/log.h"
#include "rhi/capture.h"
#include "rhi/swap_chain_state.h"

namespace fct::rhi::gl {
namespace {

using fct::gl::kArrayBuffer;
using fct::gl::kColorBufferBit;
using fct::gl::kCompileStatus;
using fct::gl::kDynamicDraw;
using fct::gl::kFloat;
using fct::gl::kFragmentShader;
using fct::gl::kLines;
using fct::gl::kLinkStatus;
using fct::gl::kRenderer;
using fct::gl::kRgba;
using fct::gl::kTriangles;
using fct::gl::kUnsignedByte;
using fct::gl::kVertexShader;

constexpr const char* kVertexSource = R"(#version 460 core
layout(location = 0) in vec4 a_pos;
layout(location = 1) in vec4 a_color;
out vec4 v_color;
void main() {
    gl_Position = a_pos;
    v_color = a_color;
}
)";

constexpr const char* kFragmentSource = R"(#version 460 core
in vec4 v_color;
out vec4 o_color;
void main() {
    o_color = v_color;
}
)";

// Eight floats per vertex: clip-space position and the colour unpacked to 0..1.
// Sending the colour as floats keeps one buffer layout for every backend; the
// packing only exists to make the digest exact.
constexpr int kFloatsPerVertex = 8;

unsigned compile_stage(const GlApi& api, unsigned stage, const char* source) {
    const unsigned shader = api.create_shader(stage);
    api.shader_source(shader, 1, &source, nullptr);
    api.compile_shader(shader);
    int status = 0;
    api.get_shader_iv(shader, kCompileStatus, &status);
    if (status == 0) {
        api.destroy_shader(shader);
        return 0;
    }
    return shader;
}

unsigned build_program(const GlApi& api) {
    const unsigned vertex = compile_stage(api, kVertexShader, kVertexSource);
    if (vertex == 0) {
        return 0;
    }
    const unsigned fragment = compile_stage(api, kFragmentShader, kFragmentSource);
    if (fragment == 0) {
        api.destroy_shader(vertex);
        return 0;
    }

    const unsigned program = api.create_program();
    api.attach_shader(program, vertex);
    api.attach_shader(program, fragment);
    api.link_program(program);
    int status = 0;
    api.get_program_iv(program, kLinkStatus, &status);
    api.destroy_shader(vertex);
    api.destroy_shader(fragment);
    return status == 0 ? 0 : program;
}

float channel(std::uint32_t rgba, int shift) {
    return static_cast<float>((rgba >> shift) & 0xFFu) / 255.0f;
}

void append_vertex(std::vector<float>& out, const Vertex& vertex) {
    out.push_back(vertex.x);
    out.push_back(vertex.y);
    out.push_back(vertex.z);
    out.push_back(vertex.w);
    out.push_back(channel(vertex.rgba, 24));
    out.push_back(channel(vertex.rgba, 16));
    out.push_back(channel(vertex.rgba, 8));
    out.push_back(channel(vertex.rgba, 0));
}

// The chain: owns the VAO, the dynamic vertex buffer and the readback path. Its
// counters are the shared SwapChainState, so stats match the headless backend.
class GlSwapChain final : public SwapChain {
public:
    GlSwapChain(const GlApi& api, unsigned program, const SwapChainDesc& desc)
        : api_(api), program_(program), state_(desc) {
        api_.gen_vertex_arrays(1, &vao_);
        api_.gen_buffers(1, &vbo_);
        api_.bind_vertex_array(vao_);
        api_.bind_buffer(kArrayBuffer, vbo_);
        api_.viewport(0, 0, desc.width_px, desc.height_px);
        api_.use_program(program_);
    }

    ~GlSwapChain() override {
        api_.destroy_buffers(1, &vbo_);
        api_.destroy_vertex_arrays(1, &vao_);
    }

    int width_px() const override { return state_.width_px(); }
    int height_px() const override { return state_.height_px(); }
    Format format() const override { return state_.format(); }

    bool try_resize(int width_px, int height_px) override {
        if (!state_.try_resize(width_px, height_px)) {
            return false;
        }
        api_.viewport(0, 0, state_.width_px(), state_.height_px());
        return true;
    }

    void clear(const ClearColor& color) override {
        api_.clear_color(color.r, color.g, color.b, color.a);
        api_.clear(kColorBufferBit);
        state_.clear(color);
    }

    bool try_submit(const CommandBuffer& commands) override {
        if (!upload(commands)) {
            return false;
        }
        for (const DrawCommand& command : commands.commands()) {
            const int first = static_cast<int>(command.first_vertex);
            const int count = static_cast<int>(command.vertex_count);
            if (command.vertex_count == 3) {
                api_.draw_arrays(kTriangles, first, count);
            } else if (command.vertex_count == 2) {
                api_.draw_arrays(kLines, first, count);
            }
        }
        return state_.try_submit(commands);
    }

    bool try_present() override {
        if (state_.is_lost()) {
            return false;
        }
        api_.flush();
        return state_.try_present();
    }

    bool try_capture(CapturedFrame& frame) const override {
        if (state_.is_lost()) {
            return false;
        }
        const int width_px = state_.width_px();
        const int height_px = state_.height_px();
        const std::size_t count =
            static_cast<std::size_t>(width_px) * static_cast<std::size_t>(height_px);
        std::vector<std::uint8_t> bytes(count * 4u);
        api_.read_pixels(0, 0, width_px, height_px, kRgba, kUnsignedByte, bytes.data());
        frame.width_px = width_px;
        frame.height_px = height_px;
        frame.pixels.assign(count, 0u);
        // GL hands back the bottom row first; the frame and every writer above it
        // are top row first, so flip on the way out.
        for (int row = 0; row < height_px; ++row) {
            const int source_row = height_px - 1 - row;
            for (int column = 0; column < width_px; ++column) {
                const std::size_t source =
                    (static_cast<std::size_t>(source_row) * static_cast<std::size_t>(width_px) +
                     static_cast<std::size_t>(column)) * 4u;
                const std::uint8_t r = bytes[source];
                const std::uint8_t g = bytes[source + 1];
                const std::uint8_t b = bytes[source + 2];
                const std::uint8_t a = bytes[source + 3];
                frame.pixels[static_cast<std::size_t>(row) * static_cast<std::size_t>(width_px) +
                             static_cast<std::size_t>(column)] = pack_rgba(r, g, b, a);
            }
        }
        return frame.is_valid();
    }

    std::uint64_t frames_presented() const override { return state_.frames_presented(); }
    std::uint64_t clears_issued() const override { return state_.clears_issued(); }
    std::uint64_t submitted_buffers() const override { return state_.submitted_buffers(); }
    std::uint64_t vertices_submitted() const override { return state_.vertices_submitted(); }
    std::uint64_t frame_digest() const override { return state_.frame_digest(); }

private:
    bool upload(const CommandBuffer& commands) {
        if (state_.is_lost()) {
            return false;
        }
        std::vector<float> floats;
        floats.reserve(commands.vertices().size() * static_cast<std::size_t>(kFloatsPerVertex));
        for (const Vertex& vertex : commands.vertices()) {
            append_vertex(floats, vertex);
        }
        const std::size_t stride = static_cast<std::size_t>(kFloatsPerVertex) * sizeof(float);
        const std::size_t bytes = floats.size() * sizeof(float);

        api_.bind_vertex_array(vao_);
        api_.bind_buffer(kArrayBuffer, vbo_);
        api_.buffer_data(kArrayBuffer, static_cast<std::ptrdiff_t>(bytes), floats.data(),
                         kDynamicDraw);
        api_.enable_vertex_attrib_array(0);
        api_.vertex_attrib_pointer(0, 4, kFloat, 0,
                                   static_cast<int>(stride), reinterpret_cast<void*>(0));
        api_.enable_vertex_attrib_array(1);
        api_.vertex_attrib_pointer(1, 4, kFloat, 0, static_cast<int>(stride),
                                   reinterpret_cast<void*>(4 * sizeof(float)));
        return true;
    }

    GlApi api_;
    unsigned program_ = 0;
    unsigned vao_ = 0;
    unsigned vbo_ = 0;
    SwapChainState state_;
};

}  // namespace

GlDevice::GlDevice(const GlApi& api) : api_(api) {}

std::unique_ptr<GlDevice> GlDevice::try_create(const GlApi& api, const char* app_name) {
    if (!api.is_complete()) {
        FCT_LOG_ERROR("gl: entry points are incomplete, refusing to create a device");
        return nullptr;
    }
    std::unique_ptr<GlDevice> device = std::make_unique<GlDevice>(api);
    device->app_name_ = app_name;
    device->program_ = build_program(api);
    if (device->program_ == 0) {
        FCT_LOG_ERROR("gl: shader program did not build");
        return nullptr;
    }
    return device;
}

DeviceInfo GlDevice::info() const {
    const char* renderer = app_name_;
    if (api_.get_string != nullptr) {
        const unsigned char* raw = api_.get_string(kRenderer);
        if (raw != nullptr) {
            renderer = reinterpret_cast<const char*>(raw);
        }
    }
    return DeviceInfo{renderer, Backend::kGl, false};
}

std::unique_ptr<SwapChain> GlDevice::try_create_swap_chain(const SwapChainDesc& desc) {
    if (!is_valid(desc)) {
        FCT_LOG_ERROR("gl: rejecting swap chain '%s' at %dx%d", desc.debug_name, desc.width_px,
                      desc.height_px);
        return nullptr;
    }
    return std::make_unique<GlSwapChain>(api_, program_, desc);
}

void GlDevice::wait_idle() { api_.flush(); }

}  // namespace fct::rhi::gl
