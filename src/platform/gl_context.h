// An OpenGL context, owned by the platform module because creating one needs the
// window system. rhi/ gets the entry points through a callback and never sees SDL.
#pragma once

namespace fct::platform {

struct GlContextDesc {
    int major = 4;
    int minor = 6;
    bool core_profile = true;
};

class GlContext {
public:
    GlContext() = default;
    ~GlContext();
    GlContext(const GlContext&) = delete;
    GlContext& operator=(const GlContext&) = delete;

    // False when the build has no SDL3 or the driver refused the version.
    bool try_create(void* window_handle, const GlContextDesc& desc);

    // Null for names the driver does not export, which is how a missing entry
    // point is detected instead of crashing on the first draw.
    void* proc_address(const char* name) const;

    void make_current();
    void swap_buffers();
    void destroy();

    bool is_open() const { return context_ != nullptr; }

private:
    void* context_ = nullptr;  // SDL_GLContext in the SDL backend
    void* window_ = nullptr;
};

}  // namespace fct::platform
