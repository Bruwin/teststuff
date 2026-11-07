// Turns a proc-address callback into a GlApi. No SDL, no <GL/gl.h>, no platform
// include: the caller (the app) supplies a loader backed by whatever created the
// context, so this file compiles and is tested everywhere.
#pragma once

#include "rhi/gl/gl_api.h"

namespace fct::rhi::gl {

struct GlProcLoader {
    void* (*load)(void* user, const char* name) = nullptr;
    void* user = nullptr;
};

// Fills every entry it can find. False when the loader is unusable or an entry is
// missing; `out` is then incomplete and must not be used to build a device.
bool try_load_api(const GlProcLoader& loader, fct::gl::GlApi& out);

}  // namespace fct::rhi::gl
