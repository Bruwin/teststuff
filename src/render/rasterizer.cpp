#include "render/rasterizer.h"

#include <cstdint>

namespace fct::render {
namespace {

struct ScreenPoint {
    float x = 0.0f;
    float y = 0.0f;
    bool visible = false;  // false when the vertex is at or behind the eye
};

// Clip space to pixel space. y flips because clip space is up-positive and
// framebuffers are row-major down-positive.
ScreenPoint to_screen(const rhi::Vertex& vertex, const Framebuffer& target) {
    ScreenPoint point;
    if (vertex.w <= 0.0f) {
        return point;
    }
    const float inv_w = 1.0f / vertex.w;
    const float ndc_x = vertex.x * inv_w;
    const float ndc_y = vertex.y * inv_w;
    point.x = (ndc_x * 0.5f + 0.5f) * static_cast<float>(target.width_px());
    point.y = (1.0f - (ndc_y * 0.5f + 0.5f)) * static_cast<float>(target.height_px());
    point.visible = true;
    return point;
}

float edge(float ax, float ay, float bx, float by, float px, float py) {
    return (px - ax) * (by - ay) - (py - ay) * (bx - ax);
}

int clamp_int(int value, int low, int high) {
    return value < low ? low : (value > high ? high : value);
}

}  // namespace

void Rasterizer::draw(const rhi::CommandBuffer& commands, Framebuffer& target) const {
    for (const rhi::DrawCommand& command : commands.commands()) {
        if (command.vertex_count == 3) {
            draw_triangle(command, commands, target);
        } else if (command.vertex_count == 2) {
            draw_line(command, commands, target);
        }
    }
}

// Barycentric fill over the clipped bounding box. Pixels exactly on an edge are
// included, which keeps two triangles sharing an edge from leaving a seam.
void Rasterizer::draw_triangle(const rhi::DrawCommand& command, const rhi::CommandBuffer& commands,
                               Framebuffer& target) const {
    const std::uint32_t first = command.first_vertex;
    const ScreenPoint a = to_screen(commands.vertices()[first], target);
    const ScreenPoint b = to_screen(commands.vertices()[first + 1], target);
    const ScreenPoint c = to_screen(commands.vertices()[first + 2], target);
    if (!a.visible || !b.visible || !c.visible) {
        return;
    }

    const float area = edge(a.x, a.y, b.x, b.y, c.x, c.y);
    if (area == 0.0f) {
        return;  // degenerate: nothing to cover
    }
    const std::uint32_t rgba = commands.vertices()[first].rgba;

    const int min_x = clamp_int(static_cast<int>(a.x < b.x ? (a.x < c.x ? a.x : c.x)
                                                           : (b.x < c.x ? b.x : c.x)),
                                0, target.width_px() - 1);
    const int max_x = clamp_int(static_cast<int>(a.x > b.x ? (a.x > c.x ? a.x : c.x)
                                                           : (b.x > c.x ? b.x : c.x)),
                                0, target.width_px() - 1);
    const int min_y = clamp_int(static_cast<int>(a.y < b.y ? (a.y < c.y ? a.y : c.y)
                                                           : (b.y < c.y ? b.y : c.y)),
                                0, target.height_px() - 1);
    const int max_y = clamp_int(static_cast<int>(a.y > b.y ? (a.y > c.y ? a.y : c.y)
                                                           : (b.y > c.y ? b.y : c.y)),
                                0, target.height_px() - 1);

    for (int y = min_y; y <= max_y; ++y) {
        for (int x = min_x; x <= max_x; ++x) {
            const float px = static_cast<float>(x) + 0.5f;
            const float py = static_cast<float>(y) + 0.5f;
            const float w0 = edge(a.x, a.y, b.x, b.y, px, py);
            const float w1 = edge(b.x, b.y, c.x, c.y, px, py);
            const float w2 = edge(c.x, c.y, a.x, a.y, px, py);
            const bool inside = area > 0.0f ? (w0 >= 0.0f && w1 >= 0.0f && w2 >= 0.0f)
                                            : (w0 <= 0.0f && w1 <= 0.0f && w2 <= 0.0f);
            if (inside) {
                target.try_set_pixel(x, y, rgba);
            }
        }
    }
}

// DDA: one pixel per step along the longer axis, which is all a debug line needs.
void Rasterizer::draw_line(const rhi::DrawCommand& command, const rhi::CommandBuffer& commands,
                           Framebuffer& target) const {
    const std::uint32_t first = command.first_vertex;
    const ScreenPoint a = to_screen(commands.vertices()[first], target);
    const ScreenPoint b = to_screen(commands.vertices()[first + 1], target);
    if (!a.visible || !b.visible) {
        return;
    }
    const std::uint32_t rgba = commands.vertices()[first].rgba;

    const float dx = b.x - a.x;
    const float dy = b.y - a.y;
    const float steps_f = (dx < 0.0f ? -dx : dx) > (dy < 0.0f ? -dy : dy)
                              ? (dx < 0.0f ? -dx : dx)
                              : (dy < 0.0f ? -dy : dy);
    const int steps = static_cast<int>(steps_f) + 1;
    for (int step = 0; step <= steps; ++step) {
        const float t = static_cast<float>(step) / static_cast<float>(steps);
        const int x = static_cast<int>(a.x + dx * t);
        const int y = static_cast<int>(a.y + dy * t);
        target.try_set_pixel(x, y, rgba);
    }
}

}  // namespace fct::render
