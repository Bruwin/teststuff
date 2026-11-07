// What the engine asks a device to draw. Commands are recorded once and replayed
// by whichever backend is active, so the headless path and the GL path consume
// the same description -- there is no second code path that only tests exercise.
#pragma once

#include <bit>
#include <cstddef>
#include <cstdint>
#include <vector>

#include "core/hash.h"

namespace fct::rhi {

// Colours are packed integers, not floats: the digest over a command buffer is
// then exact, and a vertex stays 20 bytes.
inline constexpr std::uint32_t pack_rgba(std::uint8_t r, std::uint8_t g, std::uint8_t b,
                                         std::uint8_t a) {
    return (static_cast<std::uint32_t>(r) << 24) | (static_cast<std::uint32_t>(g) << 16) |
           (static_cast<std::uint32_t>(b) << 8) | static_cast<std::uint32_t>(a);
}

// Clip-space vertex. Both the software rasteriser and the GL backend expect
// w > 0; a vertex at or behind the eye is rejected rather than divided by zero.
struct Vertex {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;
    float w = 1.0f;
    std::uint32_t rgba = 0xFFFFFFFFu;
};

enum class Primitive : std::uint8_t {
    kTriangle = 0,
    kLine,
};

struct DrawCommand {
    Primitive primitive = Primitive::kTriangle;
    std::uint32_t first_vertex = 0;
    std::uint32_t vertex_count = 0;
};

// Bounded on purpose: a frame that asks for a million vertices is a bug, and it
// should be refused here rather than at the driver (MEM-05: reserve, do not grow
// inside a frame).
inline constexpr std::size_t kMaxVerticesPerBuffer = 65536;

class CommandBuffer {
public:
    CommandBuffer() {
        vertices_.reserve(1024);
        commands_.reserve(256);
    }

    void reset() {
        vertices_.clear();
        commands_.clear();
        digest_ = fct::kHashSeed;
    }

    // False when the buffer is full; the buffer is unchanged in that case.
    bool try_push_triangle(const Vertex& a, const Vertex& b, const Vertex& c) {
        if (vertices_.size() + 3 > kMaxVerticesPerBuffer) {
            return false;
        }
        const std::uint32_t first = static_cast<std::uint32_t>(vertices_.size());
        push_vertex(a);
        push_vertex(b);
        push_vertex(c);
        commands_.push_back(DrawCommand{Primitive::kTriangle, first, 3});
        digest_ = fct::hash_combine(digest_, static_cast<std::uint64_t>(Primitive::kTriangle));
        digest_ = fct::hash_combine(digest_, first);
        return true;
    }

    bool try_push_line(const Vertex& a, const Vertex& b) {
        if (vertices_.size() + 2 > kMaxVerticesPerBuffer) {
            return false;
        }
        const std::uint32_t first = static_cast<std::uint32_t>(vertices_.size());
        push_vertex(a);
        push_vertex(b);
        commands_.push_back(DrawCommand{Primitive::kLine, first, 2});
        digest_ = fct::hash_combine(digest_, static_cast<std::uint64_t>(Primitive::kLine));
        digest_ = fct::hash_combine(digest_, first);
        return true;
    }

    const std::vector<Vertex>& vertices() const { return vertices_; }
    const std::vector<DrawCommand>& commands() const { return commands_; }
    bool is_empty() const { return commands_.empty(); }

    // Identifies the recorded frame: equal sequences of commands and vertices
    // produce equal digests, and any change to geometry or colour changes it.
    std::uint64_t digest() const { return digest_; }

private:
    void push_vertex(const Vertex& vertex) {
        vertices_.push_back(vertex);
        digest_ = fct::hash_combine(digest_, vertex_bits(vertex.x));
        digest_ = fct::hash_combine(digest_, vertex_bits(vertex.y));
        digest_ = fct::hash_combine(digest_, vertex_bits(vertex.z));
        digest_ = fct::hash_combine(digest_, vertex_bits(vertex.w));
        digest_ = fct::hash_combine(digest_, static_cast<std::uint64_t>(vertex.rgba));
    }

    // Bit pattern, not the numeric value: -0.0f and 0.0f are different vertices
    // for a digest, and no rounding can make two distinct frames collide.
    static std::uint64_t vertex_bits(float value) {
        static_assert(sizeof(std::uint32_t) == sizeof(value), "float must be 32 bits");
        return static_cast<std::uint64_t>(std::bit_cast<std::uint32_t>(value));
    }

    std::vector<Vertex> vertices_;
    std::vector<DrawCommand> commands_;
    std::uint64_t digest_ = fct::kHashSeed;
};

}  // namespace fct::rhi
