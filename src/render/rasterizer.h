// Reference rasteriser: draws recorded commands in software, into an RGBA8
// framebuffer. It is not a fallback renderer for shipping builds -- it exists so
// that "the triangle is on screen" is checkable on a machine with no GPU, and so
// the geometry and the draw path are exercised by the same commands the GL
// backend will replay.
#pragma once

#include "render/framebuffer.h"
#include "rhi/command_buffer.h"

namespace fct::render {

class Rasterizer {
public:
    // Ignores depth: M3 draws one flat layer, and a depth test nobody can
    // falsify without a second layer would be untested code.
    void draw(const rhi::CommandBuffer& commands, Framebuffer& target) const;

private:
    void draw_triangle(const rhi::DrawCommand& command, const rhi::CommandBuffer& commands,
                       Framebuffer& target) const;
    void draw_line(const rhi::DrawCommand& command, const rhi::CommandBuffer& commands,
                   Framebuffer& target) const;
};

}  // namespace fct::render
