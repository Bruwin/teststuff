// Public API of the render module (MOD-06). M3 scope: a command buffer drawn by a
// reference rasteriser, plus the framebuffer it draws into. Scene graph, culling
// and the chunk batcher arrive with M4.
#pragma once

#include "render/framebuffer.h"
#include "render/ppm.h"
#include "render/rasterizer.h"
