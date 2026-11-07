#include "render/ppm.h"

#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

namespace fct::render {
namespace {

std::string header(int width_px, int height_px) {
    return "P6\n" + std::to_string(width_px) + " " + std::to_string(height_px) + "\n255\n";
}

}  // namespace

bool try_write_ppm(const char* path, int width_px, int height_px, const std::uint32_t* pixels) {
    if (path == nullptr || pixels == nullptr || width_px <= 0 || height_px <= 0) {
        return false;
    }
    const std::size_t count =
        static_cast<std::size_t>(width_px) * static_cast<std::size_t>(height_px);
    std::vector<std::uint8_t> rgb;
    rgb.reserve(count * 3u);
    for (std::size_t index = 0; index < count; ++index) {
        const std::uint32_t pixel = pixels[index];
        rgb.push_back(static_cast<std::uint8_t>((pixel >> 24) & 0xFFu));
        rgb.push_back(static_cast<std::uint8_t>((pixel >> 16) & 0xFFu));
        rgb.push_back(static_cast<std::uint8_t>((pixel >> 8) & 0xFFu));
    }

    std::FILE* file = std::fopen(path, "wb");
    if (file == nullptr) {
        return false;
    }
    const std::string text = header(width_px, height_px);
    bool ok = std::fwrite(text.data(), 1, text.size(), file) == text.size();
    ok = ok && std::fwrite(rgb.data(), 1, rgb.size(), file) == rgb.size();
    ok = (std::fclose(file) == 0) && ok;
    return ok;
}

}  // namespace fct::render
