// No SDL3: there is no context to create, and the caller falls back to the
// headless backend. This is a supported configuration, not an error path.
#include "platform/gl_context.h"

#include "core/log.h"

namespace fct::platform {

GlContext::~GlContext() { destroy(); }

bool GlContext::try_create(void* window_handle, const GlContextDesc& desc) {
    (void)window_handle;
    (void)desc;
    FCT_LOG_DEBUG("gl: no SDL3 in this build, no context to create");
    return false;
}

void* GlContext::proc_address(const char* name) const {
    (void)name;
    return nullptr;
}

void GlContext::make_current() {}

void GlContext::swap_buffers() {}

void GlContext::destroy() { context_ = nullptr; }

}  // namespace fct::platform
