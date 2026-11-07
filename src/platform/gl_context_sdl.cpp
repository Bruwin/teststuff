// The only place SDL and GL meet: create a core-profile context on the window and
// expose proc addresses. Compiled by CMake only when SDL3 is found, so the
// fallback build never sees these headers (MOD-03 keeps SDL inside platform/).
#include "platform/gl_context.h"

#include <SDL3/SDL.h>

#include "core/log.h"

namespace fct::platform {
namespace {

// Done once per process, before any context exists: the attributes are global.
bool configure_attributes(const GlContextDesc& desc) {
    if (!SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, desc.major)) {
        FCT_LOG_ERROR("gl: could not set the context major version: %s", SDL_GetError());
        return false;
    }
    if (!SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, desc.minor)) {
        FCT_LOG_ERROR("gl: could not set the context minor version: %s", SDL_GetError());
        return false;
    }
    const int profile = desc.core_profile ? SDL_GL_CONTEXT_PROFILE_CORE
                                          : SDL_GL_CONTEXT_PROFILE_COMPATIBILITY;
    if (!SDL_GL_SetAttribute(SDL_GL_CONTEXT_PROFILE_MASK, profile)) {
        FCT_LOG_ERROR("gl: could not set the profile: %s", SDL_GetError());
        return false;
    }
    return true;
}

}  // namespace

GlContext::~GlContext() { destroy(); }

bool GlContext::try_create(void* window_handle, const GlContextDesc& desc) {
    if (window_handle == nullptr) {
        FCT_LOG_WARN("gl: no window to attach a context to");
        return false;
    }
    if (!configure_attributes(desc)) {
        return false;
    }
    auto* window = static_cast<SDL_Window*>(window_handle);
    SDL_GLContext context = SDL_GL_CreateContext(window);
    if (context == nullptr) {
        FCT_LOG_WARN("gl: no %d.%d core context: %s", desc.major, desc.minor, SDL_GetError());
        return false;
    }
    context_ = context;
    window_ = window_handle;
    return true;
}

void* GlContext::proc_address(const char* name) const {
    return reinterpret_cast<void*>(SDL_GL_GetProcAddress(name));
}

void GlContext::make_current() {
    if (context_ != nullptr) {
        SDL_GL_MakeCurrent(static_cast<SDL_Window*>(window_), static_cast<SDL_GLContext>(context_));
    }
}

void GlContext::swap_buffers() {
    if (window_ != nullptr) {
        SDL_GL_SwapWindow(static_cast<SDL_Window*>(window_));
    }
}

void GlContext::destroy() {
    if (context_ != nullptr) {
        SDL_GL_DestroyContext(static_cast<SDL_GLContext>(context_));
    }
    context_ = nullptr;
    window_ = nullptr;
}

}  // namespace fct::platform
