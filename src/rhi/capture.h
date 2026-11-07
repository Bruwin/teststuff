// A frame read back from a real surface: RGBA8 packed one pixel per word, top row
// first. Produced by the GL swap chain, consumed by the screenshot writer.
#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

namespace fct::rhi {

struct CapturedFrame {
    int width_px = 0;
    int height_px = 0;
    std::vector<std::uint32_t> pixels;

    bool is_valid() const {
        const std::size_t expected =
            static_cast<std::size_t>(width_px) * static_cast<std::size_t>(height_px);
        return width_px > 0 && height_px > 0 && pixels.size() == expected;
    }
};

}  // namespace fct::rhi
