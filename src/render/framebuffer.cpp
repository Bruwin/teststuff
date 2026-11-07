#include "render/framebuffer.h"

#include <cstdint>

#include "core/hash.h"

namespace fct::render {

namespace {

std::uint32_t pack_clear(const rhi::ClearColor& color) {
    auto channel = [](float value) {
        const float clamped = value < 0.0f ? 0.0f : (value > 1.0f ? 1.0f : value);
        return static_cast<std::uint8_t>(clamped * 255.0f + 0.5f);
    };
    return rhi::pack_rgba(channel(color.r), channel(color.g), channel(color.b), channel(color.a));
}

}  // namespace

bool Framebuffer::try_resize(int width_px, int height_px) {
    if (width_px <= 0 || height_px <= 0 || width_px > kMaxFramebufferPx ||
        height_px > kMaxFramebufferPx) {
        return false;
    }
    width_px_ = width_px;
    height_px_ = height_px;
    pixels_.assign(static_cast<std::size_t>(width_px) * static_cast<std::size_t>(height_px), 0u);
    return true;
}

void Framebuffer::clear(const rhi::ClearColor& color) {
    const std::uint32_t packed = pack_clear(color);
    for (std::uint32_t& pixel : pixels_) {
        pixel = packed;
    }
}

bool Framebuffer::try_set_pixel(int x, int y, std::uint32_t rgba) {
    if (!contains(x, y)) {
        return false;
    }
    const std::size_t index =
        static_cast<std::size_t>(y) * static_cast<std::size_t>(width_px_) +
        static_cast<std::size_t>(x);
    pixels_[index] = rgba;
    return true;
}

std::uint32_t Framebuffer::pixel_rgba(int x, int y) const {
    if (!contains(x, y)) {
        return 0u;
    }
    const std::size_t index =
        static_cast<std::size_t>(y) * static_cast<std::size_t>(width_px_) +
        static_cast<std::size_t>(x);
    return pixels_[index];
}

int Framebuffer::covered_pixels() const {
    if (pixels_.empty()) {
        return 0;
    }
    const std::uint32_t background = pixels_[0];
    int covered = 0;
    for (const std::uint32_t pixel : pixels_) {
        if (pixel != background) {
            ++covered;
        }
    }
    return covered;
}

std::uint64_t Framebuffer::digest() const {
    return fct::hash_bytes(pixels_.data(), pixels_.size() * sizeof(std::uint32_t));
}

}  // namespace fct::render
