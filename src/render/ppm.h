// Binary PPM (P6) writer. A screenshot format with no dependency, no compression
// and a header a test can read back: the point is a file that proves what was
// drawn, not a PNG encoder in the engine.
#pragma once

#include <cstdint>

namespace fct::render {

bool try_write_ppm(const char* path, int width_px, int height_px, const std::uint32_t* pixels);

}  // namespace fct::render
