// A CPU-side colour target. Small, exact and inspectable: tests assert on pixels,
// and the headless frame check compares digests. The GL backend does not use this
// class; it draws to the swap chain's surface.
#pragma once

#include <cstdint>
#include <vector>

#include "rhi/swap_chain.h"

namespace fct::render {

inline constexpr int kMaxFramebufferPx = 4096;

class Framebuffer {
public:
    Framebuffer() = default;

    // False when the size is outside [1, kMaxFramebufferPx]; the target keeps its
    // previous contents. A 1x1 blank target is the documented empty state.
    bool try_resize(int width_px, int height_px);

    int width_px() const { return width_px_; }
    int height_px() const { return height_px_; }
    bool contains(int x, int y) const {
        return x >= 0 && y >= 0 && x < width_px_ && y < height_px_;
    }

    void clear(const rhi::ClearColor& color);

    // Out-of-range writes are dropped and reported, never clamped: a rasteriser
    // that scribbles just outside the image is a bug worth seeing.
    bool try_set_pixel(int x, int y, std::uint32_t rgba);
    std::uint32_t pixel_rgba(int x, int y) const;

    // Pixels that differ from the clear colour: the cheapest useful statement
    // about "did anything actually get drawn".
    int covered_pixels() const;

    std::uint64_t digest() const;

private:
    int width_px_ = 1;
    int height_px_ = 1;
    std::vector<std::uint32_t> pixels_{0u};
};

}  // namespace fct::render
